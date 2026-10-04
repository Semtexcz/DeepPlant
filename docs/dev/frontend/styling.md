---
type: governance
status: active
canonical_for:
  - frontend-styling-architecture
read_when:
  - frontend-change
  - styling-change
  - editor-frontend-work
update_when:
  - styling-architecture-change
depends_on:
  - docs/dev/frontend/index.md
  - docs/dev/frontend/architecture.md
decision:
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
evidence:
  - docs/dev/research/engineering-editor-reuse-architecture.md
superseded_by: null
---

# Styling Architecture

> **Question this document answers:** which styling approach is canonical for the
> Engineering Editor, and how is styling owned?

## Options evaluated

Evaluated against the actual DeepPlant needs: Vue 3 + Vite, a **local**
engineering application, agent-driven development, minimal infrastructure, clear
ownership, replaceable tooling, and future Reka UI primitives when a concrete
accessible primitive is needed.

| Option | Fit | Assessment |
|---|---|---|
| Scoped / native CSS | Native, zero infrastructure, excellent for SVG and canvas | Necessary but insufficient alone: ordinary UI drifts into a growing global stylesheet with no local ownership |
| Tailwind CSS | Mature, popular utility-first | Viable, but heavier configuration/toolchain surface than needed and a larger default framework footprint |
| **UnoCSS** | Vite/Vue-native, on-demand utilities, lightweight, no visual component framework | **Selected** for ordinary utility-first application styling |

UnoCSS is selected because it is Vite-native, generates only the utilities that
are used, adds minimal infrastructure, does not impose a visual component
framework, and coexists cleanly with explicit engineering/canvas CSS.

## Canonical layering

```text
Vue
│
├── Vue Flow
│   └── graph / canvas infrastructure
│
├── Reka UI (only when a concrete accessible primitive is needed)
│   └── dialogs / menus / popovers / tabs / etc.
│
└── UnoCSS
    └── ordinary application presentation
```

The target principle is:

```text
semantic design tokens
+ utility-first styling for ordinary application UI
+ scoped / component-specific CSS where it is clearer
+ minimal explicit third-party overrides
```

Global feature styling must **not** remain the default long-term architecture.

Do **not** adopt "everything must be UnoCSS". Native or scoped CSS remains the
right choice for:

- SVG-specific behavior;
- specialized engineering visuals;
- pseudo-elements;
- complex selectors;
- Vue Flow integration overrides;
- visual behavior clearer in CSS than in a long utility list.

Third-party overrides (for example Vue Flow classes) stay minimal, explicit, and
documented where they are not obvious.

## Current state (implemented)

The canonical layering is now applied, not merely decided:

| Layer | Location | Owns |
|---|---|---|
| Semantic design tokens | `apps/editor/src/styles.css` (`:root`) | `--dp-bg`, `--dp-surface`, `--dp-border`, `--dp-text`, `--dp-muted`, `--dp-accent`, `--dp-valid-*`, `--dp-invalid-*`, `--dp-ink` — meaning, not component detail |
| Utility layer | `apps/editor/uno.config.ts` + `virtual:uno.css` imported by `src/main.ts` | ordinary application presentation: layout, spacing, sizing, typography, borders, backgrounds, interaction states |
| Component CSS | `*.vue` scoped `<style>` | specialized component behaviour that utilities express less clearly |
| Vue Flow integration | `ProcessPfdCanvas.vue` scoped `:deep(...)` | framework node-wrapper resets |
| Global CSS | `apps/editor/src/styles.css` | semantic tokens, minimal reset, document/root sizing, global typography defaults — nothing else |

UnoCSS is one preset (`presetWind3`) with no reset package, no directive
transformer, and no second utility framework. Utilities never hard-code colours:
they reference the semantic tokens through bracket values, for example
`bg-[var(--dp-surface)]` and `text-[var(--dp-muted)]`, so the token layer stays
the single place DeepPlant colour meaning is defined and remains easy to replace.

Two scoped `:deep(...)` integration selectors exist and are documented where they
live:

- `ProcessPfdCanvas.vue` neutralises `.vue-flow__node-deeplantProcessStep`, because
  the framework renders the node wrapper and the engineering symbol — not a
  generic card — is the visual.
- `ProcessNode.vue` makes `.vue-flow__handle` visually inert, because the handles
  only express DeepPlant presentation anchors while the canonical SVG symbol is
  the visual.

`ProcessNode.vue` additionally keeps its symbol sizing, selected treatment, and
label geometry as scoped component CSS: those are component invariants, not
ordinary UI.

## Rules for new styling work

- Add ordinary application presentation as UnoCSS utilities in the owning
  component, not as a new global selector.
- Add semantic meaning as a `--dp-*` token in `src/styles.css`, not as a
  component-local literal, when more than one surface must agree on it.
- Keep specialized engineering/SVG/Vue Flow behaviour in the owning component's
  scoped CSS, with a comment stating why the selector is framework-facing.
- Do not add a second utility framework, a CSS reset package, or a component
  framework.
