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

## Current state vs deferred

- **Current (implemented):** one global stylesheet, `apps/editor/src/styles.css`,
  with hand-authored `--dp-*` CSS custom properties. This is honest global CSS
  debt, **not** a migrated design-token or utility system.
- **Canonical rule:** new ordinary application UI should move toward semantic
  tokens plus utility-first styling rather than adding more global selectors.
- **Deferred to #81:** integrating UnoCSS, defining the token layer, and migrating
  the existing global CSS.

This contract records the decision only. It deliberately adds **no** UnoCSS
dependency, because an unused package must not be installed merely to record a
decision. #81 integrates and applies it.
