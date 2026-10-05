---
name: implement-change
version: 1
purpose: Implement a requested change with the smallest coherent repository diff.
triggers: [implement change, make change, code task, implement task]
inputs:
  required:
    - requested_change
reads:
  - AGENTS.md
  - .agents/context-map.yaml
  - project/brief.md
  - docs/dev/architecture/index.md
  - docs/dev/workflow/index.md
  - docs/dev/workflow/quality.md
  - docs/dev/decisions/
commands:
  - make validate-docs
  - make validate-agent-skills
outputs:
  - scoped code or documentation change
  - verification results
approval_boundary:
  may_approve: false
stop_conditions:
  - requested change is ambiguous
  - scope requires higher approval
  - context map is invalid
  - focused checks fail
---

# Implement Change

Use durable project context first, then inspect only the files needed for the
requested change. In managed projects, include active-task context when it is
available, but do not make implementation depend on a task id.

Choose the smallest coherent implementation that preserves architecture
invariants. Prefer existing patterns and helpers over new abstractions.

Run only the focused checks for the changed surface while iterating (see
`docs/dev/workflow/quality.md`); do not run the broad local gate after every
edit.

Before finalizing the pull request, make sure the final candidate repository
state has passed the canonical broad local confidence gate. That gate is owned by
the `verify-change` skill (`make check`); route the final candidate through it
rather than mandating a second `make check` here when that verification has
already been performed for the same state. Then follow this repository's `pr`
workflow: push the branch and open a ready pull request. CI is required but
asynchronous: do not wait for or poll it from the implementation session. If CI
later fails, repair it in a fresh focused session on the same branch/PR. Do not
mutate task state from this skill.
