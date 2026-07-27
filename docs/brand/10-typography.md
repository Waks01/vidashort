# Typography reference

## Font loading

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,800;0,900;1,700;1,800;1,900&family=Inter:wght@400;500;600;700;800&display=swap">
```

## CSS variables

```css
--font-display: 'Playfair Display', Georgia, serif;
--font-body:    'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono:    'SF Mono', Menlo, Consolas, monospace;
```

## Roles (locked)

| Use | Font | Weight | Style | Example |
|---|---|---|---|---|
| Wordmark | Playfair Display | 800 | italic | "vidashort" |
| Hero / splash title | Playfair Display | 900 | italic | "Endless Drama." |
| Modal title | Playfair Display | 800 | italic | "Unlock the next episode" |
| Section title | Playfair Display | 700 | italic | "Continue Watching" |
| Player / feed title | Playfair Display | 800 | italic | "The CEO's Forbidden Bride" |
| Top bar title | Inter | 700 | normal | "Settings" |
| Body copy | Inter | 400 | normal | "Watch the full series…" |
| Button label | Inter | 700 | normal, letter-spacing 0.05em | "Continue" |
| Chip / pill label | Inter | 600 | normal | "Romance" |
| Coin count | Inter | 800 | normal, tabular-nums | "12,450" |
| VIP label | Inter | 800 | uppercase, letter-spacing 0.18em | "VIP" |
| Tab bar label | Inter | 600 | normal, 10px | "Home" |
| Error code | SF Mono | 400 | normal | "MEDIA_ERR_DECODE" |

## Type scale (locked)

| Token | Size | Line height | Use |
|---|---|---|---|
| `--text-xs` | 11px | 1.4 | Tab bar, error codes, ad labels |
| `--text-sm` | 12px | 1.45 | Body small, captions, hints |
| `--text-base` | 14px | 1.5 | Body default, input, button |
| `--text-md` | 16px | 1.5 | List item, form label |
| `--text-lg` | 18px | 1.4 | Section title, top bar title |
| `--text-xl` | 22px | 1.3 | Player title, big number |
| `--text-2xl` | 28px | 1.2 | Modal title, hero |
| `--text-3xl` | 32px | 1.15 | Splash title |
| `--text-4xl` | 40px | 1.1 | Wallet balance, daily reward day counter |

## Tracking

```
--tracking-tight:  -0.01em;
--tracking-normal:  0;
--tracking-wide:    0.05em;  /* default for buttons */
--tracking-widest:  0.18em;  /* VIP, "MARQUEE" pill, error codes */
```

## Weights — what to use when

- **400** — body only. Never for UI.
- **500** — secondary UI (less important links, less important labels).
- **600** — chips, list items, tab bar.
- **700** — buttons, top bar title, primary labels.
- **800** — display-leaning UI (coin counts, modal titles, VIP).
- **900 italic** — hero, splash, marketing.

## Display italics

Playfair Display italic is the brand's emotional voice. Use it for:
- Modal titles
- Section titles
- Player / feed episode titles
- Splash
- Wordmark

Do NOT use it for:
- Buttons
- Form labels
- Body
- Error messages
- Tab bar

## Common mistakes (avoid)

- ❌ Playfair 400 — looks anaemic. Use 700+.
- ❌ Playfair in a button — it doesn't render well at small sizes.
- ❌ Inter 800 for body — too heavy, looks like display type.
- ❌ Mixed weights in one line ("Welcome **back**, friend") — choose one.
- ❌ Unitalicised Playfair for drama — always italic.
- ❌ Underlined text — never. We don't have a link convention that needs it.
- ❌ ALL CAPS Inter at any weight below 800 — reads like shouting, not brand.
