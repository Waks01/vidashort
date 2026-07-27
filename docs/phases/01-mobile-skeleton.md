# Phase 1 — Expo mobile skeleton

## Goal

A runnable Expo app that boots, shows the splash → onboarding → sign-up flow, and renders the home feed against a mock API. Design system in TypeScript. No real backend. No real IAP. No real video. But the screens, gestures, and tokens work.

## Why this order

Before we wire up a real backend, we want to validate:
1. The Expo SDK 57 / RN 0.86 combo boots on iOS + Android.
2. The design tokens port cleanly from CSS to TypeScript.
3. The paywall decision tree runs in TypeScript (mirroring the prototype's `vidashort.Paywall.decide`).
4. The mock API contract matches what the real API will return. (We'll catch contract drift before the backend is built.)

This is the phase where the design prototype's "this is what it looks like" becomes the mobile app's "this is what it feels like in your hand."

## What's in scope

### 1. Monorepo setup (Day 1)

- Keep `mobile/` at the repo root. Do **not** move it into `apps/`.
- Root `package.json` with npm workspaces: `["mobile", "packages/*"]`.
- `mobile/package.json` is the existing one (`@vidashort/mobile`).
- `packages/shared/` with zod for type-safe API contracts.
- `.gitignore` at root (Node, Python, env, OneDrive debris).
- `.nvmrc` with Node 22.

Files touched:
- `package.json` (new, at root)
- `packages/shared/package.json` (new)
- `packages/shared/src/index.ts` (new)
- `.gitignore` (new)
- `.nvmrc` (new)
- `docs/runbooks/onedrive-exclude.md` (new, runbook)
- `mobile/` (untouched, stays at repo root)

### 2. Design system in TypeScript (Day 1-2)

- `mobile/src/lib/theme/tokens.ts` — mirrors every var in `apps/design/styles/tokens.css`. No values invented.
- `mobile/src/constants/theme.ts` — typography shorthands (`TYPOGRAPHY.display`, `TYPOGRAPHY.body`), spacing shorthands.
- `mobile/src/components/ui/Text.tsx` — wraps RN `Text`, applies font family based on `variant` prop. Variants: `display`, `heading`, `title`, `body`, `caption`, `coin`, `vip`.
- `mobile/src/components/ui/Pressable.tsx` — wraps RN `Pressable`, adds haptics on press, accessibility role, `activeOpacity: 0.7`.
- `mobile/src/components/ui/View.tsx`, `Stack.tsx`, `Screen.tsx` — base layout primitives with `gap` prop.

Files touched:
- `mobile/src/lib/theme/tokens.ts` (new)
- `mobile/src/lib/theme/provider.tsx` (new)
- `mobile/src/constants/theme.ts` (new)
- `mobile/src/components/ui/Text.tsx` (new)
- `mobile/src/components/ui/Pressable.tsx` (new)
- `mobile/src/components/ui/View.tsx` (new)
- `mobile/src/components/ui/Stack.tsx` (new)
- `mobile/src/components/ui/Screen.tsx` (new)

### 3. Shared package (Day 1)

- `packages/shared/src/schemas/user.ts` — zod schema for `User`.
- `packages/shared/src/schemas/series.ts` — zod for `Series`, `EpisodeMeta`.
- `packages/shared/src/schemas/paywall.ts` — zod for `PaywallDecision`.
- `packages/shared/src/index.ts` — re-exports.
- `mobile/package.json` depends on `@vidashort/shared: "*"`.

Files touched:
- `packages/shared/src/schemas/user.ts` (new)
- `packages/shared/src/schemas/series.ts` (new)
- `packages/shared/src/schemas/paywall.ts` (new)
- `packages/shared/src/schemas/coin.ts` (new)
- `packages/shared/src/schemas/ads.ts` (new)
- `packages/shared/src/index.ts` (new)

### 4. Mock API client (Day 2)

The mobile app needs an API client. We build the real one now, but back it with a mock. When the real backend is ready in Phase 2, we flip a flag and the same client talks to it.

- `mobile/src/lib/api/client.ts` — fetch wrapper, base URL, auth header, 401 → refresh → retry.
- `mobile/src/lib/api/auth.ts` — `signup`, `signin`, `refresh`, `apple`, `google`, `forgot`, `reset`. Backed by mock for Phase 1.
- `mobile/src/lib/api/me.ts` — `getMe`, `updateMe`, `deleteMe`. Backed by mock.
- `mobile/src/lib/api/content.ts` — `listSeries`, `getSeries`, `getStream`. Backed by mock.
- `mobile/src/lib/api/index.ts` — namespace export.
- `mobile/src/lib/api/mock/` — the mock implementation, same shape as the real client. Uses a hardcoded `MockData` mirror of the prototype's `apps/design/scripts/data.js`.
- `mobile/src/lib/api/real/` — placeholder for the real client (Phase 2).

Files touched: ~ 10 new files in `lib/api/`.

### 5. Auth provider (Day 2)

- `mobile/src/lib/auth/storage.ts` — `expo-secure-store` wrapper. `getAccessToken`, `getRefreshToken`, `setTokens`, `clearTokens`.
- `mobile/src/lib/auth/provider.tsx` — React Context. State: `user`, `loading`, `signedIn`. Methods: `signIn`, `signUp`, `signOut`, `refresh`. Persists tokens to secure-store on change.
- `mobile/src/lib/auth/useAuth.ts` — hook.
- `mobile/src/lib/auth/tokens.ts` — JWT decode (no verify, just read).

Files touched: 4 new files in `lib/auth/`.

### 6. Routing (Day 3-4)

- `mobile/src/app/_layout.tsx` — root: `ThemeProvider`, `AuthProvider`, `GestureHandlerRootView`, `SafeAreaProvider`, `QueryClientProvider` (for react-query).
- `mobile/src/app/index.tsx` — splash, then redirect to `(auth)/` or `(viewer)/` based on auth state.
- `mobile/src/app/(auth)/_layout.tsx` — Stack for the auth flow.
- `mobile/src/app/(auth)/splash.tsx` — animated wordmark, 1.5s auto-advance.
- `mobile/src/app/(auth)/onboarding.tsx` — 3 horizontal scroll-snap slides, pagination dots, Skip, Next.
- `mobile/src/app/(auth)/genre-picker.tsx` — 12 chips, Continue enables at 3+.
- `mobile/src/app/(auth)/age-gate.tsx` — "Are you 17 or older?" Yes/No.
- `mobile/src/app/(auth)/role-picker.tsx` — "Watch" or "Create".
- `mobile/src/app/(auth)/auth-entry.tsx` — Apple / Google / Email buttons.
- `mobile/src/app/(auth)/sign-up.tsx` — email + password + confirm + terms.
- `mobile/src/app/(auth)/sign-in.tsx` — email + password + forgot.
- `mobile/src/app/(auth)/forgot-password.tsx` — email submit.
- `mobile/src/app/(auth)/otp.tsx` — 6-digit, auto-advance, resend.
- `mobile/src/app/(auth)/creator-signup.tsx` — channel + handle + payout method.

Files touched: 12 new route files.

### 7. Viewer shell (Day 5)

- `mobile/src/app/(viewer)/_layout.tsx` — tab bar with 5 tabs: Home, Discover, Library, Wallet, Profile.
- `mobile/src/app/(viewer)/home.tsx` — vertical scroll-snap feed. **Uses the design from `apps/design/screens/10-home.html` as the pixel reference.**
- `mobile/src/app/(viewer)/discover.tsx` — 2-col grid, filter chips, search.
- `mobile/src/app/(viewer)/search.tsx` — input, trending tags, recent, results.
- `mobile/src/app/(viewer)/library.tsx` — 4 tabs (Continue, Favorites, Watchlist, History).
- `mobile/src/app/(viewer)/wallet.tsx` — coin balance, daily check-in, transactions.
- `mobile/src/app/(viewer)/profile.tsx` — avatar, balance, menu, sign out.
- `mobile/src/components/bottom-nav.tsx` — shared tab bar.
- `mobile/src/components/top-bar.tsx` — shared top bar.
- `mobile/src/components/coin-badge.tsx` — gold pill with coin count.

Files touched: 7 new route files + 3 component files.

### 8. Components for the home feed (Day 5-6)

- `mobile/src/components/poster-card.tsx` — 9:16 poster with gradient placeholder fallback.
- `mobile/src/components/video-item.tsx` — one feed slide: gradient bg, meta, action column.
- `mobile/src/components/action-column.tsx` — right-side heart / comment / share / cost chip.
- `mobile/src/lib/paywall/decide.ts` — `decidePaywall({ episode, coins, vip, adCap })`. Mirrors the prototype's priority order.
- `mobile/src/hooks/use-paywall-decision.ts` — wraps the above with `useMe()`.

Files touched: 4 new component files + 2 new lib files.

### 9. Mock data parity (Day 6)

- `mobile/src/lib/api/mock/data.ts` — TypeScript mirror of `apps/design/scripts/data.js`. 3 originals, 30 episodes, 5 coin packs, 3 VIP plans, sample comments.
- The visual output of `mobile/src/app/(viewer)/home.tsx` should match `apps/design/screens/10-home.html` to within a few pixels.

### 10. Gesture handling (Day 6-7)

- `mobile/src/lib/gestures/feed.ts` — tap right 1/3 = next, tap left 1/3 = prev, double-tap = heart particle, long-press 500ms = pause.
- Reanimated 3 worklets for the heart particles.

## What's out of scope

- ❌ Real backend calls. Everything is mock. The mock returns the same shapes as the real API will.
- ❌ Real IAP. `react-native-purchases` is installed but not wired.
- ❌ Real video. The player uses a CSS-like gradient as a stand-in (the same trick the prototype uses).
- ❌ Real push notifications.
- ❌ Real Cloudflare Stream. The "playback URL" in the mock is a fake.
- ❌ The episode player screen (Phase 2 — too much player logic to do now).
- ❌ Comments, share, library, wallet, profile, settings, notifications (Phase 2). The home feed is the priority.
- ❌ Creator + admin stacks (Phase 3).
- ❌ EAS Build (Phase 1.5).

## Tasks (ordered, with line estimates)

1. **Monorepo** — root `package.json`, `packages/shared` init, `.gitignore`, `.nvmrc`. **~ 50 lines.**
2. **Design tokens** — `lib/theme/tokens.ts`, `constants/theme.ts`. **~ 200 lines.**
3. **UI primitives** — `ui/Text.tsx`, `ui/Pressable.tsx`, `ui/View.tsx`, `ui/Stack.tsx`, `ui/Screen.tsx`. **~ 300 lines.**
4. **Shared schemas** — `packages/shared/src/schemas/*` (5 files, 1 index). **~ 200 lines.**
5. **Mock data** — `lib/api/mock/data.ts`. Mirror `data.js`. **~ 800 lines.**
6. **API client + mocks** — `lib/api/*` (10 files). **~ 600 lines.**
7. **Auth provider** — `lib/auth/*` (4 files). **~ 300 lines.**
8. **Auth routes** — `(auth)/*` (12 route files). **~ 1500 lines.**
9. **Bottom nav, top bar, coin badge** — components. **~ 200 lines.**
10. **Viewer routes** — `(viewer)/*` (7 route files). **~ 700 lines.**
11. **Feed components** — `video-item`, `action-column`, `poster-card`. **~ 400 lines.**
12. **Paywall decide + hook** — `lib/paywall/decide.ts`, `hooks/use-paywall-decision.ts`. **~ 200 lines.**
13. **Gesture handling** — `lib/gestures/feed.ts`. **~ 200 lines.**
14. **Polish** — fonts loaded, haptics, animations, accessibility. **~ 200 lines.**

Total: **~ 5,800 lines of new TS.** This is the biggest phase by code volume.

## Verification

```bash
# Local dev
cd mobile
npm install
npx expo start

# In another terminal, or with the iOS/Android button:
npx expo start --ios
# or
npx expo start --android
```

The end-to-end smoke test (run on a real simulator):

1. App boots. Splash shows, wordmark animates, 1.5s → advances.
2. Onboarding 3 slides. Swipe works, pagination dots update, Skip works, Next works.
3. Genre picker: tap 3 chips, Continue button enables, tap Continue.
4. Age gate: tap Yes.
5. Role picker: tap "Watch" (or "Create" — if Create, also runs creator-signup).
6. Auth entry: tap "Email", fill sign-up form, tap "Create account".
7. Home feed loads. 12 mock episodes in a vertical scroll-snap. Top bar shows "vidashort" wordmark, coin balance (0), bell icon, search.
8. Tap the heart on any episode. Heart fills, toast "Added to favorites".
9. Double-tap anywhere on the feed. Heart particle flies up.
10. Tap right side. Feed advances. Tap left side. Feed goes back.
11. Pull down to refresh. (Optional in Phase 1, but if react-query is set up, this is free.)
12. Tap a feed item. Paywall modal opens (because user has 0 coins, not VIP, and the episode is paywalled).
13. Tap X on paywall. Modal closes.
14. Tap bottom nav: Discover. 2-col grid of series.
15. Tap bottom nav: Profile. Avatar (placeholder), name, sign out.
16. Tap sign out. Tokens cleared. Returns to splash.

**Pass criteria:**
- No red errors in the React Native debug overlay.
- No `console.error` in the Metro log.
- The visual output of home feed matches `apps/design/screens/10-home.html` to within reasonable.
- All 16 steps complete in under 5 minutes.

**Run automated checks:**
```bash
npm run typecheck  # tsc passes
npm run lint       # eslint passes
```

## Hand-off

What Phase 2 (backend) assumes:
- The mobile app has a real `lib/api/` client that talks to `EXPO_PUBLIC_API_URL`.
- The shared package has zod schemas that match the API contract in `docs/api/`.
- The mobile app can render the home feed with real data, not just mock.
- The paywall `decide()` is a pure function with the locked priority order.
- The auth provider persists tokens to secure-store.

What Phase 1.5 (build) assumes:
- The app boots without metro on a real device.
- No use of `process.env` in a way that breaks EAS Build.
- All assets (icon, splash, fonts) are bundled.
- Privacy policy, support URL, age rating are placeholders.
