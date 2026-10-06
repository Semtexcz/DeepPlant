---
type: governance
status: active
canonical_for:
  - strategic-planning-governance
read_when:
  - feature-planning
  - roadmap-change
  - idea-triage
  - project-board-change
update_when:
  - planning-policy-change
depends_on:
  - docs/dev/planning/strategy.md
  - docs/dev/planning/roadmap.md
decision: []
evidence: []
superseded_by: null
---

# Strategic Planning

This document defines how DeepPlant moves from vision to delivered capability:

```text
VISION.md                              why DeepPlant exists
    ↓
docs/dev/planning/strategy.md          who it is for, and the deliberate choices
    ↓
docs/dev/planning/product.md           what the first MVP must do
    ↓
docs/dev/planning/roadmap.md           the product milestones we build toward
    ↓
GitHub Issues                          ideas and bounded, executable work
    ↓
Pull Requests                          delivered, verified capability
```

The repository planning documents are sufficient to determine direction. **If
the GitHub Project and repository planning documents disagree, the repository
planning documents are authoritative.** GitHub Issues remain authoritative for
the detailed scope of concrete executable work.

## Document ownership

Each document owns one durable responsibility; it is not duplicated elsewhere.

| Document | Canonical responsibility |
|---|---|
| [VISION.md](../../../VISION.md) | Vision, thesis, and fundamental principles |
| [strategy.md](strategy.md) | Target user, positioning, differentiation, trade-offs, hypotheses |
| [product.md](product.md) | Product definition, MVP scope, and user workflows |
| [roadmap.md](roadmap.md) | Product milestones, the active outcome, dependencies, evidence gaps |
| [direction.md](direction.md) | Future capability directions (context, not authorization) |
| [history/implementation-slices.md](../history/implementation-slices.md) | Delivered work and slice provenance |
| [history/gate-decisions.md](../history/gate-decisions.md) | Retired planning-gate decisions (historical) |
| [architecture.md](../architecture/index.md) | Boundary map — what exists and its module boundaries |
| [contracts/index.md](../../contracts/index.md) | Current model, format, CLI, renderer, and adapter obligations |
| GitHub Issues | Ideas and the detailed scope of concrete bounded work |
| GitHub Milestones | Meaningful product outcomes (see below) |
| ADRs ([decisions/](../decisions/index.md)) | Consequential architectural decisions |
| Pull Requests | Implementation and review units |

Planning governance (this document) is the rule set for how those documents and
GitHub artifacts interact.

## Milestones

A **product milestone** is an outcome an engineer can experience, not a bucket of
Issues. The [roadmap](roadmap.md) defines the milestones and selects exactly one
**active** milestone.

- An active milestone defines its outcome, user value, demonstrable success
  criteria, genuine dependencies, relevant Issues, and evidence gaps.
- A milestone is **not** complete merely because its linked Issues merged;
  completion requires the demonstrated outcome.
- A GitHub Milestone is a useful surface for grouping the Issues that serve an
  active outcome. It is **not** a long-term vision bucket, a mandatory sequential
  phase, or a container created in advance for every capability. Distant
  capabilities do not receive empty Milestones, and no arbitrary due dates are
  assigned.
- The roadmap, not the GitHub Milestone list, decides ordering.

## Idea-to-delivery workflow

```text
IDEA
  ↓
TRIAGE
  ├── Duplicate → reference the canonical issue
  ├── Not aligned → record the disposition and close
  ├── Relevant but deferred → BACKLOG
  ├── Unresolved evidence → RESEARCH
  └── Selected for the active milestone → REFINEMENT
                                            ↓
                                          READY
                                            ↓
                                       IN PROGRESS
                                            ↓
                                           PR
                                            ↓
                                          DONE
```

**Core rule:** creating an Issue does **not** authorize implementation. An open
Issue is a captured idea or a proposed piece of work, never a commitment.

### Idea

A newly captured idea may contain only:

- the problem or opportunity;
- the proposed capability;
- the user benefit;
- examples or references.

It must **not** require a full architectural proposal, implementation plan, or
acceptance criteria before it is recorded. Capturing an idea must be cheap.

### Triage

Triage is a lightweight decision, not a formal approval process. It evaluates:

1. Does it align with the product [strategy](strategy.md)?
2. Which user problem does it address?
3. Does a duplicate or overlapping issue already exist?
4. Does it contribute to an existing milestone?
5. Is discovery needed before implementation?
6. Does it challenge a current strategic assumption?

Possible dispositions:

- **Duplicate** — reference the canonical issue and close; do not maintain two.
- **Not aligned** — record the reason and close, so the disposition is
  explainable later.
- **Relevant but deferred** — add to the **backlog** (label `backlog`).
- **Unresolved evidence** — open a **research** item (label the type/category);
  an unanswered evidence question is not an implementation task.
- **Selected for the active milestone** — move to **refinement**.

### Backlog

A relevant but unselected idea remains available for later consideration.
Backlog placement means **neither rejection nor commitment**, and backlog order
does **not** automatically determine implementation priority.

### Refinement and Ready

