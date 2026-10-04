---
name: frontend-engineering
version: 1
purpose: Apply the canonical DeepPlant Engineering Editor frontend contract to any change under apps/editor/.
triggers: [frontend change, vue change, editor frontend, typescript frontend, styling change, component change, frontend review]
inputs:
  required:
    - frontend_change
reads:
  - AGENTS.md
  - docs/dev/frontend/index.md
  - docs/dev/frontend/architecture.md
  - docs/dev/frontend/vue.md
  - docs/dev/frontend/typescript.md
  - docs/dev/frontend/styling.md
  - docs/dev/frontend/testing.md
  - docs/dev/frontend/accessibility.md
  - docs/dev/architecture/index.md
  - docs/dev/workflow/quality.md
commands:
  - make frontend-lint
  - make frontend-typecheck
  - make frontend-test
  - make frontend-build
  - make frontend-check
  - make check
outputs:
  - scoped frontend change that follows the contract
  - frontend verification results
approval_boundary:
  may_approve: false
stop_conditions:
  - change would re-implement the semantic model or parse YAML in the browser
  - change would leak Vue Flow types outside the adapter boundary
  - change requires a new dependency without justification
  - change crosses a hard size limit without a centralized config change
  - change belongs to the #81 refactor or the #82 browser E2E slice
---

# Frontend Engineering

Use this skill for any change under `apps/editor/`. The durable rules live in
`docs/dev/frontend/`; this skill routes to them and deliberately does not restate
them, so there is one canonical copy.

## Read first

1. `docs/dev/frontend/index.md` — the contract map, the status vocabulary
   (implemented / canonical rule / deferred), and the review checklist.
2. The one topic document the change touches: `architecture`, `vue`,
   `typescript`, `styling`, `testing`, or `accessibility`.
3. `docs/dev/frontend/architecture.md` for the DeepPlant / Vue Flow boundary and
   the size/cohesion guardrails.

## Non-negotiable boundaries

- The Python semantic model stays authoritative. The browser reads the
  projection DTO, never parses YAML, and never recreates validation.
- Vue Flow stays behind `process-pfd/vue-flow-adapter.ts`:
  `Vue Flow Node != ProcessStep` and `Vue Flow Edge != ProcessStream`.
- Untrusted transport data is narrowed from `unknown` before it is trusted.

## Before review

Run the frontend gates and report their results, then apply the review checklist
in `docs/dev/frontend/index.md`:

```bash
make frontend-lint
make frontend-typecheck
make frontend-test
make frontend-build
```

`make frontend-check` runs all four and `make check` includes it.

## Scope

Do not use this skill to perform the #81 feature refactor, component/integration
tests, the UnoCSS integration and CSS migration, or #82 browser E2E. Those are
separate slices that must follow this contract.
