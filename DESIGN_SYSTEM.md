# Design System

## Visual Direction

Editorial Light with technical clarity: warm, paper-like surfaces, serif-forward headlines,
and restrained accent usage. The UI should feel like a thoughtful engineering notebook rather
than a default SaaS dashboard.

## Palette

- **Primary**: `hsl(145 32% 30%)` (olive-forest)
  - Used for primary actions, active nav states, and key highlights.
- **Accent**: `hsl(38 92% 52%)` (amber)
  - Used sparingly for CTA emphasis and important attention moments.
- **Neutrals (warm, olive-tinted)**:
  - `--color-surface`: `hsl(45 22% 97%)`
  - `--color-surface-2`: `hsl(45 16% 93%)`
  - `--color-surface-3`: `hsl(45 12% 88%)`
  - `--color-border`: `hsl(42 10% 78%)`
- **Text**:
  - Primary: `hsl(34 16% 16%)`
  - Muted: `hsl(34 10% 42%)`
  - Subtle: `hsl(34 8% 58%)`
- **Semantic**:
  - Success: `hsl(145 45% 36%)`
  - Warning: `hsl(38 90% 48%)`
  - Danger: `hsl(3 70% 50%)`

### Dark Palette

- `--color-surface`: `hsl(220 12% 10%)` (warm charcoal)
- `--color-surface-2`: `hsl(220 10% 14%)` (elevated surface)
- `--color-surface-3`: `hsl(220 8% 19%)` (tertiary surface)
- `--color-border`: `hsl(220 8% 24%)`
- `--color-text`: `hsl(40 15% 90%)` (warm off-white)
- `--color-text-muted`: `hsl(40 8% 62%)`
- `--color-text-subtle`: `hsl(40 6% 46%)`
- `--color-primary`: `hsl(145 35% 45%)`
- `--color-primary-light`: `hsl(145 25% 18%)`
- `--color-accent`: `hsl(38 85% 58%)`

## Typography

- **Display**: `Fraunces`
- **Body**: `DM Sans`
- **Mono**: `JetBrains Mono`

Rationale: Fraunces provides editorial character and hierarchy; DM Sans keeps controls and
body content readable; JetBrains Mono preserves code legibility.

Rules:

- Headings use display font with `tracking-tight`.
- Body text uses `leading-relaxed` by default.
- Inter/Roboto/Arial are not used as primary fonts.

## Spacing

- Base grid: `4px`
- Density: **comfortable**
- Page gutter: `--space-6` (`24px`)
- Card padding: `--space-5` (`20px`)
- Section gap: `--space-16` (`64px`)
- Stack gap: `--space-4` (`16px`)

Token scale:

- `--space-1` `0.25rem`
- `--space-2` `0.5rem`
- `--space-3` `0.75rem`
- `--space-4` `1rem`
- `--space-5` `1.25rem`
- `--space-6` `1.5rem`
- `--space-8` `2rem`
- `--space-10` `2.5rem`
- `--space-12` `3rem`
- `--space-16` `4rem`
- `--space-20` `5rem`

## Radius

- Inputs: `--radius-md` (`8px`)
- Cards: `--radius-lg` (`12px`)
- Dialogs/highlight containers: `--radius-xl` (`16px`)
- Pills/badges: `--radius-full`

## Component Conventions

- `frontend/src/lib/components/ui/` remains generated base components.
- All app usage goes through `primitives/` wrappers for `Button`, `Input`, `Card`, `Badge`.
- Avoid raw `<button>` and `<input>` in route components.
- Chat UI composes `svelte-ai-elements` primitives first (`new-message`, `prompt-input`,
  `model-selector`, `sources`, `loader`, `shimmer`, `actions`) before custom replacements.
- Lists that can be empty include an explicit empty state with icon + headline + CTA.
- Loading states use skeletons that mirror final layout.
- Status badges use semantic tokens; color is never the only signal.

## Chat Layout Blueprint

- Desktop: left nav `240px`, conversation rail `320px`, chat canvas flexible remainder.
- Tablet: collapsible nav + single main chat column.
- Mobile: single column; conversation rail is drawer/sheet.
- Composer is sticky at bottom of chat canvas and always visible.
- Message widths:
  - assistant max `72ch`
  - user max `60ch`

## Anti-patterns For This Project

- `bg-white`, `text-gray-*`, `text-blue-*` in app surfaces.
- Unthemed shadcn variables.
- Arbitrary spacing drift (`mt-3`, `p-2`) when scale tokens exist.
- Flat pages without hierarchy (no display headings, no section rhythm).
- Spinner-only loading states where skeletons should be shown.

## Maintenance

When a UI decision changes, update this file first, then align:

1. `frontend/src/app.css` tokens
2. `tailwind.config.js` mapping
3. primitive component defaults
4. `AGENTS.md` references
