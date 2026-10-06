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
mechanically checkable subset of its size and import-boundary rules is enforced
by the repository-owned checker delivered by
[Issue #108](https://github.com/Semtexcz/DeepPlant/issues/108) and run as
`make architecture-check`.

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
- **Implemented:** deterministic size and import-boundary enforcement is the
  repository-owned checker `tools/architecture_check.py`, run as
  `make architecture-check` (part of `make check` and CI), delivered by
  [Issue #108](https://github.com/Semtexcz/DeepPlant/issues/108). The size policy
  and counting semantics below are its canonical definition; its exact scopes,
  thresholds, and exceptions policy are recorded under
  [Enforcement scope](#enforcement-scope). Not every statement of this contract is
  mechanically enforced.

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
- **Hard limits** are enforcement thresholds: `make architecture-check` fails on a
  hard violation. Soft limits never fail the gate.
- **Cohesion beats line count.** Never split a cohesive unit merely to stay under
  a limit. One cohesive 240-logical-LOC module is better than three fragments
  that must be read together.
- **Exceptions are centralized, explicit, and justified.** If a hard limit is
  genuinely wrong for a class of file, the limit is changed centrally with
  recorded reasoning, not loosened with an inline suppression.
- **Generated, vendored, or schema material** may justify an explicit exclusion;
  a package `__init__.py` re-export surface is not a reason to raise the policy.

### Counting semantics (logical LOC)

The deterministic checker (`tools/architecture_check.py`) and its regression tests
(`tests/test_architecture_check.py`) implement exactly this definition. **Logical
LOC** is defined here in terms of **Python lexical tokens**, not raw text, and is
computed with the standard library (`ast` and `tokenize`).

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
  no sized scope. Only a source line whose sole code-bearing content is that
  docstring is excluded, so executable code sharing a module-docstring line (for
  example a statement joined after its closing quotes with `;`) still counts as a
  code line.
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

`make architecture-check` runs `tools/architecture_check.py` over:

```text
src/deepplant/**/*.py  — production module, function/method, and class limits
tests/**/*.py          — test-module limit, plus the same function/method and
                         class limits
```

The **module** limit depends on the file kind (production module 250/500; test
module 400/800). The **function/method** and **class** limits apply to every
discovered file. Repository developer tooling under `tools/**/*.py` is **outside**
the size guardrails — that excludes it from this checker only; `tools/` remains
covered by Ruff, Pyright, and pytest.

Soft violations are reported as `WARNING` and never fail. Hard violations are
reported as `ERROR` and exit non-zero; a clean tree exits zero. Findings are sorted
and formatted deterministically, so the same tree always yields the same output.

The checker also protects the direction of dependencies by inspecting imports
(`ast`) in the framework-free layers. The following scopes must not import a
transport, CLI, GUI, or presentation layer:

```text
src/deepplant/model/    !-> FastAPI/Starlette/Uvicorn, Typer/Click, PySide6/PyQt,
                            deepplant.editor, deepplant.render, deepplant.io,
                            deepplant.adapters
src/deepplant/render/   !-> the same frameworks, deepplant.editor
src/deepplant/adapters/ !-> the same frameworks, deepplant.editor, deepplant.render
src/deepplant/io.py     !-> the same frameworks, deepplant.editor, deepplant.render,
                            deepplant.adapters
```

Both absolute imports (`import deepplant.editor.api`, `from deepplant.editor import api`)
and relative imports (`from ..render import svg`) are resolved, including imports
nested inside functions and classes. This is a **direct-import** structural check:
it does not prove runtime or transitive behaviour, so the broader dependency
principles here still need human review.

**Exceptions** are centralized in the checker's `SIZE_EXCEPTIONS` list — never
inline suppression comments — and each entry names its exact path and scope with a
written justification. The list is empty: ordinary production code passes every
hard limit without grandfathering. Only generated, vendored, or schema material
may add a narrowly justified entry.

```bash
make architecture-check   # also part of `make check` and the CI python-checks job
```

### Current evidence

Measured with the checker itself (`make architecture-check`) against the
repository after Issue #97, using the token-aware logical-LOC definition above
(module-level docstrings excluded). Limits: production module 500, test module 800,
function/method 80, class 300.

**Production modules** (hard 500): the largest are `render/layout.py` (439 logical
LOC), `adapters/dexpi/importer.py` (419), `render/symbols.py` (410),
`editor/desktop_qt/self_check.py` (393), and `render/svg.py` (297) — all below the
hard limit. Several exceed the 250 soft limit; those are cohesive review signals,
not failures, and are deliberately not split for line count alone.

**Test modules** (hard 800): the largest are `tests/test_io.py` (750 logical LOC),
`tests/adapters/dexpi/test_dexpi_adapter.py` (746), `tests/render/test_render.py`
(639), and `tests/test_roundtrip.py` (534) — all below the hard limit. No test
module requires splitting or an exemption.

**Classes** (soft 150 / hard 300). The rule above counts a class's complete body,
including its methods, so the class limit is genuinely measured. The largest
production classes are `editor/desktop_qt/runtime.py` `DesktopEditor` (149 logical
LOC), `editor/desktop_qt/window.py` `MainWindow` (122), and `editor/api.py`
`EditorServer` (122); the largest semantic-model classes are `model/plant.py`
`PlantModel` (74) and `model/process.py` `ProcessModel` (50). `DesktopEditor` is the
only production class near the 150 soft limit, so the class limits (150 / 300) are
kept unchanged.

**Functions/methods** (soft 40 / hard 80). The largest are
`editor/desktop.py` `run_desktop_editor` (75),
`adapters/dexpi/importer.py` `_collect_stream` (70),
`adapters/dexpi/importer.py` `import_dexpi_process_xml` (68), `render/svg.py`
`render_process_svg` (66), and `editor/desktop_qt/runtime.py` `run_host` (65). The
#108 refactor resolved the six over-limit functions the #107 review identified,
preserving their behaviour:

| Function | Before | After |
|---|---:|---:|
| `render/svg.py` `render_process_svg` | 211 | 66 |
| `editor/desktop_qt/self_check.py` `start_self_check` | 165 | 45 |
| `render/symbols.py` `parse_symbol_variant` | 119 | 21 |
| `render/layout.py` `place_steps_and_assign` | 99 | 30 |
| `render/layout.py` `compute_process_pfd_layout` | 92 | 49 |
| `editor/projection.py` `project_process_pfd` | 88 | 48 |

There are no hard violations and no size exceptions. Soft-limit findings remain
informative, non-blocking review signals across the repository.

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
