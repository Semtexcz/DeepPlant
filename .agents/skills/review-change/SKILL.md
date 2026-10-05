---
name: review-change
version: 1
purpose: Review the actual diff for correctness, risk, and readiness.
triggers: [review change, inspect diff, pre review, ready for review]
inputs:
  required:
    - requested_intent
reads:
  - AGENTS.md
  - .agents/context-map.yaml
  - project/brief.md
  - docs/dev/architecture/index.md
  - docs/dev/workflow/quality.md
  - docs/dev/workflow/index.md
commands:
  - git diff --stat
  - git diff
  - make validate-docs
  - make validate-agent-skills
outputs:
  - findings ordered by severity
  - residual risks and test gaps
  - readiness recommendation
approval_boundary:
  may_approve: false
stop_conditions:
  - requested intent is unclear
  - unsafe diff
  - failing checks
  - missing verification evidence
---

# Review Change

Inspect the diff itself before declaring readiness. Evaluate correctness against
the requested intent, architecture invariants, unnecessary complexity,
regressions, test coverage, documentation impact, security and risk
implications, and accidental unrelated changes.

Report findings before summaries or readiness statements. Review the actual
diff, correctness and risks, test coverage, and the verification evidence for the
current head/state. Do not run an unconditional `make check` merely because
review was invoked; the canonical broad local confidence gate is owned by
`verify-change`, and its result is reusable while the candidate state is
unchanged. Run that gate again only when no valid local confidence result exists
for the current candidate state, or when review or repair changed that state - in
which case run focused checks and then one new `make check` for the new final
candidate. Do not wait for or poll GitHub Actions, which are authoritative but run
asynchronously after the push. In managed projects, task acceptance criteria may
add context, but lifecycle transitions remain outside this core review skill.
