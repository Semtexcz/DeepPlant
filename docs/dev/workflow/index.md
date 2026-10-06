---
type: governance
status: active
canonical_for:
  - daily-change-loop
read_when:
  - implement-change
  - review-change
  - verify-change
update_when:
  - workflow-policy-change
depends_on: []
decision: []
evidence: []
superseded_by: null
---

# Workflow

Project type: `script`. Runtime level: `shared`.
Governance: `lightweight`. Workflow mode: `pr`.

DeepPlant is past the project-foundation state. Work proceeds as small vertical
changes toward the active product milestone. What exists today, and what each
document owns, is recorded in
[architecture.md](../architecture/index.md) (boundary map), the
[contracts](../../contracts/index.md) (current obligations), and
[roadmap.md](../planning/roadmap.md) (product milestones and the active outcome). Do not implement
capabilities ahead of the slice that authorizes them.

## Change Loop

Understand enough -> build the smallest useful vertical slice -> run focused
checks -> learn -> refine durable project knowledge.

Use executable guardrails before process gates:

```bash
make setup
make check     # the one canonical local confidence gate (run once before finalizing a PR)
make build     # release wheel/sdist (not part of `make check`)
```

While implementing, run only the focused checks for the changed surface
(documentation, Python/Core, frontend, desktop, or packaging - see
[quality.md](quality.md)). `make check` is the single broader local gate, run
once before finalizing the pull request. After the PR is pushed the
implementation session ends: do not wait for or poll GitHub Actions. CI is
authoritative where required but asynchronous; if it later fails, repair it in a
fresh focused session on the same branch/PR.

After that push, pull-request CI is change-aware: a repository-owned classifier
selects only the jobs the changed surface can justify, and one always-present
aggregate job (`ci-gate`) is the stable required result for branch protection.
`main` and `workflow_dispatch` always run the full matrix. The canonical routing
matrix is in [quality.md](quality.md#change-aware-ci).

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
- `docs/dev/architecture/index.md` for current technical shape
- `docs/dev/decisions/` for ADRs when decisions become durable
- `docs/dev/workflow/standards.md` for standards usage and symbol-provenance
  rules, when work touches standards material or distributed symbol assets

Ordinary reversible implementation work can proceed when it fits that context
and the canonical `make check` gate passes once before the PR is finalized.


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

After the PR is pushed the implementation session ends. Required GitHub Actions
CI is asynchronous and must not be waited for or polled from that session; a
later CI failure is repaired in a fresh focused session on the same branch/PR.


## Release and Post-Release

Local projects may stop at verified checks. Shared and production projects need
release notes, rollback notes, and post-release verification appropriate to
their runtime level.


