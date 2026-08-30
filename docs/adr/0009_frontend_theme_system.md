# ADR-0009: Frontend Theme System (CSS Tokens + ThemeProvider)

## Status

Accepted

---

## Context

The frontend currently styles UI with ad-hoc Tailwind utility classes
(e.g. `bg-slate-50`, `bg-teal-600`, `text-slate-800`) scattered across
feature views. There is no dark mode, no shared design tokens, and no
single place to change colours or surfaces.

Planned work includes:

- Coherent light and dark themes
- A future colourblind-friendly (or other accessibility) theme
- A shared component library so styling changes are localised
- A home page, collapsible sidebar, and more polished layout

Without a token-based theme system, every new mode or visual change
would require hunting through feature components. Theme preference is
also a client-side concern and should not wait on a full user/profile
backend.

---

## Decision

The frontend will adopt a **semantic CSS token system** driven by a
`data-theme` attribute on `<html>`, with a React `ThemeProvider` that:

1. Defaults to the user’s system preference (`prefers-color-scheme`)
2. Supports an explicit override: `"light" | "dark" | "system"`
3. Persists the choice in `localStorage`
4. Updates live when the OS theme changes while preference is `"system"`

### Token model

Semantic tokens (not raw palette colours) are defined as CSS custom
properties and mapped into Tailwind via `@theme` in `index.css`:

| Token group      | Examples                                              | Purpose                       |
| ---------------- | ----------------------------------------------------- | ----------------------------- |
| Surfaces         | `--background`, `--card`, `--muted`                   | Page and card backgrounds     |
| Text             | `--foreground`, `--muted-foreground`                  | Primary and secondary text    |
| Borders          | `--border`                                            | Dividers and control outlines |
| Brand / actions  | `--primary`, `--primary-foreground`                   | Buttons, links, focus rings   |
| Feedback         | `--success`, `--warning`, `--destructive`             | Status and alerts             |
| Knowledge status | `--status-new`, `--status-learning`, `--status-known` | Vocab/character state colours |

Components and feature views must use semantic utilities
(`bg-background`, `text-foreground`, `bg-primary`, `text-status-known`,
etc.) instead of hard-coded palette classes (`bg-slate-50`, `bg-teal-600`).

### Theme values

| Value    | Behaviour                                          |
| -------- | -------------------------------------------------- |
| `system` | Follow `prefers-color-scheme`; react to OS changes |
| `light`  | Fixed light theme                                  |
| `dark`   | Fixed dark theme                                   |

Additional themes (e.g. `colorblind`) are added by:

1. A new `[data-theme="…"]` block in CSS
2. An entry in the theme list used by the UI control

No component changes are required for a new theme beyond the control
that selects it.

### Control placement

- **Near term:** a compact theme control in the top navigation (or
  settings area). Preference is stored only in `localStorage`.
- **Later:** the same control can move into the user/sidebar menu when
  learner profiles exist. Optionally, preference may later be synced
  to the backend; until then client-side storage is sufficient.

### Out of scope for this ADR

- Full component library implementation (separate follow-up)
- Backend persistence of theme preference
- Colourblind or other accessibility themes (token model is designed
  so they can be added later without structural change)
- i18n / language switcher (orthogonal; may share top-nav space)

---

## Consequences

### Positive

- Single source of truth for colours and surfaces
- Light / dark (and future modes) change in one place
- System preference is respected by default; users can still override
- Feature views become easier to keep visually consistent
- Theme preference does not depend on auth or learner profile work
- Aligns with common modern frontend practice (semantic tokens +
  `data-theme` / class strategy)

### Negative

- Existing feature views must be migrated off hard-coded palette
  utilities (incremental; can be done view-by-view)
- Slightly more CSS and provider boilerplate than pure utility classes
- Developers must prefer semantic tokens; linting or review is needed
  to avoid regressions to raw colour classes

### Neutral

- `localStorage` is the source of truth until a backend
  user preference API exists
- Tailwind CSS 4 `@theme` mapping is the integration point; if the
  styling toolchain changes, tokens remain the abstraction layer
