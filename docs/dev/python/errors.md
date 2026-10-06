---
type: governance
status: active
canonical_for:
  - python-error-handling
read_when:
  - python-change
  - error-handling-change
  - python-review
update_when:
  - python-engineering-contract-change
depends_on:
  - docs/dev/python/index.md
  - docs/dev/python/architecture.md
  - docs/contracts/cli.md
decision:
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
evidence: []
superseded_by: null
---

# Error Handling

> **Question this document answers:** how should DeepPlant signal, propagate, and
> report failures consistently across the semantic Core, the application layer,
> and the CLI, HTTP, and desktop boundaries?

## Semantics per layer

Each layer has one error role. Do not blur them.

```text
CLI / HTTP / desktop boundary  → translate to a user-facing message + exit/status
              ↑
Application / use-case layer   → raise a specific, named error with context
              ↑
Semantic engineering core      → raise ValueError inside Pydantic validators
```

- **Semantic Core.** Validation failures raise `ValueError` with a concise,
  engineering-specific message, inside Pydantic `model_validator`/field
  constraints. The Core raises **no** framework error and imports no CLI, HTTP, or
  GUI type. Pydantic surfaces these as `ValidationError` to the boundary.
- **Application / use-case layer.** The YAML boundary (`io.py`) converts expected
  failure modes into named errors: `PlantLoadError` and `PlantSaveError`. The
  editor application layer uses `EditorSetupError`. Each carries a message a
  caller can show without further interpretation.
- **CLI.** Typer entry points catch the named errors and print `✗ <message>` to
  stderr, then `raise typer.Exit(code=1)`. The CLI never prints a raw traceback
  for an expected user error.
- **HTTP adapter.** The FastAPI layer maps an application result to an HTTP
  status: a valid projection is `200`, a semantically valid but non-projectable
  model is `422` with an honest message. It exposes no raw internal traceback as
  an ordinary response body.
- **Native desktop boundary.** The desktop host reports a launch failure as a
  user-facing message (a window error / concise CLI error), not a traceback.

**The core must not depend on FastAPI or Typer exceptions.** Framework error
types stay in their boundary layer.

## Preserve useful context

An engineering error should name what an engineer would need to fix it:

- the affected element (the step, connection, or piping realization),
- the invalid value,
- a unit where a quantity is involved,
- the violated invariant or rule id (for example "duplicate ProcessStep id",
  "unknown connection 'X'").

Prefer a specific message over a generic one. `duplicate equipment id(s): P-101`
is useful; `invalid model` is not. Where a rule has an identifier (S1–S4, C1,
P1–P5), the message may reference it so the reader can find the contract.

## Do not

- **Do not swallow exceptions broadly.** A bare `except Exception: pass`, or a
  broad `except` that hides a real failure, is not acceptable in ordinary code. A
  genuinely defensive `except Exception` must be deliberate, documented, and
  leave evidence (as the desktop self-check does, which records the failure in a
  diagnostic report).
- **Do not wrap unnecessarily.** Re-raising a `PlantLoadError` as another
  `PlantLoadError` adds no context. Convert only when you can add context or
  cross a genuine layer boundary. Use `raise ... from exc` to keep the cause.
- **Do not expose a raw traceback as an ordinary user-facing diagnostic.** A raw
  Pydantic or PyYAML error is not a user message; translate it (as `io.py` does)
  into a concise one.
- **Do not introduce a new exception hierarchy** unless a concrete current
  requirement justifies it. DeepPlant's named errors are small and purposeful:
  `PlantLoadError`, `PlantSaveError`, `EditorSetupError`,
  `ProcessRenderError`, `ProcessPfdProjectionError`,
  `MissingEditorDependenciesError`, `DexpiImportError`, `DexpiExportError`,
  `EditorLaunchError`, `DesktopHostError`, and a small set of packaging errors
  under `tools/`. Add a new one only when a caller needs to distinguish a new
  failure mode.

## Boundary pattern (implemented)

The YAML boundary is the reference shape:

```text
read/parse/validate → named error with a concise message → CLI prints it, exit 1
```

`load_plant` catches `OSError`, `yaml.YAMLError`, and `ValidationError` and
re-raises `PlantLoadError` with a message naming the file and the failing field.
The CLI catches `PlantLoadError` and prints it. No framework type crosses the
layer, and no traceback reaches the user for an expected error.

## Related

- [index.md](index.md) — the contract home and review checklist.
- [conventions.md](conventions.md) — design and boundary conventions.
- [contracts/cli.md](../../contracts/cli.md) — the CLI's error and exit-code contract.
- [contracts/yaml-format.md](../../contracts/yaml-format.md) — the load/save error contract.
