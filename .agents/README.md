# Agent Layer

`.agents/` is the canonical, tool-neutral agent layer. Skills represent reusable
agent capabilities. Governance controls project-management process. These are
separate concerns.

## Responsibilities

- Core engineering skills live in `.agents/skills/*/SKILL.md` and are available
  in lightweight and managed projects.
- Managed lifecycle skills live in `.agents/managed/skills/*/SKILL.md` and are
  generated only when `governance=managed`.
- Capability skills live in `.agents/capabilities/skills/*/SKILL.md` and are
  generated only for profiles with the matching specialized workflow.
- Skill-local `agents/` metadata may pin model profiles and validator scripts.
- Skills describe judgment, inputs, reads, outputs, approval boundaries, and
  stop conditions. They do not rewrite task state.
- In managed projects, project state, task transitions, approvals, and dashboard
  sync are controlled by `tools/project.py`.
- Skill validation is controlled by `tools/agent.py`. Managed context commands
  and hooks are available only in managed projects.
- Tool-specific adapters such as `.codex/` only point back to these canonical
  skills.

## Skill Groups

Core skills:

- `orient-project`: build concise project orientation from durable context.
- `implement-change`: implement the smallest coherent requested change.
- `verify-change`: route changes to existing validation commands.
- `review-change`: review the actual diff before declaring readiness.
- `update-documentation`: decide and apply durable documentation updates.
- `create-adr`: create ADRs only for durable architectural decisions.
- `conventional-commit`: draft and validate one commit message when requested.
- `capture-learning`: convert repeated failures into executable guardrails,
  durable documentation, or agent instructions in that order.

Managed skills:

- `assess-project-state`
- `choose-next-task`
- `prepare-task`
- `complete-task`
- `reassess-project`

Capability skills:

- `change-api-contract` for full-stack OpenAPI/client workflows.
- `verify-production-artifact` for production runtime artifact checks.

Project skills (DeepPlant-specific):

- `python-engineering` for any change under `src/deepplant/` or `tests/`: the
  canonical DeepPlant Python engineering contract (dependency direction,
  capability-package ownership, idiomatic design, the Pydantic boundary, strict
  typing, error semantics, engineering-computation documentation, testing, and
  the size/cohesion policy). It routes to the durable rules in `docs/dev/python/`
  and does not restate them.
- `frontend-engineering` for any change under `apps/editor/`: the canonical
  Engineering Editor frontend contract (architecture, feature ownership, Vue
  conventions, composables, state ownership, effects/watchers, TypeScript,
  styling, accessibility, testing, size guardrails). It routes to the durable
  rules in `docs/dev/frontend/` and does not restate them.

## Context Map

`.agents/context-map.yaml` defines a small routing model. Its `always` list is
only the universal bootstrap/invariants; task files, project-type paths, and
changed-file patterns select the rest of the durable context. A selected skill
may add only the specific reads it needs, so the effective context stays small:

```text
task + changed files + selected skill -> small relevant context
```

Managed projects may add `project/state.yaml`, `project/index.md`,
`project/board.md`, and active task files. Core skills must not require those
managed files. Excludes block secrets, dependency directories, caches, and build
artifacts. Paths cannot traverse outside the project root and symlinks outside
the root are rejected.

The recommended loop is conceptual, not mandatory orchestration:

```text
orient when context is unclear
implement the scoped change
verify with deterministic checks
review the diff
update docs or record no documentation impact
capture learning only when repeated experience justifies a guardrail
```

## Hooks

Hooks are managed-governance guardrails. They are generated only when
`governance=managed`.

- `make agent-pre-task TASK=<id>` verifies readiness before implementation.
- `make agent-pre-review TASK=<id>` checks diff safety, skills, project checks,
  and review readiness.
- `make agent-post-task TASK=<id>` verifies a completed task and synchronized
  project state.

Hooks may call project CLI functions, but they must not approve A1/A2 work or
silently change task status.
