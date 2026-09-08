# AGENTS.md

## Required Start

Start by reading the durable project context:

```bash
sed -n '1,220p' project/brief.md
sed -n '1,220p' docs/architecture.md
sed -n '1,220p' docs/workflow.md
```


This project uses lightweight governance. There is no mandatory task state
machine for ordinary implementation work. Use the brief, architecture, workflow,
quality gates, and any relevant ADRs as the durable context.


## Architecture Rules

- Start from the current project type: `script`.
- Start from the current runtime level: `shared`.
- Start from the current governance mode: `lightweight`.
- Use the simplest architecture that satisfies the current requirement.
- Keep business rules independently testable from transport concerns.
- Introduce abstractions only when repetition, coupling, complexity, or an explicit requirement justifies them.
- Do not add databases, queues, caches, external services, authentication, Kubernetes, or production deployment unless a concrete requirement and ADR justify it.

## DeepPlant Architectural Constraints

The semantic engineering model is the product core.

- Do not introduce UI, persistence, network services or external integrations into the domain model.
- Domain objects must remain independently usable from Python and CLI.
- YAML is a serialization format, not the domain model.
- Rendering and presentation data must remain separate from engineering semantics.
- Prefer small vertical changes with executable tests.
- Do not build abstractions for hypothetical future features unless a current requirement justifies them.
- The directional roadmap provides product context, not implementation authorization. Implement only the currently scoped vertical slice.




## Standard Commands

```bash
make setup
make dev
make test
make lint
make typecheck
make check
make format
make validate-docs
make validate-agent-skills

```

## Approval Boundaries

- Ordinary reversible implementation work can proceed autonomously when it is already scoped and automated checks pass.
- Human approval is required for destructive or irreversible data operations, authentication or authorization boundaries, security-sensitive changes, secret handling, paid external services, production deployment, destructive schema migrations, major scope expansion, and infrastructure with significant operational or financial consequences.


## Workflow


Workflow mode is `pr`: agents must work on a non-`main` branch, commit their own
changes, push to `origin`, and open a ready pull request. Do not push directly
to `main`.


General reusable skills are in `.agents/skills/`. Codex adapter notes are in
`.codex/`. Capability skills, when selected by this profile, are under
`.agents/capabilities/skills/`.


Project-specific context is in `project/brief.md`, `docs/`, and ADRs under
`docs/decisions/`. Keep changes small, run `make check`, and update the brief or
ADRs when implementation teaches something durable.

## Roadmap Reconciliation

For every PR that changes implemented capabilities, architecture decisions,
examples, or milestone progress, roadmap reconciliation is part of Definition
of Done.

Before opening or finalizing the PR:

1. Re-read `docs/roadmap.md` against the actual repository state after the
   change.
2. Mark an item complete only if the PR actually delivers it.
3. Re-evaluate the next task from:
   - current implemented capabilities,
   - milestone goals,
   - unresolved evidence gaps,
   - existing realistic examples/prototypes,
   - accepted ADRs.
4. Do not mechanically promote the next existing backlog row.
5. Prefer the smallest evidence-producing next slice. In particular, prefer
   testing the semantic model against a realistic executable example before
   introducing new abstractions or presentation architecture.
6. Ensure these roadmap sections are mutually consistent:
   - Current Implementation Roadmap
   - Completed
   - Backlog (Suggested Order)
   - Milestones
   - Next Task
7. Search touched documentation for stale statements such as:
   `next task`, `not yet implemented`, `deferred`, `open decision`,
   `prerequisite`, and similar status wording.
8. If the PR genuinely does not affect roadmap state, explicitly verify that
   no roadmap update is required.

The final task report must include a short `Roadmap check` stating:

- what became complete,
- what is now the next task,
- why that next task follows from the current repository state.

