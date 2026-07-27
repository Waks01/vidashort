# Visual style guide

Companion to `docs/brand/00-overview.md`. This is the practical "do this, not that" reference for screen designers.

## Screen anatomy (every screen has these)

| Slot | What goes there | Style |
|---|---|---|
| Status bar | OS time, battery, signal | Native (don't draw our own) |
| Top bar (56px, fixed) | Back button (left, optional) · Title (center) · Right actions (notifications, etc.) | `--color-bg-glass` + `backdrop-filter: blur(20px) saturate(180%)` |
| Main content | The screen's primary view | Full bleed for player, padded for lists |
| Bottom nav (64px, fixed) | 5 tabs for the current role | `--color-bg-glass-dark` + `backdrop-filter: blur(20px) saturate(180%)` |
| Safe areas | Top notch, bottom home indicator | `padding-top: env(safe-area-inset-top)` / `padding-bottom: env(safe-area-inset-bottom)` |

On desktop (≥ 768px), the whole phone is wrapped in a 390×844 container with bezel, drop shadow, and a floating "← Index" pill.

## Component patterns

### Buttons

```
.btn            — base, 52px height, pill radius, Inter 700
.btn--primary   — magenta gradient, white text
.btn--gold      — gold gradient, dark text (only for coins / VIP / reward)
.btn--secondary — elevated dark bg, magenta border
.btn--ghost     — transparent, 44px height (for low-emphasis)
.btn--sm        — 40px
.btn--lg        — 60px
.btn--block     — 100% width
```

Active state: `transform: scale(0.97)`.
Hover state (desktop): `filter: brightness(1.1)`.
Loading state: `aria-busy="true"` → spinner inside, `pointer-events: none`.

### Cards

```
.card           — base, --color-bg-elev-1 bg, 1px border, --radius-lg
.card--hover    — adds lift on hover
.card--gold     — gold border, gold inset shadow (for VIP / premium surfaces)
```

### Inputs

```
.input          — 52px height, --color-bg-elev-1 bg, 1.5px border
.input--error   — red border
.input--with-icon — left padding for icon
.input-group    — wrapper with absolute-positioned icon/action
```

Labels are above the input, not floating. Helper text below. Error text in red.

### Lists (Library, Wallet, Notifications, Comments)

- List item: 64px tall, 16px horizontal padding, divider line below.
- Avatar (if any): 40px circle, left.
- Title: Inter 600, 14px, single line ellipsis.
- Subtitle: Inter 400, 12px, single line ellipsis, `--color-text-2`.
- Trailing icon (right): chevron or count badge.

### Modals

- Backdrop: `rgba(0, 0, 0, 0.85) + backdrop-filter: blur(8px)`.
- Card: 90% width, max 400px, `--radius-xl` (24px), `--color-bg-elev-2` bg, `--shadow-modal`.
- Enter animation: `cubic-bezier(0.34, 1.56, 0.64, 1)` scale + slide.
- Close X: top-right, 32×32 round, always visible (even on paywall — App Store rule).
- Body: padded 24px horizontal.
- Footer (if any): 24px padding, top border, sticky.

### Bottom sheets

- Drag handle: 36×4 px, `--color-border-strong`, centered top.
- Header: title + close X.
- Body: scrollable, max 80vh.
- Slide up: `cubic-bezier(0.34, 1.56, 0.64, 1)` from below.
- Drag to dismiss: phase 4. Phase 1 uses snap open/close only.

### Toasts

- Bottom: 80px (above bottom nav).
- Background: `--color-bg-elev-2`, 1px border (color matches variant).
- Pill radius, 12px padding, Inter 600 12px.
- Variant: success (green border + icon), error (red), info (blue), warning (orange).
- Auto-dismiss: 2.5s. Long-press to dismiss early.

### Empty states

- Icon in a 96px circle, `--color-bg-elev-1` bg, `--color-text-3` color, 40px icon size.
- Title: Playfair 700 italic, 22px.
- Body: Inter 400, 12px, max 280px width.
- One CTA below, max 200px width.

### Loading (skeleton)

- Block: 1px border `--color-border`, `--radius-md`.
- Shimmer: 200% wide linear gradient, slides from 200% to -200% over 1.5s.
- Use for: feed cards, list items, profile.

### Ad placeholders

- Sponsored pill (top-left, always): 10px Inter 800, all caps, "SPONSORED" or "AD".
- Banner ad (bottom of detail screens): 56px tall, dark bg, "Install Acme VPN — Free for 7 days" copy, magenta CTA.
- Interstitial: full-bleed gradient poster + 5s countdown to X.
- Rewarded: 3 states (loading 1.5s / playing 15s with countdown / complete with confetti + toast).

## Layout patterns

### Cards in a grid (Discover, Search, Library)

- 2 columns on phone, 3+ on tablet.
- Card aspect ratio: 9:16 (vertical poster) or 16:9 (landscape banner).
- Gap: 8px.
- Padding: 16px on the screen, 0 on the grid.

### Lists with sections (Wallet, Profile, Settings)

- Section header: 11px Inter 800, uppercase, `--tracking-widest`, `--color-text-3`, 8px padding below.
- Section items: 12px below each.

### Centered content (Onboarding, Paywall, Auth)

- Full-bleed background (gradient or image).
- Content centered, max 360px wide, padded 24px.
- Sticky CTA at bottom (or near it).

### Player (full-screen video)

- Full bleed, no chrome by default.
- Top: 56px gradient (black 0.5 → transparent) for status bar + back button.
- Bottom-left: series title + episode # + duration (96px from bottom).
- Bottom-right: action column (avatar, heart, comment, share, coin-cost).
- Very bottom: 2px gold progress bar.
- Tap to toggle controls (3s auto-hide).

## Spacing rules

- Screen edge padding: 16px (compact lists) or 20px (lounge content).
- Inter-card gap: 8–12px.
- Section gap: 24–32px.
- Above the bottom nav: 80px (to clear the nav).
- Below the top bar: 0 (top bar has its own padding).

## Do

- ✅ Use `--space-4` (16px) for screen padding.
- ✅ Use Playfair Display italic for any "big" title.
- ✅ Use Phosphor duotone for filled states.
- ✅ Use the magenta gradient for primary actions.
- ✅ Use gold gradient for coins / VIP / reward / cash.
- ✅ Show coin cost on every locked episode.
- ✅ Add haptics to every primary tap.

## Don't

- ❌ Use emoji. Ever. As UI. As illustration. As anything.
- ❌ Use pure white (#fff) text. Cream only.
- ❌ Use a light surface. Anywhere.
- ❌ Hide the back / close / cancel button.
- ❌ Stack 3+ primary CTAs in a row.
- ❌ Use animation longer than 400ms.
- ❌ Use Comic Sans. (Yes, again. Still.)
