---
type: governance
status: active
canonical_for:
  - python-typing-policy
read_when:
  - python-change
  - typing-change
  - python-review
update_when:
  - python-engineering-contract-change
depends_on:
  - docs/dev/python/index.md
  - docs/dev/python/conventions.md
  - docs/dev/workflow/quality.md
decision: []
evidence: []
superseded_by: null
---

# Typing

> **Question this document answers:** how should DeepPlant use Python's type
> system so it acts as an architectural safety net rather than decoration?

## Baseline (implemented)

Pyright runs in **strict** mode and is a required gate:

```toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
include = ["src", "tests", "tools"]
exclude = ["src/deepplant/editor/desktop_qt/"]
```

- Keep Pyright strict as the baseline. Do not weaken the mode to make code pass.
- The `desktop_qt/` package is excluded from the **default** run only because the
  fast `dev`/`check` environment deliberately does not install the multi-hundred
  megabyte Qt runtime. It is **not** untyped: the native packaging jobs run
  `make typecheck-desktop` (`pyrightconfig.desktop.json`), which mirrors the
  strict settings with PySide6 available and keeps every module in scope. There
  is **no blanket `type: ignore`** for the Qt module.
- Ruff (`UP`) already modernizes syntax; keep the 3.12 syntax it enforces.

## Canonical rules

### Public signatures

- Annotate every public parameter and return type. A caller should never have to
  read the body to know the contract.
- `-> None` is required for functions that return nothing; do not omit it.
- Prefer precise types over `object` in a public signature. Reach for `object`
  only when a value is genuinely opaque, and narrow it at the point of use.

### `Any` and `Unknown`

- **Avoid `Any` in ordinary code.** It disables checking at exactly the boundary
  where mistakes are most likely.
- `Any` is acceptable only at a genuine untyped boundary (for example a value
  decoded from `yaml.safe_load`, or a third-party return the platform does not
  type), and it must be narrowed to a real type before use.
- Do not let `Any` propagate through a signature or a return type. Narrow and
  convert.
- Do not silence an `Unknown` with a blanket ignore; resolve the underlying type.

### `Protocol` versus inheritance

- Use `typing.Protocol` for **structural** boundaries: a function or layer needs
  "something with this shape", not a specific base class.
- Use inheritance only for a genuine substitutable relationship. Do not inherit
  for code reuse alone (see [architecture.md](architecture.md#pythonic-solid)).
- DeepPlant currently has few explicit interfaces; a plain function or a concrete
  object is the default. Introduce a `Protocol` only where multiple
  implementations or testing needs justify it.

### Type narrowing

- Narrow from a wide type to a precise one, and let the checker see it:
  `isinstance`, `is None`, `assert isinstance(...)`, `TypeGuard`, or an explicit
  validation function.
- Untrusted input is narrowed before it is trusted. `io.load_plant` checks the
  decoded document is a `dict` before handing it to Pydantic.
- Prefer a real narrowing over a `cast`. Use `typing.cast` only when the checker
  cannot know a fact that is genuinely true, and keep it local.

### Generics

- Use built-in generics (`list[str]`, `dict[str, int]`, `tuple[str, ...]`) and the
  modern syntax; the codebase targets 3.12.
- Do not introduce a custom generic or `TypeVar` unless a real, reused
  polymorphism needs it. A one-off is not a reason.

### Optional values

- Model absence explicitly with `T | None`. `None` means "not authored"; an empty
  container means "authored and empty". Do not overload one to mean the other
  (`PlantModel.process` is `ProcessModel | None`, and an explicitly empty
  `ProcessModel` is a distinct, valid value).
- Do not use a sentinel string or a magic value where `None` is correct.

### Type aliases

- Use a type alias to name a meaningful type once (`NonEmptyString =
  Annotated[str, StringConstraints(...)]`).
- Name it for the concept, not the implementation. Do not create an alias layer
  that adds a hop without adding meaning.

### Modern Python 3.12 syntax

- `X | Y` instead of `Optional`/`Union`.
- Built-in generics instead of `typing.List`/`Dict`/`Tuple`.
- `from __future__ import annotations` only where the module needs forward
  references or to keep annotations lazy; do not add it mechanically.
- `Self` for a validator that returns `self` (Pydantic `model_validator`).

### Typed structured data versus dictionaries

- Prefer a typed structure (dataclass, Pydantic model, `TypedDict`) over a plain
  `dict` crossing a boundary. A dictionary loses the field names, types, and the
  checker.
- A `dict[str, object]` is acceptable for a genuinely dynamic payload (a
  JSON-ready envelope whose shape the transport serializes), and the builder
  should be small and typed at its edges.

### Domain-specific identifiers and quantities

- **Do not wrap every primitive in a new class.** A `PlantId(str)` that exists
  only to rename `str` adds a layer and no invariant.
- Introduce a named type only when it carries a real distinction or invariant:
  a validated constraint (`NonEmptyString`), a qualified engineering value, or a
  genuinely separate identity namespace.
- Keep separate identity namespaces separate. Process ids, physical ids,
  connection ids, and piping ids are distinct; a shared "id" type must not blur
  them (see [architecture.md](architecture.md#two-engineering-concepts-that-must-remain-distinct)).
- Qualified engineering quantities (a magnitude plus a represented unit, ADR-0013)
  are a real concept and get a real type when that slice is implemented; do not
  pre-build one before the current requirement justifies it.

## Anti-patterns to avoid

- `def process(data: Any) -> Any:` — a fully unchecked boundary.
- `# type: ignore` or `# pyright: ignore` used to make a real problem quiet.
  Fix the type design; if a suppression is genuinely required, scope it to one
  line and add a comment explaining why.
- `cast(...)` used to tell the checker a fact that is not actually guaranteed.
- A `dict` with stringly-typed keys flowing through three modules.

## Related

- [index.md](index.md) — the contract home and review checklist.
- [conventions.md](conventions.md) — data shapes and the Pydantic boundary.
- [quality.md](../workflow/quality.md) — the Pyright gates and their scope.
- [workflow/packaging.md](../workflow/packaging.md) — the desktop type-check job.
