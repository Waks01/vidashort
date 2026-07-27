# Mobile component tree — apps/mobile/src/

Expo SDK 57 + expo-router + React 19.2 + RN 0.86 + TypeScript 6.

## Layout

```
apps/mobile/
├── app.json
├── eas.json
├── package.json
├── tsconfig.json
├── babel.config.js
├── metro.config.js
├── .env.example
├── index.ts
└── src/
    ├── app/                          # expo-router file-based routes
    │   ├── _layout.tsx               # root: ThemeProvider, AuthProvider, GestureHandlerRootView
    │   ├── index.tsx                 # role-aware redirect (splash → onboarding OR home)
    │   ├── +not-found.tsx
    │   ├── (auth)/                   # unauthenticated stack
    │   │   ├── _layout.tsx
    │   │   ├── splash.tsx
    │   │   ├── onboarding.tsx
    │   │   ├── genre-picker.tsx
    │   │   ├── age-gate.tsx
    │   │   ├── role-picker.tsx
    │   │   ├── auth-entry.tsx
    │   │   ├── sign-up.tsx
    │   │   ├── sign-in.tsx
    │   │   ├── forgot-password.tsx
    │   │   ├── otp.tsx
    │   │   └── creator-signup.tsx
    │   ├── (viewer)/                 # authenticated viewer stack
    │   │   ├── _layout.tsx           # tab bar
    │   │   ├── home.tsx
    │   │   ├── discover.tsx
    │   │   ├── search.tsx
    │   │   ├── library.tsx
    │   │   ├── wallet.tsx
    │   │   ├── profile.tsx
    │   │   ├── settings.tsx
    │   │   ├── notifications.tsx
    │   │   ├── series/[slug].tsx
    │   │   ├── episode/[id].tsx
    │   │   ├── comments/[episodeId].tsx
    │   │   ├── share.tsx
    │   │   ├── coin-store.tsx
    │   │   ├── vip.tsx
    │   │   ├── daily-reward.tsx
    │   │   └── paywall.tsx
    │   ├── (creator)/                # authenticated creator stack
    │   │   ├── _layout.tsx
    │   │   ├── dashboard.tsx
    │   │   ├── series/index.tsx
    │   │   ├── series/new.tsx
    │   │   ├── series/[id]/edit.tsx
    │   │   ├── analytics.tsx
    │   │   ├── payouts.tsx
    │   │   └── account.tsx
    │   └── (admin)/                  # authenticated admin stack
    │       ├── _layout.tsx
    │       ├── overview.tsx
    │       ├── moderation.tsx
    │       ├── content.tsx
    │       ├── users.tsx
    │       ├── ads.tsx
    │       └── finance.tsx
    ├── components/                   # shared RN components (one per file)
    │   ├── ui/
    │   │   ├── Pressable.tsx         # haptics + active opacity + accessibility
    │   │   ├── Text.tsx              # font-family enforcement
    │   │   ├── View.tsx
    │   │   ├── Stack.tsx             # flex column with spacing
    │   │   ├── Screen.tsx            # SafeArea + topbar slot + bottomnav slot
    │   │   ├── Skeleton.tsx
    │   │   └── Image.tsx             # expo-image wrapper, fade-in
    │   ├── top-bar.tsx
    │   ├── bottom-nav.tsx
    │   ├── coin-badge.tsx
    │   ├── topbar-action.tsx
    │   ├── primary-button.tsx
    │   ├── secondary-button.tsx
    │   ├── gold-button.tsx
    │   ├── input-field.tsx
    │   ├── chip.tsx
    │   ├── poster-card.tsx
    │   ├── video-item.tsx            # one feed slide
    │   ├── action-column.tsx        # right-side heart/comment/share
    │   ├── paywall-modal.tsx
    │   ├── confetti.tsx              # react-native-reanimated
    │   ├── toast.tsx
    │   ├── confirm.tsx
    │   ├── ad-banner.tsx
    │   ├── sponsored-card.tsx
    │   ├── loading-skeleton.tsx
    │   ├── empty-state.tsx
    │   └── error-state.tsx
    ├── lib/                          # framework-agnostic TS
    │   ├── api/
    │   │   ├── client.ts             # fetch wrapper, base URL, auth header
    │   │   ├── auth.ts
    │   │   ├── me.ts
    │   │   ├── content.ts
    │   │   ├── entitlement.ts
    │   │   ├── coins.ts
    │   │   ├── ads.ts
    │   │   ├── creator.ts
    │   │   └── admin.ts
    │   ├── auth/
    │   │   ├── provider.tsx          # React context: useAuth()
    │   │   ├── storage.ts            # expo-secure-store wrapper
    │   │   └── tokens.ts
    │   ├── storage/
    │   │   ├── mmkv.ts               # offline cache
    │   │   └── schema.ts
    │   ├── analytics/
    │   │   └── events.ts
    │   ├── video/
    │   │   ├── player.ts             # expo-video wrapper, gestures
    │   │   └── captions.ts
    │   ├── paywall/
    │   │   ├── decide.ts             # mirrors server priority
    │   │   └── usePaywall.ts
    │   ├── monetization/
    │   │   ├── ad-cap.ts             # mirrors server cap
    │   │   └── rewarded-ad.ts
    │   ├── iap/
    │   │   ├── revenuecat.ts         # react-native-purchases wrapper
    │   │   └── use-purchase.ts
    │   ├── theme/
    │   │   ├── tokens.ts             # mirrors design tokens
    │   │   └── provider.tsx
    │   └── utils/
    │       ├── format.ts             # Intl-based money + date
    │       ├── logger.ts             # sentry-bridge
    │       └── haptics.ts
    ├── hooks/
    │   ├── use-coins.ts
    │   ├── use-vip.ts
    │   ├── use-feed.ts
    │   ├── use-episode.ts
    │   ├── use-series.ts
    │   ├── use-paywall-decision.ts
    │   ├── use-favorites.ts
    │   ├── use-watch-history.ts
    │   ├── use-comments.ts
    │   ├── use-daily-reward.ts
    │   └── use-role.ts
    ├── constants/
    │   ├── theme.ts                  # typography, spacing shorthands
    │   ├── layout.ts                 # screen sizes, safe area, dimensions
    │   ├── routes.ts                 # typed route names
    │   └── economics.ts              # mirrored from docs
    ├── types/
    │   ├── api.ts                    # mirrors docs/api/
    │   └── domain.ts                 # User, Series, Episode, etc.
    └── assets/
        ├── icon.png
        ├── splash.png
        └── adaptive-icon.png
```

