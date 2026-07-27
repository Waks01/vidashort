# Design tokens

The complete token system, machine-readable. Source of truth: `apps/design/styles/tokens.css` in the prototype, and the TS module `apps/mobile/src/lib/theme/tokens.ts` once mobile is built.

The two implementations MUST stay in sync. When you change a token in the prototype, change it in the mobile module the same day. The cross-check is: every var defined here appears in both files with the same value.

## Layout tokens

```css
--phone-width:  390px;   /* iPhone 14 Pro width */
--phone-height: 844px;   /* iPhone 14 Pro height */
--topbar-height: 56px;
--bottomnav-height: 64px;
--safe-top:      env(safe-area-inset-top, 0);
--safe-bottom:   env(safe-area-inset-bottom, 0);
```

## Spacing

8px base. See `00-overview.md § 6` for the scale.

## Radius

See `00-overview.md § 7`.

## Z-index

```
--z-bottomnav: 50;
--z-topbar:    60;
--z-sheet:     90;
--z-modal:     100;
--z-toast:     200;
--z-confetti:  300;
```

Modals over modals (rare): increment. Toast always on top of all chrome.

## Animation

```css
--duration-fast:  150ms;
--duration-base:  220ms;
--duration-slow:  320ms;

--ease-out:       cubic-bezier(0.4, 0, 0.2, 1);
--ease-in:        cubic-bezier(0.4, 0, 1, 1);
--ease-bounce:    cubic-bezier(0.34, 1.56, 0.64, 1);
--ease-smooth:    cubic-bezier(0.2, 0.6, 0.4, 1);
```

## Effects

Already covered in `00-overview.md § 4` and `§ 11`.

## Naming convention

- `--color-*` for color
- `--space-*` for spacing
- `--radius-*` for border-radius
- `--text-*` for font size
- `--tracking-*` for letter-spacing
- `--leading-*` for line-height
- `--shadow-*` for box-shadow
- `--glow-*` for filter: drop-shadow
- `--gradient-*` for background-image linear/radial gradients
- `--z-*` for z-index
- `--duration-*` and `--ease-*` for motion
- `--font-*` for font-family

## Mobile mirror

When mobile is built, this becomes a TypeScript file:

```ts
// apps/mobile/src/lib/theme/tokens.ts
export const colors = {
  bg:        '#0a0608',
  bgElev1:   '#14090d',
  bgElev2:   '#1f0e15',
  accent1:   '#ff1f5a',
  accent2:   '#b3002b',
  accent3:   '#ff4d80',
  gold1:     '#ffe27a',
  gold2:     '#d4a017',
  gold3:     '#8b6914',
  text1:     '#f5e9d4',
  text2:     '#b8a99a',
  text3:     '#6b5a4d',
  border:    '#2a1a20',
  borderStrong: '#4a2a35',
  success:   '#2ed47a',
  error:     '#ff3838',
  warning:   '#ffb648',
  info:      '#4dabf7',
} as const;

export const spacing = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48 } as const;
export const radius  = { sm: 8, md: 12, lg: 16, xl: 24, pill: 999 } as const;
export const text    = { xs: 11, sm: 12, base: 14, md: 16, lg: 18, xl: 22, '2xl': 28, '3xl': 32, '4xl': 40 } as const;
```

Both files must be edited together. Add a CI step in Phase 1 that diffs them.
