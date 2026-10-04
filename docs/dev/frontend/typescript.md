---
type: governance
status: active
canonical_for:
  - frontend-typescript-safety
read_when:
  - frontend-change
  - typescript-change
  - editor-frontend-work
update_when:
  - typescript-policy-change
depends_on:
  - docs/dev/frontend/index.md
  - docs/dev/frontend/architecture.md
decision: []
evidence: []
superseded_by: null
---

# TypeScript Safety

> **Question this document answers:** how must TypeScript be used in the editor
> frontend so the type system acts as an architectural safety net rather than
> decoration?

`vue-tsc` owns type checking and remains a separate gate from lint, tests, and
build. TypeScript is a **safety mechanism**: the compiler settings plus the rules
below are the first defense against a boundary mistake.

## Compiler baseline (implemented)

`apps/editor/tsconfig.json` already enables strict checking. Keep:

```text
strict
noUncheckedIndexedAccess
noImplicitOverride
noUnusedLocals
noUnusedParameters
isolatedModules
```

These are not weakened to make code compile. Do not add `// @ts-expect-error` or
relax a compiler option to silence a real problem; fix the type design instead.

## Runtime type environments (implemented)

The frontend has two real runtimes — the browser and the Node-executed tooling —
so it has two explicit TypeScript environments. The runtime boundary **is** the
type-system boundary:

```text
apps/editor/tsconfig.json             browser / frontend
  src/**/*.ts  src/**/*.vue           production application
  tests/**/*.ts                       Vitest verification
  env.d.ts
  → DOM / Vue / Vite client APIs      (`types: ["vite/client"]`)
  ✗ Node globals

apps/editor/tsconfig.node.json        Node / tooling
  e2e/**/*.ts                         Playwright E2E suite
  playwright.config.ts
  vite.config.ts
  uno.config.ts
  → Node APIs and `node:*` allowed    (`types: ["node"]`)
```

- `tsconfig.json` is the application + Vitest config (`vue-tsc`). It must **never**
  expose `node` through `compilerOptions.types`: production browser code under
  `src/**` must not be able to use `process`, `Buffer`, or `node:*` and still type
  check.
- `tsconfig.node.json` is the Node-executed tooling config. It covers only the
  config files and the E2E suite, and must not include `src/**` or `tests/**`.

`tsconfig.node.json` extends `tsconfig.json` for the shared compiler baseline but
overrides `lib` and `types` so the Node environment stays explicit, and both stay
strict. They are checked independently — deliberately **no** TypeScript project
references — by the single canonical command:

```bash
make frontend-typecheck   # → pnpm run typecheck
```

which runs `pnpm run typecheck:browser` (`vue-tsc -p tsconfig.json`) and then
`pnpm run typecheck:node` (`tsc -p tsconfig.node.json`). Both must pass; neither
runtime may silently borrow the other's globals. This split exists because there
are now two real runtimes, not to introduce a general multi-tsconfig framework:
keep it to these two configs.

## Prefer

- Inference for obvious local implementation variables.
- Explicit types at public/module boundaries (exported functions, DTOs, props).
- `unknown` for untrusted transport data, then runtime narrowing.
- Discriminated unions for finite state (for example selection kinds).
- `readonly` where it meaningfully expresses ownership.
- Narrow, purpose-specific types over broad shared ones.

The current DTOs (`process-pfd/transport/dto.ts`) are `readonly` and the
selection type in `process-pfd/view-models/inspector.ts` is a discriminated
union — keep that style.

## Avoid

- Explicit `any` without a documented interoperability reason. `any` is a lint
  error; the only escape hatch is an inline `eslint-disable` with a stated
  reason, and a stale disable is itself an error.
- Casts used merely to silence the compiler.
- Giant shared type files.
- Duplicate semantic/domain models (there is deliberately no TypeScript
  `PlantModel`).
- Boolean-heavy state where a finite state union is clearer.

## Assertions (`as`)

All `as` assertions are not banned. Distinguish two cases:

```text
justified   narrowing after runtime validation, or a framework interoperability
            boundary where the framework type is genuinely known
unsafe      a cast used to bypass the type design and avoid fixing it
```

A justified assertion is fine, for example after an explicit runtime check has
already established the shape. An unsafe assertion is a review failure: it hides
a design problem rather than expressing a checked fact. When in doubt, prefer a
type guard or a validating parser over a cast.

## Untrusted input

Data coming from the local FastAPI boundary is `unknown` until narrowed. The
canonical pattern is the explicit runtime narrowing in
`process-pfd/transport/projection-contract.ts` (reached through
`process-pfd/transport/api.ts`), which raises `ProjectionContractError` with an
actionable message when the payload does not match the DTO contract. A contract mismatch
must fail clearly; it must never silently produce a half-valid view.
