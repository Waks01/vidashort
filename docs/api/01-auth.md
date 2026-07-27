# Auth endpoints

## Conventions

- All endpoints return JSON. No redirects.
- `email` is case-insensitive, stored as citext (lowercase).
- `password` is 8+ chars, at least one letter and one digit. Server validates.
- `acceptedTerms: true` is required on signup. The client should never send `false`.
- `identityToken` (Apple) is a JWT signed by Apple. Server verifies via JWKS.
- `idToken` (Google) is a JWT signed by Google. Server verifies via Google's certs.
- `forgot` and `reset` always return 202 / 200, never 4xx, to prevent email enumeration.

## Endpoints

### POST /v1/auth/signup

- **Auth:** public
- **Request:**
  ```json
  {
    "email": "user@example.com",
    "password": "correct-horse-battery",
    "name": "Maya",
    "acceptedTerms": true
  }
  ```
- **Response 201:**
  ```json
  {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "Maya",
      "role": "viewer",
      "avatarUrl": null,
      "createdAt": "2026-07-22T11:00:00Z"
    },
    "accessToken": "<jwt, 1h>",
    "refreshToken": "<opaque, 30d>"
  }
  ```
- **Errors:**
  - `400 invalid_email` — email format wrong
  - `400 weak_password` — < 8 chars or no letter/digit
  - `409 email_taken` — email already registered
  - `422 terms_required` — acceptedTerms not true
- **Side effects:**
  - `users` row created with role=viewer, coins=0, vipUntil=null.
  - `user_identities` row created (provider=email).
  - `coin_txn` row not created (no coins).
  - Welcome email queued (Phase 5).

### POST /v1/auth/signin

- **Auth:** public
- **Request:**
  ```json
  { "email": "user@example.com", "password": "correct-horse-battery" }
  ```
- **Response 200:** same shape as signup response.
- **Errors:**
  - `400 invalid_credentials` — email or password wrong (deliberately vague)
  - `429 rate_limited` — 5+ failed attempts in 10 min
  - `403 user_banned` — admin banned the user
  - `403 user_deleted` — account is soft-deleted; prompt for restore
- **Side effects:** `user_identities` last_login_at updated.

### POST /v1/auth/refresh

- **Auth:** public (the refresh token itself is the credential)
- **Request:**
  ```json
  { "refreshToken": "<opaque>" }
  ```
- **Response 200:**
  ```json
  { "accessToken": "<new jwt, 1h>", "refreshToken": "<new opaque, 30d>" }
  ```
  (Refresh token rotation: every refresh issues a new pair and invalidates the old refresh.)
- **Errors:**
  - `401 invalid_refresh` — token not found, or already rotated
  - `401 refresh_expired` — older than 30 days
- **Side effects:** old refresh token marked `used_at = now()`.

### POST /v1/auth/apple

- **Auth:** public
- **Request:**
  ```json
  {
    "identityToken": "<jwt from Apple>",
    "name": "Maya",
    "email": "user@privaterelay.appleid.com"
  }
  ```
  `name` and `email` are only sent on the first sign-in. After that, they're ignored (Apple doesn't return them).
- **Response 200:** same as signup.
- **Errors:**
  - `401 apple_verification_failed` — JWT signature invalid, expired, or audience mismatch
- **Side effects:**
  - If `provider_user_id` (Apple's sub) not in DB, create user + identity row.
  - If exists, return existing user.
  - First-time email is whatever Apple returns; we don't validate it.

### POST /v1/auth/google

- **Auth:** public
- **Request:**
  ```json
  { "idToken": "<jwt from Google Identity>" }
  ```
- **Response 200:** same as signup.
- **Errors:** same as Apple but with `google_verification_failed`.

### POST /v1/auth/forgot

- **Auth:** public
- **Request:** `{ "email": "user@example.com" }`
- **Response 202:** `{ "ok": true }` (always 202, even if email not registered)
- **Side effects:**
  - If email exists, generate reset token (random 256-bit, sha256 in DB, TTL 1h), email the link.
  - If email doesn't exist, no-op (no email sent, but same response).

### POST /v1/auth/reset

- **Auth:** public (the reset token is the credential)
- **Request:** `{ "token": "<opaque>", "newPassword": "..." }`
- **Response 200:** `{ "ok": true }`
- **Errors:**
  - `401 invalid_token` — token not found
  - `401 token_expired` — > 1h old
  - `400 weak_password`
- **Side effects:** user's password hash updated. All refresh tokens for this user invalidated.

## Token shape (JWT access token)

```json
{
  "sub": "uuid",
  "email": "user@example.com",
  "role": "viewer",
  "vip": false,
  "iat": 1753172400,
  "exp": 1753176000
}
```

- `sub` = user id.
- `role` ∈ {`viewer`, `creator`, `admin`}.
- `vip` is a fast-path flag to skip the DB hit on every request. Sourced from `vip_entitlements.expires_at > now()`. If the flag is wrong (token older than 5 min, user re-subscribed), the entitlement check on the protected route will correct it.

## Security notes

- Passwords hashed with bcrypt cost 12.
- Refresh tokens: sha256 in DB, never raw. We can't recover them; rotation only.
- Failed sign-in: 5 attempts in 10 min → `429 rate_limited` for 15 min.
- Successful sign-in: previous refresh tokens NOT invalidated (you can sign in on multiple devices).
- Forgot/reset always 202, never reveals whether email exists.
- JWT signed HS256 with `JWT_SECRET` (32-byte random, env var). Rotate by issuing new tokens with `kid` header; old tokens remain valid until expiry.
