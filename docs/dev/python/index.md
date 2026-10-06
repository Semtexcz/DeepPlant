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
here in terms of **Python lexical tokens**, not raw text. The definition is
implementable with the standard library (`ast` and `tokenize`); the checker
itself belongs to #108.

- **Blank lines are excluded.** A line that carries no token (only whitespace or
  a newline) is not counted.
- **Genuine comment-only lines are excluded.** A line whose only token is a
  `COMMENT` is not counted. This must be decided from tokens, not from a textual
  test such as `line.strip().startswith("#")`, because `#` inside a string
  literal is string content, not a comment.
- **Code lines are counted.** Any line that contributes a non-comment token
  (name, number, keyword, operator, or string) is a logical line.
- **String and docstring content is counted** as part of the scope that defines
  it, including the interior source lines of a multi-line string. The single
  exception is the **module-level docstring**, which is excluded and attributed to
  no sized scope.
- **Decorators are counted consistently with the definition they decorate**
  (function, method, or class): a decorator's lines belong to the decorated
  definition, never to the enclosing scope.
- **Multi-line expressions are counted by the source lines they occupy.** Every
  physical line that still carries a token — including bracket/backslash
  continuations — counts once, matching how a reviewer reads length.
- **Scopes count their complete logical source content, and overlapping scopes
  are intentional.** A scope includes every nested definition it contains:
  - a **module** (and therefore a **test module**, which applies the module rule
    to files under `tests/`) counts the whole file's logical content, including
    all nested definitions, minus the module-level docstring;
  - a **class** counts its **complete** body, **including its methods and nested
    classes**;
  - a **function/method** counts its **complete** body, **including nested
    functions and classes**.
  Each nested definition (nested class, nested function, or method) is **also**
  measured independently against its own limit. Overlap is therefore expected: a
  method contributes to its own size, to its enclosing class's size, and to the
  module's size; a nested function contributes to its own size, to its enclosing
  function's size, and to the module's size.

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

Measured against the repository at Issue #106, using the token-aware logical-LOC
definition above (module-level docstrings excluded). The figures below are
measured with `ast`/`tokenize`; #108's checker is the authoritative
implementation and must reproduce them.

**Production modules** (hard limit 500): the largest are
`adapters/dexpi/importer.py` (419 logical LOC), `render/layout.py` (412), and
`render/symbols.py` (361) — all below the hard limit. (Their physical line counts
are 490 / 480 / 447; physical length is not the limit.) The production module
limit is consistent with the current code.

**Test modules** (hard limit 800): the largest are `tests/adapters/dexpi/test_dexpi_adapter.py`
(746 logical LOC), `tests/test_io.py` (750), and `tests/render/test_render.py`
(639) — **all below the 800 hard limit**. (Their physical line counts are
970 / 911 / 838; an earlier draft of this contract compared those *physical* line
counts against the *logical* limit and wrongly concluded the modules exceeded it.
They do not.) No test module requires splitting or an exemption.

**Classes** (soft 150 / hard 300). The rule above counts a class's complete body,
including its methods, so the class limit is genuinely measured. The largest
production classes are `editor/desktop_qt/runtime.py` `DesktopEditor` (130 logical
LOC), `editor/api.py` `EditorServer` (117), and `editor/desktop_qt/window.py`
`MainWindow` (86); the largest semantic-model classes are `model/plant.py`
`PlantModel` (74) and `model/process.py` `ProcessModel` (50). **No production
class approaches the 300 hard limit, and none even reaches the 150 soft limit.**
Decision: the class limits (150 / 300 logical LOC) are **kept unchanged** — they
are realistic with substantial headroom, so #108 needs no class exception.

**Functions/methods** (soft 40 / hard 80). Under the same complete-content rule,
the function/method limits are exceeded by several large module-level production
procedures — the largest are `render/svg.py` `render_process_svg` (211 logical
LOC), `editor/desktop_qt/self_check.py` `start_self_check` (165),
`render/symbols.py` `parse_symbol_variant` (119), `render/layout.py`
`place_steps_and_assign` (99), `render/layout.py` `compute_process_pfd_layout`
(92), and `editor/projection.py` `project_process_pfd` (88). The function/method
limits are **kept unchanged** by this contract; this is recorded as measured
evidence of the current repository state so #108 can see it rather than
re-derive it.

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
