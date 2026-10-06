---
type: navigation
status: active
canonical_for:
  - python-engineering-contract-navigation
  - python-review-checklist
  - python-size-cohesion-policy
read_when:
  - python-change
  - python-review
  - implement-change
  - review-change
update_when:
  - python-engineering-contract-change
depends_on:
  - docs/dev/architecture/index.md
  - docs/dev/workflow/quality.md
  - docs/dev/workflow/conventions.md
decision:
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0004-yaml-is-a-serialization-format.md
evidence: []
superseded_by: null
---

# Python Engineering Contract

> **Question this document answers:** how must DeepPlant Python code be
> architected, designed, typed, validated, documented, and tested so that quality
> does not depend on individual judgment, and so both humans and coding agents
> apply one consistent standard?

This is the canonical, repository-owned Python engineering contract for
`src/deepplant/` (the semantic Core, its adapters and hosts) and `tests/`. It is
developer-owned governance, not a product feature, and it is tool-neutral: it
must be usable from any agent harness and by a human.

It builds directly on the architecture established by Issue #106 (capability
packages) and the ADRs that own each boundary. It defines the **contract**; the
mechanically checkable subset of its size and architecture rules is enforced
later by [Issue #108](https://github.com/Semtexcz/DeepPlant/issues/108).

## Status vocabulary

| State | Meaning |
|---|---|
| **Implemented** | Already true or already enforced in the repository today. |
| **Canonical rule** | Required for new or changed Python code. |
| **Deferred** | Direction decided here, applied by a later Issue. |

Where a rule is already proven by a check, the rule names the check. Where a rule
is a review expectation not yet automated, it says so explicitly; it is never
described as "enforced by CI" unless a real gate enforces it.

## Topics

| Topic | Document |
|---|---|
| Dependency direction, capability packages, boundaries, module splitting, Pythonic SOLID | [architecture.md](architecture.md) |
| Idiomatic design, functions/classes, dataclasses/enums, public APIs, Pydantic boundaries, naming, Ruff rule review | [conventions.md](conventions.md) |
| Typing baseline, `Any`/`Unknown`, `Protocol`, narrowing, generics, identifiers and quantities | [typing.md](typing.md) |
| Error semantics across the Core, application, CLI, HTTP, and desktop boundaries | [errors.md](errors.md) |
| Engineering-computation documentation: equations, units, assumptions, invariants | [scientific-computation.md](scientific-computation.md) |
| Test organization, behavior tests, fixtures, parameterization, reference/numerical validation, determinism | [testing.md](testing.md) |
| Commands and the enforced gates | [quality.md](../workflow/quality.md) |

## Current vs canonical vs deferred

- **Implemented:** `src/deepplant/` is a capability-oriented Python package
  (`model/`, `render/`, `adapters/dexpi/`, `editor/`) delivered by Issue #106. The
  semantic model is Pydantic v2 (`model/`), YAML is a serialization boundary
  (`io.py`, ADR-0004), the editor separation is application
  (`editor/application.py`) → transport (`editor/api.py`) with the GUI-toolkit
  code confined to (`editor/desktop_qt/`), and the tests are grouped by capability
  (`tests/model/`, `tests/render/`, `tests/adapters/dexpi/`, `tests/editor/`).
  Ruff (`E`, `F`, `I`, `UP`, `B`), Pyright (strict), and pytest are already
  enforced by `make lint`, `make typecheck`, and `make test`.
- **Canonical rule:** everything in this document set is binding for new or
  changed Python code.
- **Deferred:** deterministic size/architecture enforcement (a checker, a Make
  target, and any new architectural CI gate) is owned by
  [Issue #108](https://github.com/Semtexcz/DeepPlant/issues/108). This contract
  defines the size policy and counting semantics so #108 can implement them
  without inventing policy.

## Python review checklist

Use this for any change under `src/deepplant/` or `tests/`. It is the single
canonical copy; the `python-engineering` skill points here rather than
duplicating it.

- Is the change as simple as the engineering problem allows, with no speculative
  abstraction?
- Is new code owned by a cohesive capability package rather than a generic bucket
  (`utils.py`, `helpers.py`, `common.py`, and the like)?
- Does every dependency arrow point toward the independently usable semantic
  core, never away from it?
- Are CLI, HTTP, and desktop entry points thin, with behavior living below them?
- Is framework-specific code (Typer, FastAPI, Qt) confined to its boundary?
- Are Pydantic models used only where runtime validation or serialization is
  genuinely needed, rather than for every internal object?
- Is the code strictly typed, with no unnecessary `Any`, no blanket suppression,
  and no primitive wrapped in a class without a real distinction?
- Do errors carry useful engineering context (element, value, unit, invariant)
  and avoid broad swallowing, redundant wrapping, and raw tracebacks for
  ordinary use?
- Are units, assumptions, validity ranges, and numerical method or tolerance
  documented where an engineering calculation is involved?
- Is engineering/numerical behavior validated against an independent reference
  or analytical value, with explicit tolerances, where such a reference exists?
- Do tests assert observable behavior rather than mirror the implementation?
- Are the module/function/class/test-module limits below respected (soft limits
  are review signals; hard limits are the enforcement thresholds)?
- Is every new dependency justified, or is a local helper or an existing
  dependency sufficient?
- Are SOLID principles applied pragmatically, using Python's idioms, without
  introducing unnecessary abstractions?
- Is documentation consistent with the code, with one authoritative home for
  each durable rule?

## Size and cohesion policy

Line count is a **review signal for cohesion**, never a goal in itself. The
purpose is to notice loss of cohesion; it is never to fragment cohesive code
into artificially small units.

| Scope | Soft limit | Hard limit |
|---|---:|---:|
| Production module | 250 logical LOC | 500 logical LOC |
| Function/method | 40 logical LOC | 80 logical LOC |
| Class | 150 logical LOC | 300 logical LOC |
| Test module | 400 logical LOC | 800 logical LOC |

- **Soft limits** are review signals. Crossing one prompts a reviewer to ask
  whether a genuinely independent responsibility should be extracted; it never
  fails a check.
- **Hard limits** are the intended enforcement thresholds. They are the level at
  which a mechanically checkable rule
  ([Issue #108](https://github.com/Semtexcz/DeepPlant/issues/108)) is expected to
  fail.
- **Cohesion beats line count.** Never split a cohesive unit merely to stay under
  a limit. One cohesive 240-logical-LOC module is better than three fragments
  that must be read together.
- **Exceptions are centralized, explicit, and justified.** If a hard limit is
  genuinely wrong for a class of file, the limit is changed centrally with
  recorded reasoning, not loosened with an inline suppression.
- **Generated, vendored, or schema material** may justify an explicit exclusion;
  a package `__init__.py` re-export surface is not a reason to raise the policy.

### Counting semantics (logical LOC)

[Issue #108](https://github.com/Semtexcz/DeepPlant/issues/108) implements the
deterministic checker. To avoid it inventing policy, **logical LOC** is defined
here precisely as:

- a source line that contains executable or declarative code, **excluding** blank
  lines and lines whose first non-whitespace characters begin a comment (`#`);
- **docstrings and string statements count** as lines of their defining scope
  (they are real, maintained source), except the module-level docstring, which is
  not attributed to any sized scope;
- a **decorator line** is attributed to the definition it decorates
  (function/method/class), not to the enclosing scope;
- a **file-level scope** (module) counts the whole file's logical LOC, including
  all nested definitions;
- a **function/method** counts only its own body, **excluding** the bodies of
  nested definitions (a nested function or class is measured in its own scope);
- a **class** counts its own body, **excluding** the bodies of its methods and of
  nested classes (each is measured in its own scope); a class's own body includes
  its non-method statements, class-body assignments, and annotations;
- the **test-module** scope applies the module rule to files under `tests/`.

Multi-line expressions count each physical line that carries code, consistent
with how a reviewer reads length. Continuation lines that still carry tokens are
part of the statement they belong to.

### Enforcement scope

The initial policy enforcement planned for #108 covers:

```text
src/deepplant/**/*.py  — production size rules
tests/**/*.py          — test-module policy
```

Repository developer tooling under `tools/**/*.py` is **outside** the initial
size guardrails. That does not exempt `tools/` from existing Ruff, Pyright, or
pytest quality checks; it only excludes it from the new size checker until a
later, separately justified decision. Issue #107 does not expand into a `tools/`
refactor.

### Current evidence

Measured against the repository at Issue #106:

- the largest production modules are `adapters/dexpi/importer.py` (490 physical
  lines), `render/layout.py` (480), and `render/symbols.py` (447), all below the
  500 hard limit, so the production limits are consistent with the current code;
- existing test modules `tests/adapters/dexpi/test_dexpi_adapter.py` (970),
  `tests/test_io.py` (911), and `tests/render/test_render.py` (838) exceed the
  proposed 800 hard test-module limit. This is recorded as **existing technical
  debt for #108**, not refactored here, because a test reorganization is outside
  Issue #107's scope. #108 decides whether to split those modules or record a
  centralized, justified exception.

## Ruff rule review

The Ruff baseline is unchanged by this contract:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

Issue #107 reviewed the candidate families `SIM`, `C4`, `PT`, and `RUF` against
the actual codebase. The evidence and decision are recorded in
[conventions.md](conventions.md#ruff-rule-review) so the decision has one
authoritative home. In summary, all four were **deferred**: each would require
unrelated production, test, or `tools/` changes (or impose subjective/noisy
policy) that #107 does not justify. No blanket ignores were added and no useful
existing check was disabled.

## Related

- [architecture.md](../architecture/index.md) — current technical shape and boundaries.
- [quality.md](../workflow/quality.md) — the quality gates this contract is part of.
- [conventions.md](conventions.md) — design, Pydantic boundaries, and the Ruff review.
- [frontend/index.md](../frontend/index.md) — the parallel frontend contract.
- [roadmap.md](../planning/roadmap.md) — current state and next direction.
