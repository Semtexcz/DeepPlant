---
name: python-engineering
version: 1
purpose: Apply the canonical DeepPlant Python engineering contract to any change under src/deepplant/ or tests/.
triggers: [python change, core change, semantic model change, renderer change, adapter change, editor python change, cli change, python review, pytest change]
inputs:
  required:
    - python_change
reads:
  - AGENTS.md
  - docs/dev/python/index.md
  - docs/dev/python/architecture.md
  - docs/dev/workflow/quality.md
commands:
  - make format-check
  - make lint
  - make typecheck
  - make test
  - make architecture-check
  - make check
outputs:
  - scoped Python change that follows the contract
  - python verification results
approval_boundary:
  may_approve: false
stop_conditions:
  - change would place UI, persistence, network, or framework code in the semantic model
  - change would add a speculative abstraction, service/repository/factory layer, or generic framework without a current requirement
  - change requires a new dependency without justification
  - change crosses a hard size limit without a centralized, justified policy change
  - change exceeds the currently authorized Issue or roadmap scope
---

# Python Engineering

Use this skill for any change under `src/deepplant/` or `tests/`. The durable
rules live in `docs/dev/python/`; this skill routes to them and deliberately does
not restate them, so there is one canonical copy.

## Read first

1. `docs/dev/python/index.md` — the contract map, the status vocabulary
   (implemented / canonical rule / deferred), the review checklist, and the
   size/cohesion policy.
2. The one topic document the change touches: `architecture`, `conventions`,
   `typing`, `errors`, `scientific-computation`, or `testing`.
3. `docs/dev/python/architecture.md` for dependency direction and the
   capability-package boundaries.

## Non-negotiable boundaries

- The semantic model stays the independently usable core (ADR-0002); no CLI, YAML,
  rendering, HTTP, or GUI code enters it.
- Dependencies point toward the core: entry point → application → semantic core.
  Never the reverse.
- Framework code (Typer, FastAPI, Qt) stays in its boundary layer only.
- YAML is a serialization boundary, not the model (ADR-0004).
- Pydantic is used where runtime validation or serialization is genuinely needed,
  not for every internal object.

## Before review

Run the Python gates and report their results, then apply the review checklist in
`docs/dev/python/index.md`:

```bash
make format-check
make lint
make typecheck
make architecture-check
```

`make architecture-check` runs the repository-owned size/import-boundary checker
(`tools/architecture_check.py`, Issue #108). Hard-limit or forbidden-import
findings fail it; soft-limit notices are review signals, not failures. The
enforced scopes, thresholds, counting semantics, and exceptions policy are
canonical in `docs/dev/python/index.md`.

During iteration, run a focused `uv run pytest <relevant test paths>` selection
rather than the whole suite. `make test` (the full suite) and `make check` (the
single broad local confidence gate) are reserved for the final candidate state,
run once, per `AGENTS.md`.

## Scope

Apply this contract to all `src/deepplant/` and `tests/` work. The active Issue and
roadmap define what may be implemented.

The size/import-boundary checker owned by Issue #108 now exists: run
`make architecture-check` and keep new and changed code within the hard limits it
enforces. Do not absorb work from sibling, future, or unselected Issues.
