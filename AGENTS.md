# AGENTS.md

## Required Start

Build the smallest relevant documentation context from the task, the files you
will change, and the selected skill — do not eagerly load the entire repository
documentation.

The machine-readable bootstrap context is the `always` list in
[.agents/context-map.yaml](.agents/context-map.yaml). Then select task files,
project-type paths, and change-pattern context from that map, and add only the
contract, ADR, evidence, or navigation page the task needs. For documentation
work, use [docs/index.md](docs/index.md) and
[docs/dev/index.md](docs/dev/index.md) as the routing maps; `docs/dev/index.md`
contains the task → context table.


This project uses lightweight governance. There is no mandatory task state
machine for ordinary implementation work. Load the brief, architecture, workflow,
quality gates, roadmap, and relevant ADRs only when the selected task, changed
files, or skill makes them relevant.


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
- The milestone roadmap provides product context, not implementation
  authorization. Implement only the currently scoped vertical slice.

## Strategic Planning

Repository planning is self-contained and milestone-driven. Read
`VISION.md` for the thesis, `docs/dev/planning/strategy.md` for the target user
and deliberate choices, `docs/dev/planning/product.md` for the MVP definition,
and `docs/dev/planning/roadmap.md` for the product milestones and the single
**active milestone**. Concrete executable scope comes from the relevant GitHub
Issue; planning governance (idea intake, triage, refinement, readiness, and
Issue selection) is in `docs/dev/planning/index.md`.

GitHub Project access is not required to determine priority. The
`roadmap.md` milestones are canonical for what DeepPlant is building toward;
`direction.md` is long-term capability progression (context, not
authorization). GitHub Project may visualize derived groupings but is a
non-canonical convenience projection; it must not contain unique direction
required by agents.

Before implementing substantial work:

1. read the relevant strategy, product, roadmap, architecture, and ADR context;
2. work toward the **active milestone**, from a concrete **Ready** Issue;
3. treat an idea or an open Issue as a candidate, not authorization — creating
   an Issue does not authorize implementation;
4. do not create speculative Issues, and do not promote an open Issue into the
   active milestone unilaterally; triage new ideas per
   `docs/dev/planning/index.md`.

Never merge automatically.

## Licensed Standards

DeepPlant references engineering standards by identifier and never redistributes
their restricted normative content. See `docs/dev/workflow/standards.md` (policy)
and ADR-0007.

- Do not commit restricted standards content or standards PDFs unless the
  applicable licence explicitly permits redistribution.
- Do not provide licensed ISO, IEC, ISA, or other restricted standards content
  to AI tools unless the applicable licence explicitly permits that use, or the
  operator has explicitly authorized a private local reference bundle for the
  task. Operator-authorized private engineering references — restricted standards
  material and company/project drawings alike — may be inspected only under the
  rules in `docs/dev/workflow/standards.md`; they must never be redistributed or
  committed, and an authorized inspection never produces a `human-verified`
  state.
- Agents may use openly licensed specifications (for example DEXPI under CC BY
  4.0, with attribution), project-authored summaries, and public material whose
  applicable terms explicitly permit AI use. For ISO, use only ISO Open Data or
  other material explicitly licensed for such use; public availability alone is
  not permission for AI ingestion.
- Reference standards by identifier and official source.
- Do not reproduce normative figures, tables, symbol artwork, or substantial
  standard text without verified permission.
- Do not claim standards compliance from visual similarity or secondary
  sources. Standards conformance that depends on restricted normative content
  requires explicit human verification against an authorized copy.
- Distributed symbol assets need explicit redistributable provenance before
  they enter the repository (see `docs/dev/workflow/standards.md`).

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

## Development Checks and CI

While implementing, run only the checks relevant to the changed surface. The
focused mapping is: documentation `->` `make validate-docs`; agent skills/context
map `->` `make validate-agent-skills`; Python/Core `->` `make format-check`,
`make lint`, `make typecheck`, then a targeted `uv run pytest <relevant test
paths>` selection; frontend `->` `make frontend-lint`, `make frontend-typecheck`,
`make frontend-test`; desktop `->` `make typecheck-desktop`; packaging
`->` `make package-editor` / `make verify-packaged-editor`. Do not run exhaustive
validation after every edit.

Focused iteration selects only the tests a change can affect. `make test` always
runs the complete Python suite, so it belongs to the one broader gate rather than
to per-edit iteration:

```text
focused iteration        -> targeted `uv run pytest <relevant test paths>`
broader local confidence -> `make check` -> includes the full `make test` suite
```

`make check` is the single broader local confidence gate. Run it **once** for the
final candidate repository state before finalizing the pull request - not after
every edit, and not once per skill. It is owned by the `verify-change` skill;
reuse its result while the candidate state is unchanged, and rerun only when no
valid result exists for the current candidate state or after review/repair changes
that state. It is a developer-confidence gate, not a release/distribution gate:
the production frontend build, browser E2E, packaging, and the wheel build are
deliberately outside it. Canonical detail is in
[docs/dev/workflow/quality.md](docs/dev/workflow/quality.md).

CI runs afterwards and is asynchronous. Pull-request CI is change-aware: a
repository-owned classifier selects only the jobs the changed surface justifies,
and one always-present aggregate job (`ci-gate`) is the stable required result;
`main` and `workflow_dispatch` always run the full matrix.

> After pushing/finalizing the PR, do not wait for or poll GitHub Actions. CI is
> authoritative where required but runs asynchronously. If it later fails, repair
> it in a fresh focused session on the same branch/PR.

## Approval Boundaries

- Ordinary reversible implementation work can proceed autonomously when it is already scoped and automated checks pass.
- Human approval is required for destructive or irreversible data operations, authentication or authorization boundaries, security-sensitive changes, secret handling, paid external services, production deployment, destructive schema migrations, major scope expansion, and infrastructure with significant operational or financial consequences.


## Workflow


Workflow mode is `pr`: agents must work on a non-`main` branch, commit their own
changes, push to `origin`, and open a ready pull request. Do not push directly
to `main`. After the PR is pushed the implementation session ends: do not wait
for or poll GitHub Actions (see Development Checks and CI).


General reusable skills are in `.agents/skills/`. Codex adapter notes are in
`.codex/`. Capability skills, when selected by this profile, are under
`.agents/capabilities/skills/`.


Project-specific context is in `project/brief.md`, `docs/`, and ADRs under
`docs/dev/decisions/`. Keep changes small, run `make check` once before
finalizing the PR, and update the brief or ADRs when implementation teaches
something durable.

## Milestone Reconciliation

Planning documents change when versioned canonical documentation genuinely
changes — not because an Issue completed. There is no mandatory re-evaluation and
no planning PR required to pick the next Issue; the next Issue is chosen during
ordinary refinement from the active milestone (`docs/dev/planning/index.md`).

When a PR genuinely changes product state:

1. Re-read `docs/dev/planning/roadmap.md` against the actual repository state
   after the change.
2. Advance or complete a milestone only when its **demonstrable outcome** moved —
   never merely because linked Issues merged.
3. Do not select or promote a successor milestone; that is a deliberate product
   decision recorded when it actually happens.
4. If canonical documents genuinely change (strategy, product, or roadmap), keep
   them mutually consistent and update `direction.md` only if long-term context
   changed.
5. If the PR genuinely does not change milestone state, say so explicitly instead
   of editing the roadmap.

The final task report must include a short `Milestone check` stating:

- what milestone outcome (if any) moved, and how it was demonstrated;
- what the active milestone is and what evidence would complete it;
- why no roadmap change was needed, if none was.

