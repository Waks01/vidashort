# Coins endpoints

Real-money purchases, coin balance, transaction history.

## Conventions

- All amounts are integers in coins. 1 Naira = 10 coins.
- IAP receipts are verified server-side against Apple / Google before coins are credited.
- The webhook is the source of truth. The client `POST /v1/coins/purchase` is a "register my receipt" call; the webhook is what actually moves money.
- Pack IDs are server-issued strings: `"pack_100"`, `"pack_500"`, etc.

## Endpoints

### GET /v1/coins/balance

- **Auth:** required
- **Response 200:**
  ```json
  {
    "coins": 120,
    "lifetimePurchased": 5000,
    "lifetimeSpent": 4880,
    "lifetimeEarnedAds": 240,
    "lifetimeEarnedDaily": 75,
    "recent": [
      {
        "id": "uuid",
        "delta": -25,
        "reason": "unlock",
        "refId": "ep-uuid",
        "balanceAfter": 95,
        "createdAt": "2026-07-22T11:30:00Z"
      }
    ]
  }
  ```
- **Notes:**
  - `recent` is the last 20 transactions.
  - Wallet screen calls this on every open.

### GET /v1/coins/packs

- **Auth:** public
- **Response 200:**
  ```json
  {
    "packs": [
      {
        "id": "pack_100",
        "coins": 100,
        "bonusCoins": 0,
        "totalCoins": 100,
        "priceNaira": 100,
        "priceFormatted": "₦100",
        "badge": null,
        "appleProductId": "vs.coins.100",
        "googleProductId": "vs_coins_100"
      },
      {
        "id": "pack_500",
        "coins": 500,
        "bonusCoins": 0,
        "totalCoins": 500,
        "priceNaira": 500,
        "priceFormatted": "₦500",
        "badge": null,
        "appleProductId": "vs.coins.500",
        "googleProductId": "vs_coins_500"
      },
      {
        "id": "pack_2200",
        "coins": 2000,
        "bonusCoins": 200,
        "totalCoins": 2200,
        "priceNaira": 2000,
        "priceFormatted": "₦2,000",
        "badge": "Best Value",
        "appleProductId": "vs.coins.2200",
        "googleProductId": "vs_coins_2200"
      },
      {
        "id": "pack_6000",
        "coins": 5000,
        "bonusCoins": 1000,
        "totalCoins": 6000,
        "priceNaira": 5000,
        "priceFormatted": "₦5,000",
        "badge": null,
        "appleProductId": "vs.coins.6000",
        "googleProductId": "vs_coins_6000"
      },
      {
        "id": "pack_19000",
        "coins": 15000,
        "bonusCoins": 4000,
        "totalCoins": 19000,
        "priceNaira": 15000,
        "priceFormatted": "₦15,000",
        "badge": "Most Popular",
        "appleProductId": "vs.coins.19000",
        "googleProductId": "vs_coins_19000"
      }
    ]
  }
  ```
- **Notes:**
  - `appleProductId` and `googleProductId` are the IAP product IDs as registered in App Store Connect / Play Console.
  - The client never displays the pack list without the matching product IDs. The coin store screen renders the packs and uses the IDs to start the IAP flow.

### POST /v1/coins/purchase

- **Auth:** required
- **Request:**
  ```json
  {
    "packId": "pack_2200",
    "receipt": {
      "provider": "apple" | "google",
      "data": "<base64 receipt or purchase token>",
      "txnId": "<original transaction id>"
    }
  }
  ```
- **Headers:** `Idempotency-Key: <uuid>` (the client generates this once per IAP and reuses on retry)
- **Response 200:**
  ```json
  {
    "coins": 2320,
    "txnId": "vidashort-txn-uuid",
    "creditedCoins": 2200,
    "bonusCoins": 200
  }
  ```
- **Errors:**
  - `400 unknown_pack` — packId not in catalog
  - `402 receipt_invalid` — Apple/Google rejected the receipt
  - `409 already_processed` — receipt already credited (idempotent return of original)
  - `422 amount_mismatch` — receipt amount doesn't match pack
- **Side effects:**
  - Server verifies receipt against Apple (App Store Server API v2) or Google (Play Developer API).
  - On success: `coin_txn` row with `delta: +<totalCoins>, reason: "purchase"`, `users.coins += totalCoins`.
  - The `Idempotency-Key` is stored on the `coin_txn` row; same key returns the same response.

## How IAP works end-to-end

```
1. Mobile: User taps "₦2,000" pack.
2. Mobile: react-native-purchases.purchaseProduct('vs.coins.2200')
3. Apple/Google: prompts user, completes purchase, returns receipt to mobile.
4. Mobile: POST /v1/coins/purchase { packId, receipt, Idempotency-Key }
5. Server: verifies receipt, credits coins, returns new balance.
6. Server (async, may come before or after step 4): webhook from Apple/Google
   → also credits coins if not already credited (defensive double-credit prevention
     via txnId unique constraint).
7. Mobile: shows confetti + toast "₦2,000 → 2,200 coins!"
```

The webhook is the source of truth for accounting. The `/purchase` endpoint is a UX accelerator.

## Refunds

- Apple/Google may issue refunds. We get a notification via the same webhook.
- On refund: `users.coins -= totalCoins` (clamped to 0), `coin_txn` with `delta: -<totalCoins>, reason: "refund"`.
- If the user spent the coins already and balance goes negative, we don't claw back unlocks. We track the debt in `users.balance_after_refund` for analytics, and the next purchase they make is reduced.
- See `docs/contracts/00-overview.md § "Refunds"` for the full contract.

## Receipt verification libraries

- **Apple:** `app-store-server-library` (Apple's official Python lib) or direct App Store Server API v2.
- **Google:** `googleapiclient` for the Play Developer API.
- Both are sandbox-aware (the receipt from the test environment verifies against sandbox keys).

## Why this is not Stripe

We use **Apple In-App Purchase** and **Google Play Billing** for two reasons:
1. **App Store rule:** Apps selling digital content must use IAP. 30% goes to Apple/Google. We can't avoid this.
2. **No PCI scope.** We never see a card number. Apple/Google handle it.

The 30% is the cost of being on the stores. The economics (60/40 creator/platform) are calculated **after** the 30% store fee. So a 25-coin unlock (₦2.50) at 70% retention (Apple takes 30%) leaves the platform with ₦1.75 gross, of which ₦1.50 goes to the creator and ₦0.25 is platform net.
