---
name: verify-change
version: 1
purpose: Select and run the relevant deterministic validation path for a change.
triggers: [verify change, run checks, validation path]
inputs:
  required:
    - change_summary
reads:
  - .agents/context-map.yaml
  - docs/dev/workflow/quality.md
  - docs/dev/workflow/index.md
  - Makefile
commands:
  - make validate-docs
  - make validate-agent-skills
  - make check
outputs:
  - validation plan
  - command results
  - residual unverified risks
approval_boundary:
  may_approve: false
stop_conditions:
  - change type cannot be determined
  - required validation command is unavailable
  - deterministic checks fail
---

# Verify Change

Use this skill to route a change to existing deterministic checks. Do not
duplicate validation logic inside the skill when a Make target or executable
guardrail already exists.

Choose focused checks first, then the one broader local confidence gate before
finalizing the pull request. Examples:

- Python/Core change: `make format-check`, `make lint`, `make typecheck`, then the impacted `make test` tests.
- Frontend change: `make frontend-lint`, `make frontend-typecheck`, `make frontend-test`.
- Documentation-only change: `make validate-docs`.
- Agent skill / context map change: `make validate-agent-skills`.
- Desktop change: `make typecheck-desktop`.
- Packaging change: `make package-editor` / `make verify-packaged-editor`.

Run `make check` exactly once as the broader confidence gate before finalizing
the PR - not after every edit and not repeatedly. Do not treat GitHub Actions
completion as part of this session: after the PR is pushed the session ends and
CI runs asynchronously; a later CI failure is repaired in a fresh focused session
on the same branch/PR.

Report commands run, results, and any risk that remains unverified.
