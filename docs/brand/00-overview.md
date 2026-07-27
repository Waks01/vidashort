# Brand overview

> Source of truth for every visual decision. If a screen, component, or asset contradicts this document, this document wins.

## 1. One-line identity

**Glossy, dramatic, addictive.** A late-night, low-light streaming experience that feels closer to old Hollywood than to a feed app. Black + hot magenta-red + gold. Serif display + Inter body. The opposite of TikTok's bright-and-friendly.

## 2. Mood references

- **ReelShort** (primary) — the magenta-red, the gold, the serif italic, the "addictive" copy.
- **HiDrama** — the dark cinematic backdrop, the gradient poster treatments.
- **Old Hollywood posters** — drama, vignette, type that leans into the genre.
- **Late-night premium cable** (HBO / Starz idents) — the gold accent on near-black.

## 3. Voice

| We are | We are not |
|---|---|
| Sensational, dramatic | Vague, polite |
| Direct ("Unlock the next episode") | Euphemistic ("Continue your journey") |
| Reassuringly expensive | Cheap, cheerful |
| A little dangerous | Safe, neutered |
| Aimed at the user, in second person | Corporate, third person |

**Tone rules:**
- One CTA per screen, max two. Never three competing.
- Copy under 8 words per line, ideally 4–6.
- Errors are honest ("This episode won't play"), not apologetic.
- Urgency copy is allowed (timer, special offer) — but the close X / cancel / back is always visible. App Store rule.

## 4. Color tokens

Full system lives in `apps/design/styles/tokens.css`. The canonical values:

```css
:root {
  /* Surfaces */
  --color-bg:            #0a0608;   /* near-black, warm */
  --color-bg-elev-1:     #14090d;   /* card */
  --color-bg-elev-2:     #1f0e15;   /* modal, sheet */
  --color-bg-glass:      rgba(20, 9, 13, 0.72);
  --color-bg-glass-dark: rgba(10, 6, 8, 0.85);

  /* Accent — hot magenta-red (the addictive one) */
  --color-accent-1:      #ff1f5a;
  --color-accent-2:      #b3002b;
  --color-accent-3:      #ff4d80;
  --color-accent-deep:   #4a0014;
  --gradient-accent:     linear-gradient(135deg, #ff1f5a 0%, #b3002b 100%);
  --gradient-accent-hot: linear-gradient(135deg, #ff4d80 0%, #ff1f5a 50%, #b3002b 100%);

  /* Gold — coins, VIP, reward, premium */
  --color-gold-1:        #ffe27a;
  --color-gold-2:        #d4a017;
  --color-gold-3:        #8b6914;
  --gradient-gold:       linear-gradient(135deg, #ffe27a 0%, #d4a017 100%);
  --gradient-coin:       radial-gradient(circle at 35% 30%, #ffe27a 0%, #d4a017 60%, #8b6914 100%);

  /* Text */
  --color-text-1:        #f5e9d4;   /* cream — main text, never pure white */
  --color-text-2:        #b8a99a;
  --color-text-3:        #6b5a4d;
  --color-text-inverse:  #1a0e00;   /* on gold */

  /* Borders */
  --color-border:        #2a1a20;
  --color-border-strong: #4a2a35;
  --color-border-gold:   rgba(212, 160, 23, 0.4);

  /* Status */
  --color-success:       #2ed47a;
  --color-error:         #ff3838;
  --color-warning:       #ffb648;
  --color-info:          #4dabf7;
  --color-vip:           #ffb648;   /* same as warning but semantically distinct */

  /* Effects */
  --shadow-card:         0 8px 24px rgba(0, 0, 0, 0.6);
  --shadow-card-hover:   0 12px 32px rgba(0, 0, 0, 0.8);
  --shadow-modal:        0 24px 64px rgba(0, 0, 0, 0.85);
  --shadow-bottom-nav:   0 -8px 24px rgba(0, 0, 0, 0.4);
  --glow-magenta:        0 0 24px rgba(255, 31, 90, 0.45);
  --glow-gold:           0 0 24px rgba(255, 200, 80, 0.45);
}
```