## Layering

- **app/** — routing only. `index.tsx` files call hooks, render components. No API calls, no business logic, no JSX > 50 lines.
- **components/** — reusable UI. Props are typed, no globals. Each component file is small (≤ 200 lines).
- **lib/** — pure TypeScript. No React. No `useState`. Easy to test, easy to extract.
- **hooks/** — React state + lifecycle. One concern per hook. Use the `lib/` modules for actual work.
- **constants/** — frozen objects only. No functions.
- **types/** — type-only files. No runtime code.

## Why file-based routing with route groups

`expo-router` lets us have `(auth)/`, `(viewer)/`, `(creator)/`, `(admin)/` as **separate stacks** without coupling their tab bars. A viewer sees Home/Discover/Library/Wallet/Profile; a creator sees Dashboard/Series/Upload/Payouts/Account; an admin sees Overview/Moderate/Content/Users/Ads.

The role-aware redirect lives in `app/index.tsx`:
```ts
if (auth.role === 'admin') router.replace('/(admin)/overview');
else if (auth.role === 'creator') router.replace('/(creator)/dashboard');
else router.replace('/(viewer)/home');
```

## Why `lib/` is pure TS

- Same module can be tested in node, no RN runtime.
- Easy to extract into `packages/shared/` later.
- The same `paywall.decide()` runs on server (Python) and client (TS) — the priority order is shared documentation, but the implementations are language-specific.

## Why one component per file

- Tree-shakeable. Unused components don't ship.
- Easier to read. Each file is short.
- Easier to refactor.

## The hooks pattern

Hooks own state; components own rendering.

```ts
// hooks/use-paywall-decision.ts
export function usePaywallDecision(episode: Episode): {
  path: PaywallPath;
  cta: string;
  onPress: () => void;
  loading: boolean;
} {
  const { coins, vip, adCap } = useMe();
  return useMemo(() => {
    const decision = decidePaywall({ episode, coins, vip, adCap });
    return {
      path: decision.path,
      cta: decision.label,
      onPress: () => openPaywall(decision),
      loading: false,
    };
  }, [episode, coins, vip, adCap]);
}
```

```tsx
// components/video-item.tsx
export function VideoItem({ episode }: { episode: Episode }) {
  const paywall = usePaywallDecision(episode);
  return (
    <Pressable onPress={paywall.onPress}>
      <Poster url={episode.coverUrl} />
      <Text>{episode.title}</Text>
      <Pressable onPress={paywall.onPress}><Text>{paywall.cta}</Text></Pressable>
    </Pressable>
  );
}
```

The component doesn't know about coins, VIP, or ads. The hook does. This is the only way 5 different surfaces (home feed, search, series detail, library, comments) can render the same paywall logic without duplicating it.

## The `api/` layer

`lib/api/client.ts`:

```ts
const BASE_URL = process.env.EXPO_PUBLIC_API_URL!;

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as any),
  };

  if (options.auth !== false) {
    const token = await getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401 && options.auth !== false) {
    // Try refresh once
    const refreshed = await tryRefresh();
    if (refreshed) {
      return apiFetch(path, options);  // retry once
    }
    await signOut();
    throw new AuthError();
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.error || 'unknown', res.status, body);
  }

  return res.json();
}
```

`lib/api/auth.ts`:
```ts
export const auth = {
  signup: (body: SignupRequest) =>
    apiFetch<AuthResponse>('/auth/signup', { method: 'POST', body: JSON.stringify(body), auth: false }),
  signin: (body: SigninRequest) =>
    apiFetch<AuthResponse>('/auth/signin', { method: 'POST', body: JSON.stringify(body), auth: false }),
  refresh: (token: string) =>
    apiFetch<AuthResponse>('/auth/refresh', { method: 'POST', body: JSON.stringify({ refreshToken: token }), auth: false }),
  apple: (body: AppleRequest) =>
    apiFetch<AuthResponse>('/auth/apple', { method: 'POST', body: JSON.stringify(body), auth: false }),
  google: (body: GoogleRequest) =>
    apiFetch<AuthResponse>('/auth/google', { method: 'POST', body: JSON.stringify(body), auth: false }),
};
```

## State management

- **Auth state:** React Context (`lib/auth/provider.tsx`). One provider at the root. The provider re-hydrates from secure-store on app start.
- **Server cache:** `react-query` (or `@tanstack/react-query`). Used for /v1/me, /v1/content/*, /v1/coins/*. Cache TTLs per-endpoint, refetch on focus, retry once.
- **Local UI state:** `useState` / `useReducer` per component. No global UI state.
- **Form state:** `react-hook-form` for complex forms (sign-up, creator upload). `useState` for trivial.
- **No Redux.** No Zustand. No Jotai. Context + react-query is enough.

## Storage

- **`expo-secure-store`** for tokens (access + refresh). Per-app encrypted.
- **`mmkv`** for everything else (settings, cached feed, last-seen episode). Fast, sync, native.
- **No `AsyncStorage`.** Deprecated, slow, no encryption.

## Navigation type safety

`expo-router` + TypeScript gives typed routes:

```ts
import { useRouter } from 'expo-router';
const router = useRouter();
router.push({ pathname: '/series/[slug]', params: { slug: 'the-ceos...' } });
```

`constants/routes.ts`:
```ts
export const ROUTES = {
  splash: '/',
  onboarding: '/onboarding',
  signIn: '/sign-in',
  signUp: '/sign-up',
  home: '/home',
  series: (slug: string) => `/series/${slug}` as const,
  episode: (id: string) => `/episode/${id}` as const,
  paywall: '/paywall',
  // ...
} as const;
```

## Why no styled-components / nativewind

- We have a token module (`lib/theme/tokens.ts`). Same tokens as the design system. `StyleSheet.create({ ... })` consumes them.
- No runtime cost (styled-components has it).
- No class explosion in DevTools.
- Same code that ships in production is the same code we read in dev.

## Why no `react-native-paper` / `native-base`

- We own the brand. Off-the-shelf component kits ship their own styles that we'd be fighting.
- Their theming is generic; ours is brand-specific.
- The handful of primitives we need (Button, Chip, Input) is small enough to own.

## Why `expo-video` not `expo-av`

- `expo-av` is deprecated as of SDK 51. `expo-video` is the replacement.
- Better performance, better gesture support, better mid-roll handling.
- SDK 57 ships `expo-video` as the default.

## What we don't do in mobile

- ❌ No Redux / MobX / Zustand. Context + react-query.
- ❌ No styled-components / nativewind. StyleSheet + tokens.
- ❌ No react-native-paper. Own components.
- ❌ No firebase / supabase. We have our own backend.
- ❌ No analytics SDK other than Sentry + PostHog (Phase 5).
- ❌ No crashlytics. Sentry handles it.
- ❌ No App Center. EAS Build + Sentry.
- ❌ No custom fonts other than Playfair + Inter.
- ❌ No light theme. The product is dark-only.
