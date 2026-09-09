---
type: planning
status: active
source_of_truth_for:
  - strategic-planning-governance
read_when:
  - feature-planning
  - roadmap-change
  - project-board-change
update_when:
  - planning-policy-change
---

# Strategic Planning

This document defines how DeepPlant's long-term direction is governed from the
vision down to pull requests:

```text
Vision
    ↓
Architecture
    ↓
Roadmap
    ↓
GitHub Project
    ↓
active Milestones
    ↓
Issues only when work becomes Ready
    ↓
Pull Requests
```

Each layer has one job:

| Layer | Job |
|---|---|
| [VISION.md](../VISION.md) | Long-term destination / thesis — where DeepPlant is going |
| [docs/architecture.md](architecture.md) | Current architecture and durable constraints — what exists and its boundaries |
| [docs/roadmap.md](roadmap.md) | Sequencing reasoning and evidence — why the work is ordered as it is |
| GitHub Project | Strategic capability map + operational horizon — visible portfolio state |
| GitHub Milestones | Active or near-active capability goals containing concrete work |
| GitHub Issues | Concrete bounded work that is Ready to execute |
| Pull Requests | Implementation / review units |

The governing principle:

> Long-term capabilities belong in the strategic Project. Concrete Issues are
> created just in time, when a bounded piece of work is ready to execute.

The Project is not a delivery calendar and the roadmap is not a backlog. Neither
creates Issues by itself.

## Horizons

The GitHub Project uses four strategic horizons:

| Horizon | Meaning |
|---|---|
| **Now** | Currently active or immediately executable. |
| **Next** | Evidence-backed likely follow-up work. |
| **Later** | Important capability, but implementation is premature to define. |
| **Exploration** | A hypothesis/domain requiring discovery before commitment. |

> Horizon is not a delivery-date commitment.

Horizons change when evidence changes — after a spike, an ADR, a completed
slice, or a discovered dependency — never on a schedule.

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

Capability state therefore moves through the pipeline:

```text
strategic capability
    → Project item
    → evidence
    → Ready
    → Issue
    → PR
```

Do not create Issues merely to populate the Project, to fill a Milestone, or to
look busy. Do not create retrospective Issues for already completed work — Git
history and the roadmap record it. If a capability is immature, use a Project
**draft item**, not an Issue.

## Project Content

The `DeepPlant Roadmap` GitHub Project is the visual strategic portfolio: every
major capability of the vision appears there at its current horizon.

Each Project item is normally a **draft item** describing a strategic
capability, not a GitHub Issue. An Issue enters the Project only when that
capability's concrete work is Ready, and then as one bounded row.

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
| What major capabilities are part of the vision? | `VISION.md` capability map + GitHub Project |
| What exists today? | `docs/architecture.md`, `docs/roadmap.md` (Completed) |
| What is Now / Next / Later / Exploration? | GitHub Project Horizon field |
| Which capabilities are active enough for Milestones? | current roadmap state + Milestone policy above |
| Which concrete work is actually Ready? | bounded Issues created just in time |