An Issue becomes **implementation-ready** (label `ready`) when it has:

- a clear objective;
- a bounded scope;
- acceptance criteria;
- relevant dependencies and architectural constraints;
- test or verification expectations;
- a reason to implement it now.

Large ideas may be split into smaller vertical slices at this stage.

### In Progress and Done

A coding agent implements a selected Issue (label `in-progress`) through the
repository's normal workflow. Completion requires appropriate tests, review, CI,
and merged changes. The linked milestone advances only when its **outcome** is
demonstrably closer to completion — not when an Issue merges.

## Selecting the next Issue

Once a milestone is active, choose the next Issue by:

1. contribution to the active milestone;
2. user value;
3. genuine dependencies;
4. risk reduction;
5. scope and implementation cost;
6. available evidence.

Critical defects, security issues, and necessary technical maintenance may be
selected independently when justified. **No planning PR is required to pick the
next Issue.**

An agent must **not** automatically promote an arbitrary open Issue into the
active milestone. Promotion is a deliberate selection decision.

## When the strategy or roadmap changes

Change the canonical planning documents only when evidence materially changes the
plan: an accepted ADR, a completed slice that shifts a dependency, a disproved
hypothesis, or a newly discovered constraint. A strategy or roadmap pull request
is created when versioned canonical documentation genuinely changes — **not**
whenever a task completes.

Do not introduce calendar-based review schedules, deadlines, or mandatory
planning ceremonies. There is no re-evaluation gate triggered by a count of
completed Issues.

## GitHub artifacts

Use existing GitHub features; no mandatory project-management infrastructure.

- **GitHub Issues** — ideas, research, bugs, and executable tasks.
- **GitHub Milestones** — meaningful product outcomes where useful.
- **Labels** — lightweight classification and readiness.
- **Pull Requests** — implemented changes.
- **ADRs** — consequential architectural decisions.

Suggested minimal workflow labels:

```text
idea
backlog
ready
in-progress
```

Research, bugs, and technical maintenance may also use type/category labels.
Native open/closed issue state provides final disposition. Do not make `backlog`
and `ready` depend on multiple redundant fields, and do not require a GitHub
Project board or a custom state machine.

Configuring GitHub Milestones, labels, and Projects is a separate operational
action; this document defines the workflow, not a one-time setup step performed
by a planning change.

## Idea capture and implementation readiness

Capturing an idea and authorizing implementation are two distinct stages; the
[workflow above](#idea-to-delivery-workflow) keeps them apart.

**Idea capture.** Anyone may create an Issue to record a relevant idea,
opportunity, problem, or feature proposal. The Issue may be incomplete:
architecture, acceptance criteria, implementation boundaries, and milestone
assignment are **not** prerequisites for capture, and capture must stay
lightweight. Search for duplicates where practical, and reference the canonical
Issue instead of maintaining two. A captured Issue is a candidate only — it does
not authorize implementation.

**Implementation readiness.** Before implementation, a selected Issue must
undergo refinement ([Refinement and Ready](#refinement-and-ready) above).
Refinement defines the objective, bounded scope, acceptance criteria,
dependencies, architectural constraints, and verification expectations; the
`ready` label is assigned only when those are satisfied. An open Issue —
including one inside the active milestone — does **not** authorize implementation
until it is refined and Ready.

Do not create Issues merely to populate a GitHub Project or a Milestone, or to
look busy. Do not record retrospective Issues for already completed work — Git
history and the [slice history](../history/implementation-slices.md) record it.

## Project content

The `DeepPlant Roadmap` GitHub Project is a non-canonical visual planning
surface. It may project repository milestones and Issue state for convenience,
but agents and contributors must not need Project access to determine current
priority. Update it to match the repository when useful; do not treat it as an
independent planning authority.

## Planning artifacts at a glance

| Question | Answered by |
|---|---|
| Why is DeepPlant being built? | `VISION.md` |
| Who is it built for, and what are the deliberate choices? | [strategy.md](strategy.md) |
| What must the first MVP accomplish? | [product.md](product.md) |
| Which milestone are we pursuing, and how is it finished? | [roadmap.md](roadmap.md) |
| What is the long-term capability progression? | [direction.md](direction.md) (context, not authorization) |
| What exists today, and what must hold now? | [contracts/](../../contracts/index.md), [architecture.md](../architecture/index.md) |
| What shipped already? | [history/implementation-slices.md](../history/implementation-slices.md) |
| What happened when a new idea is submitted? | [Idea-to-delivery workflow](#idea-to-delivery-workflow) above |
| How is the next implementation Issue selected? | [Selecting the next Issue](#selecting-the-next-issue) above |
| Which concrete work is Ready, and what is its scope? | the relevant bounded GitHub Issue |

## Related

- [strategy.md](strategy.md) — strategy.
- [product.md](product.md) — product definition and MVP.
- [roadmap.md](roadmap.md) — milestones.
- [direction.md](direction.md) — long-term capability progression.
- [workflow/conventions.md](../workflow/conventions.md) — documentation authority
  and metadata rules.
- [decisions/index.md](../decisions/index.md) — architectural decisions.
