---
type: governance
status: active
canonical_for:
  - python-design-conventions
  - python-pydantic-boundary
  - python-ruff-rule-review
read_when:
  - python-change
  - python-review
  - pydantic-change
update_when:
  - python-engineering-contract-change
depends_on:
  - docs/dev/python/index.md
  - docs/dev/python/architecture.md
  - docs/dev/workflow/quality.md
decision:
  - docs/dev/decisions/ADR-0004-yaml-is-a-serialization-format.md
evidence: []
superseded_by: null
---

# Python Design and Conventions

> **Question this document answers:** how should DeepPlant Python code be written
> — its design, data shapes, public APIs, and boundaries — so it stays simple,
> readable, and idiomatic?

Prefer the simplest implementation that represents the actual engineering problem
correctly.

## Functions versus classes

- Use a **function** by default. It is the simplest unit that expresses a rule.
- Use a **class** when there is genuine state to carry, a group of operations that
  share that state, a framework contract to satisfy, or a value to name.
- Do not create a class with one method and no state; that is a function wearing a
  costume.

## Dataclasses and enums

- Use `@dataclass(frozen=True)` for internal, framework-free value carriers and
  result objects (for example `EditorProjectionView`). Immutability keeps a value
  safe to pass around and compare.
- Use an `Enum` when a value is a closed set of named alternatives that the code
  switches on. Do not use a bare string where a closed vocabulary is genuinely
  intended, and do not use an enum to model an open, business-defined vocabulary
  (`ProcessStep.function` stays an open string by decision, ADR-0009).
- Use `Literal` for a small, closed set of string/int options within one type
  (for example `PipingRealization.kind`).

## Mutable versus immutable data

- Prefer immutable values. Frozen dataclasses, tuples for fixed-length records,
  and functions that return new values over mutating inputs.
- Mutate deliberately and locally. Avoid hidden mutation of an argument a caller
  did not pass in to be mutated.
- Pydantic models are mutable by default only because the framework requires it
  for construction; treat a validated model as a value once built.

## Public versus private APIs

- A name without a leading underscore is public and may be imported by other
  modules and by users.
- A leading-underscore name is private to its module. Do not import another
  module's private names across a package boundary.
- Changing a public name is a public-API change; it needs a reason and a test
  update. Issue #106 preserved every public API exactly and pinned it with
  `tests/test_public_api.py`.

## Package-level re-exports

- A capability package exposes its public surface from its `__init__.py`
  (`from deepplant.model.process import ProcessStep, ...` plus `__all__`).
- Internal modules stay implementation detail; callers import the public name,
  not the internal path.
- Keep the re-export list intentional. It is a public contract, not a dumping
  ground.

## Dependency injection

Inject a dependency only when it is justified: a real boundary that must support
substitution, or a resource (a clock, a socket, a filesystem root) that must be
controlled in a test. Pass it explicitly as a parameter or constructor argument.
DeepPlant has no dependency-injection framework and does not need one.

## Side effects, resources, and cleanup

- Avoid hidden side effects. A function named `resolve_assets_dir` should not
  also start a server; a `project_*` function should not write to disk.
- Make side effects visible in the name and the signature (`load_plant`,
  `save_plant`, `serve_editor`).
- Own what you open. Use `with` for files and sockets so cleanup is deterministic.
  The editor transport binds and releases its loopback socket explicitly and
  stops the thread it started.
- Do not leave a global mutable that a later call depends on; the FastAPI
  transport is an explicit factory rather than module-level state for exactly
  this reason.

## Circular imports

