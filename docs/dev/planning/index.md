---
type: governance
status: active
canonical_for:
  - strategic-planning-governance
read_when:
  - feature-planning
  - roadmap-change
  - project-board-change
update_when:
  - planning-policy-change
depends_on: []
decision: []
evidence: []
superseded_by: null
---

# Strategic Planning

This document defines how DeepPlant's long-term direction is governed from the
vision down to pull requests:

```text
VISION.md
    ↓
docs/dev/planning/product.md
    ↓
docs/dev/planning/direction.md
    ↓
docs/dev/planning/roadmap.md
    ↓
GitHub Issues
    ↓
Pull Requests
```

The repository planning documents are sufficient to determine project
direction. **If the GitHub Project and repository planning documents disagree,
the repository planning documents are authoritative.** GitHub Issues remain
authoritative for the detailed scope of concrete executable work.

Each layer has one job:

| Layer | Job |
|---|---|
| [VISION.md](../../../VISION.md) | Long-term destination / thesis — where DeepPlant is going |
| [docs/dev/planning/product.md](product.md) | Product thesis, users, product target, and durable non-goals |
| [docs/dev/planning/direction.md](direction.md) | Long-term capability progression — product context, not authorization |
| [docs/dev/planning/roadmap.md](roadmap.md) | Canonical current operational priority, horizons, sequencing, and unresolved evidence gaps |
| [docs/dev/architecture/index.md](../architecture/index.md) | Boundary map — what exists and its module boundaries |
| [docs/contracts/index.md](../../contracts/index.md) | Current model, format, CLI, renderer, and adapter obligations |
| [docs/dev/workflow/conventions.md](../workflow/conventions.md) | Documentation authority, audience, metadata, atomicity, and linking rules |
| GitHub Issues | Detailed scope of concrete bounded work that is Ready to execute |
| Pull Requests | Implementation / review units |
| GitHub Project | Non-canonical visual/convenience projection of roadmap and Issue state |

The roadmap is not a large backlog. The GitHub Project is useful for visual
planning but does not create or prioritize work by itself.

## Operational Horizons and Direction

[roadmap.md](roadmap.md) is canonical for current operational priority and
sequencing: `Now`, `Next`, and explicit re-evaluation or evidence gates. It
changes when evidence changes—after a spike, an ADR, a completed slice, or a
discovered dependency—never on a schedule.

[direction.md](direction.md) is canonical for long-term capability progression
and unresolved future capability context. The roadmap is not a large
`Later`/`Exploration` backlog. A GitHub Project may visualize additional derived
groupings such as `Later` or `Exploration`, but those fields are not planning
authority and must not contain unique direction required by agents or
contributors.

## Issue Creation Rule

A GitHub Issue should normally be created **only when the work is bounded enough
to reasonably end in a PR, a concrete research conclusion, or another explicit
deliverable**.

Good Issue:

```text
Spike DEXPI Plant/P&ID mapping
```

because it has a bounded evidence question.

Premature Issue:

```text
Implement complete P&ID model
```

because the architecture is not yet known.

Capability state therefore moves through the repository-led pipeline:

```text
product/directional capability
    → roadmap priority or evidence gap
    → bounded Issue
    → evidence / Ready work
    → PR
```

Do not create Issues merely to populate a GitHub Project, to fill a Milestone,
or to look busy. Do not create retrospective Issues for already completed work
— Git history and the roadmap record it. If a capability is immature, retain it
as directional context or a roadmap evidence gap rather than inventing a
speculative Issue.

## Project Content

The `DeepPlant Roadmap` GitHub Project is a non-canonical visual planning
surface. It may project repository roadmap horizons and Issue state for
convenience, but agents and contributors must not need Project access to
determine current priority. Update it to match the repository when useful; do
not treat it as an independent planning authority.

## Milestone Meaning

A GitHub Milestone is an **active capability goal containing concrete executable
work**.

A Milestone is **not**:

```text
a long-term vision bucket
a roadmap category
a mandatory sequential phase
a container created in advance for every capability
```

Milestones exist only when a capability is active or close enough to execution
that concrete Issues/PRs will reasonably belong to it. They may overlap; the
roadmap, not the Milestone list, decides ordering. Distant capabilities do not
receive empty Milestones, and no arbitrary due dates are assigned.

## Planning Artifacts at a Glance

| Question | Answered by |
|---|---|
| Where is DeepPlant going? | `VISION.md` |
| What is the product target, users, and durable non-goals? | `docs/dev/planning/product.md` |
| What is the long-term capability progression? | `docs/dev/planning/direction.md` (product context, not authorization) |
| What exists today, and what must hold now? | `docs/contracts/`, `docs/dev/architecture/index.md` |
| What is the canonical current priority, horizon, sequencing, and evidence gap? | `docs/dev/planning/roadmap.md` |
| What shipped already? | `docs/dev/history/implementation-slices.md` |
| What is current operational priority and sequencing? | `docs/dev/planning/roadmap.md` — `Now`, `Next`, and explicit re-evaluation gates |
| What is long-term or immature capability context? | `docs/dev/planning/direction.md`; GitHub Project may visualize derived groupings but is non-canonical |
| Which concrete work is actually Ready and what is its detailed scope? | the relevant bounded GitHub Issue |
| What is the visual convenience projection? | GitHub Project (non-canonical) |