### Color usage rules

- **Accent (magenta-red)** is for primary CTAs, active states, the brand wordmark accent, and the "free" feed items. Never use it for body text.
- **Gold** is reserved for coins, VIP, rewards, and premium surfaces. Never use it for a regular button.
- **Cream text** (`--color-text-1`) is for all primary text. Never use pure white (#fff) for body — it reads too cold against the warm black.
- **Status colors** are used sparingly and only for their semantic role (success = green, error = red, warning = orange, info = blue).
- **Backdrops are always dark.** Even modals over a video use `rgba(0, 0, 0, 0.85)` + `backdrop-filter: blur(8px)`. No light surfaces anywhere.

## 5. Typography

| Role | Font | Weight | Use |
|---|---|---|---|
| Display / hero / marketing | **Playfair Display** | 700, 900, italic | Wordmark, modals, big section titles, player titles |
| Body / UI / labels | **Inter** | 400, 500, 600, 700 | Everything else |
| Coin counts | Inter | 800, `font-variant-numeric: tabular-nums` | Wallet, store, daily reward |
| VIP labels | Inter | 800, `letter-spacing: 0.18em`, uppercase | VIP badges |
| Error codes | `monospace` | 400 | "Error code: MEDIA_ERR_DECODE" |

### Type scale (in `tokens.css`)

```
--text-xs:   11px
--text-sm:   12px
--text-base: 14px
--text-md:   16px
--text-lg:   18px
--text-xl:   22px
--text-2xl:  28px
--text-3xl:  32px
--text-4xl:  40px
```

### Type rules

- Display headlines are always **Playfair Display 700/900 italic**. They lean into drama.
- Player episode titles, feed titles, modal titles = Playfair 800 italic.
- Everything else = Inter.
- Line-height tight (1.1–1.2) for display, comfortable (1.4–1.5) for body.
- Never use Comic Sans, system fonts, or anything outside this list. The brand dies if the type dies.

## 6. Spacing

8px base unit. All spacing via `tokens.css`:

```
--space-1: 4px
--space-2: 8px
--space-3: 12px
--space-4: 16px
--space-5: 20px
--space-6: 24px
--space-8: 32px
--space-10: 40px
--space-12: 48px
```

Vertical rhythm = 8 / 16 / 24 / 32 / 48. No 11px, no 13px, no 17px gaps.

## 7. Radius

```
--radius-sm:   8px
--radius-md:   12px
--radius-lg:   16px
--radius-xl:   24px
--radius-pill: 999px
```

Cards = 16px, modals = 24px, sheets = 24px (top corners only), buttons = pill.

## 8. Icons

**Phosphor** via CDN, duotone weight for filled states, regular for everything else. Examples:

```html
<i class="ph ph-heart"></i>            <!-- outline heart -->
<i class="ph-fill ph-heart"></i>       <!-- filled heart -->
<i class="ph-bold ph-house"></i>       <!-- bold weight -->
<i class="ph-duotone ph-coins"></i>    <!-- duotone, the brand-favoured weight -->
```

We never draw our own icon unless it's a brand mark (logo, app icon, splash, coin). All UI icons = Phosphor.

### Top icon uses (locked)
- **Coins** = `ph-coins` or `ph-fill ph-coins` (the gold one with our custom gradient)
- **VIP** = `ph-crown`
- **Heart (like)** = `ph-heart` / `ph-fill ph-heart`
- **Home** = `ph-house`
- **Discover** = `ph-compass`
- **Library** = `ph-bookmark-simple`
- **Wallet** = `ph-wallet`
- **Profile** = `ph-user`
- **Search** = `ph-magnifying-glass`
- **Bell (notifications)** = `ph-bell`
- **Share** = `ph-share-network`
- **Comments** = `ph-chat-circle`
- **Play / pause** = `ph-play` / `ph-pause` (or `ph-fill` versions)
- **Lock** = `ph-lock`
- **Settings** = `ph-gear`
- **Sign out** = `ph-sign-out`

## 9. Logo + app icon

### Wordmark — "vidashort"

The 3D V-Forward logo (selected, see `apps/design/assets/icons/logo-3d-v.svg`).

- "vida" in Playfair Display 800 italic.
- "V" rendered as a 3D gradient glyph (magenta → crimson) with gold rim light and a magenta halo.
- "short" in Playfair Display 800 italic, smaller (≈ 75% the height of "vida").
- Used in: top bar (compact), wordmark contexts (large), splash.

### App icon (iOS + Android)

- 1024×1024 SVG master, `apps/design/assets/icons/app-icon.svg`.
- Magenta→crimson 3D V with right arm extending into a play triangle.
- Gold rim light on the V.
- Magenta halo behind the V.
- 16×16 readability test: the V must be legible. The play arm must hint at "play."

### Splash

- Black background, full wordmark, tagline ("Endless Drama. One Swipe.") below.
- 1.5s auto-advance.

## 10. Imagery

- **No licensed photos until we sign a deal.** Use seeded `https://picsum.photos/seed/{slug}/540/960` URLs for all placeholders.
- TMDB original posters go through `vidashort.MockData.TMDB.poster(slug)` — synthetic URL until keys are wired.
- Creator uploads use a placeholder gradient poster keyed to the series title.
- Never use emoji as a substitute for illustration.

## 11. Motion

| Pattern | Curve | Duration |
|---|---|---|
| Button press | `cubic-bezier(0.4, 0, 0.2, 1)` (ease-out) | 100ms |
| Card hover / nav slide | `cubic-bezier(0.4, 0, 0.2, 1)` | 180ms |
| Modal / sheet enter | `cubic-bezier(0.34, 1.56, 0.64, 1)` (ease-bounce) | 280ms |
| Heart particle | `ease-out` | 800ms |
| Confetti | `cubic-bezier(0.2, 0.6, 0.4, 1)` | 2s |
| Coin count-up | linear, 1.2s | 1200ms |
| Page transition | `cubic-bezier(0.4, 0, 0.2, 1)` | 240ms |

Never animate a "loading" state for less than 600ms — it feels fake. Never animate a state change for longer than 400ms — it feels broken.

## 12. Sound + haptics

- **No background music** in the prototype (it competes with voiceover in recordings).
- Haptics: `navigator.vibrate(10)` on every primary tap (button, chip, action). `vibrate([10, 50, 10])` for success. `[50]` for error. In RN, use `expo-haptics` with the same intensity.
- The mobile player will add subtle video scrub haptics in Phase 4. Not now.

## 13. Accessibility

- All accent colors meet WCAG AA against `--color-bg` (4.5:1 minimum).
- All clickable areas ≥ 44×44 px.
- All form fields have associated `<label>`s.
- Modals trap focus, escape closes, return focus on close.
- All status / error states have both color AND icon (color-blind safe).
- Player must respect `prefers-reduced-motion` (skip the gradient drift, disable heart particles).

## 14. What you must NEVER do (brand)

- ❌ Use a light background anywhere.
- ❌ Use pure white text — cream (`#f5e9d4`) only.
- ❌ Use Tailwind / Bootstrap / a CSS framework.
- ❌ Use Comic Sans, system fonts, or any font outside Playfair + Inter.
- ❌ Use emoji as an icon.
- ❌ Use a non-Phosphor icon (except brand marks).
- ❌ Put a hard-to-dismiss paywall in front of the user.
- ❌ Hide the back / close / cancel button.
- ❌ Use a red that's more orange or more pink than `#ff1f5a`.
- ❌ Use gold for anything except coins, VIP, or premium.
- ❌ Use Comic Sans, again, because I will know.