- Keep imports acyclic. The layering in
  [architecture.md](architecture.md#preferred-direction) makes this natural.
- If two modules seem to need each other, the responsibility split is wrong, or a
  shared piece belongs in a lower module. Do not "solve" it with a lazy import
  unless a genuine optional-dependency boundary requires it (the Qt package is
  imported lazily behind a dependency probe).

## Naming

- Follow PEP 8 and the existing codebase: `snake_case` functions/modules,
  `PascalCase` classes, `UPPER_SNAKE` module constants.
- Name for the engineering concept, not the implementation: `ProcessStream`, not
  `Link2`; `find_duplicate_ids`, not `dedupe`.
- A boolean reads as a predicate (`projectable`, `is_valid`), not `flag`.
- Domain-specific terms keep their domain spelling (`nominal_diameter`, not `nd`).

## Documentation and comments

- Every module has a docstring stating its responsibility and any boundary it
  owns. Public functions and classes document their contract: what they return,
  what they raise, and any invariant a caller must respect.
- Comment **why**, not **what**. The code says what; a comment earns its place by
  explaining a non-obvious decision, a workaround, a boundary, or a constraint.
- Do not leave stale comments or docstrings. When behavior changes, its
  documentation changes in the same change.
- Engineering documentation (equations, units, assumptions) is governed by
  [scientific-computation.md](scientific-computation.md).

## Pydantic boundaries

Pydantic v2 is a genuine part of DeepPlant, not decoration. Use it deliberately
and keep the following roles distinct:

| Role | Shape | Example |
|---|---|---|
| Semantic domain model | Pydantic `BaseModel` | `PlantModel`, `ProcessStep`, `PipingModel` |
| Internal Python data structures | dataclass / plain object | `EditorProjectionView` (frozen dataclass) |
| External validation | Pydantic, at the boundary | `PlantModel.model_validate(document)` in `io.py` |
| YAML serialization | `model_dump` / `model_validate` | `io.load_plant`, `io.save_plant` (ADR-0004) |
| HTTP request/response DTOs | explicit dict built from the domain | `EditorProjectionView.to_envelope()` |
| Configuration models | Pydantic, when a config needs validation | (add one only when a config exists) |

Rules:

- **Pydantic is justified where runtime validation or serialization is needed.**
  The semantic model is validated because authored YAML is untrusted input
  (ADR-0004). That is a real reason.
- **Do not mandate `BaseModel` for all internal objects.** A small internal value
  is a frozen dataclass; a transport-neutral result is a plain object.
- **Do not rewrite existing Pydantic semantic models to satisfy an aesthetic
  preference.** They are the implemented architecture; leave them unless a
  concrete defect justifies a change.
- **`extra="forbid"` on semantic models.** Authored input must fail on unknown
  fields instead of silently discarding them.
- **Validate at the boundary, not everywhere.** YAML and adapter XML are
  validated on the way in; internal functions may then trust their inputs.
- **YAML is a serialization representation, not the semantic source of truth**
  (ADR-0004). Serialization is canonical and deterministic (declaration order,
  `exclude_none=True`), and a round trip is semantically equal, not textually
  identical.

## Ruff rule review

The Ruff configuration is:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

`E`/`F` are core correctness, `I` is import order, `UP` is pyupgrade (modern
syntax), and `B` is bugbear (real bug patterns). Issue #107 performed an
evidence-based review of the candidate families `SIM`, `C4`, `PT`, and `RUF` by
running each against the current tree (`uv run ruff check . --select <family>`).
All four were **deferred**. The decision is recorded here so it has one
authoritative home.

| Family | Findings on the current tree | Decision | Reason |
|---|---:|---|---|
| `SIM` | 6 | Defer | Mostly subjective simplifications; two are `tools/` environment-variable casing, outside #107's scope; activating would force unrelated edits. |
| `C4` | 3 | Defer | Three low-value dict-comprehension rewrites, one under `tools/`; no defect caught. |
| `PT` | 10 | Defer | Test-style preferences (`@pytest.fixture` parenthesis, assertion splitting, `pytest.raises` style); stylistic, not correctness, and would churn tests. |
| `RUF` | 26 | Defer | Mixed: `RUF001` flags a meaningful en-dash / Greek `α` in user-facing and engineering text (a false positive here), plus stale `noqa` directives and test-regex style; several touch unrelated code. |

Justification for keeping the current set:

- **A small, high-value rule set beats enabling everything.** The existing five
  families already catch the real defects (`E`, `F`, `B`) plus format hygiene.
- **No new rules were enabled**, so no incidental production, test, or `tools/`
  refactor was introduced. Issue #107 is not a codebase-wide cleanup.
- **No blanket ignores were added**, and no useful existing check was disabled.
- **Ruff formatting stays deterministic** (`line-length = 100`, `py312`); nothing
  about that changed.

A future Issue may revisit these families if the codebase changes or if a
specific rule is shown to catch a real defect that justifies the cost. Any such
change makes only its necessary, low-risk compliance edits and keeps the config
central.

## Related

- [index.md](index.md) — the contract home, review checklist, and size policy.
- [architecture.md](architecture.md) — dependency direction and Pythonic SOLID.
- [typing.md](typing.md) — the strict typing rules.
- [quality.md](../workflow/quality.md) — the gates that run Ruff and Pyright.
