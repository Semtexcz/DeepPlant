---
type: workflow
status: active
source_of_truth_for:
  - daily-change-loop
read_when:
  - implement-change
  - review-change
  - verify-change
update_when:
  - workflow-policy-change
---

# Workflow

Project type: `script`. Runtime level: `shared`.
Governance: `lightweight`. Workflow mode: `pr`.

DeepPlant is past the project-foundation state: the semantic domain model
(minimal `PlantModel`/`Plant`/`Equipment`, `Port` + `Connection` + reference
validation, and the standalone `ProcessModel` with `ProcessStep[]`/
`ProcessStream[]`), YAML load/save, the packaged `basic` process symbol pack,
the headless process renderer, and the narrow DEXPI 2.x Process adapter spike
are implemented (see [roadmap.md](roadmap.md) and
[dexpi-process-spike.md](dexpi-process-spike.md)). Work proceeds as small
vertical changes; the next step is deliberately reconsidered from the roadmap's
current evidence. Do not implement capabilities ahead of the roadmap slice that
authorizes them.

## Change Loop

Understand enough -> build the smallest useful vertical slice -> run checks ->
learn -> refine durable project knowledge.

Use executable guardrails before process gates:

```bash
make setup
make check
make build
```

`make check` is validation-only. It must not rewrite project files. Use
`make format` for formatting changes.


## Agent Skills

Skills are reusable agent capabilities, not a mandatory orchestration engine.
Use the skill that fits the situation.

Core skills are always generated:

- `orient-project`
- `implement-change`
- `verify-change`
- `review-change`
- `update-documentation`
- `create-adr`
- `conventional-commit`
- `capture-learning`

Lightweight projects use these skills with durable context only. Managed
projects use the same core skills and may add task context through managed
lifecycle commands.





`capture-learning` follows this escalation order:

```text
executable guardrail > durable documentation > agent instruction
```

Do not add textual rules when tests, validators, Make targets, or CI checks can
enforce the behavior.

## Governance


Lightweight governance has no mandatory task state machine, approval state,
generated board, milestone gate, or ready-for-development gate. Keep durable
context small:

- `project/brief.md` for problem, users, outcome, constraints, and first slice
- `docs/architecture.md` for current technical shape
- `docs/decisions/` for ADRs when decisions become durable

Ordinary reversible implementation work can proceed when it fits that context
and `make check` passes.


## Human Approval

Human approval is based on blast radius, irreversibility, security, cost, and
production risk.

Human approval is required for:

- destructive or irreversible data operations
- authentication or authorization boundary changes
- security-sensitive changes or secret handling
- paid external services
- production deployment
- destructive schema migrations
- major scope expansion
- infrastructure with significant operational or financial consequences

Normal reversible implementation work does not need human approval merely
because it adds a module, endpoint, internal refactor, tests, UI behavior, or
ordinary public behavior required by already-scoped work.



## Git Workflow


`pr` mode preserves the strict branch -> commit -> push -> pull request
workflow. Agents work on a non-`main` branch, commit their own changes, push to
`origin`, and open a ready pull request. Direct pushes to `main` are not part of
this workflow.


## Release and Post-Release

Local projects may stop at verified checks. Shared and production projects need
release notes, rollback notes, and post-release verification appropriate to
their runtime level.


