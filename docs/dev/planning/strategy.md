---
type: strategy
status: active
canonical_for:
  - product-strategy
read_when:
  - discovery
  - feature-planning
  - roadmap-change
  - idea-triage
update_when:
  - strategy-change
depends_on:
  - VISION.md
  - docs/dev/planning/product.md
decision:
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
evidence: []
superseded_by: null
---

# Strategy

> **Question this document answers:** why is DeepPlant worth building, who is it
> built for first, what deliberate choices and trade-offs define it, and which
> of those statements are established decisions versus unvalidated hypotheses?

The durable thesis and destination live in [VISION.md](../../../VISION.md). This
page is the strategy layer between that thesis and the concrete product
definition in [product.md](product.md): it decides **which target user, problem,
value, differentiation, and trade-offs** the product is optimized for, so that
milestones and Issues pursue a coherent outcome instead of an accumulating
feature catalog. Planning governance is in [planning.md](index.md).

This document selects no framework, adds no capability, and authorizes no
implementation. It records strategy; the [roadmap](roadmap.md) and the relevant
GitHub Issue authorize work.

## Established vs hypothesis

Two kinds of statement appear below and are labeled explicitly:

- **Established** — an accepted product, architecture, or repository decision
  already recorded elsewhere (an ADR, the vision, or a contract). It is a
  constraint on strategy, not a guess.
- **Hypothesis** — a working assumption not yet validated by real users or
  external evidence. Hypotheses are the assumptions the MVP exists to test; they
  must not be presented as facts.

No user research, market validation, or externally confirmed demand is claimed
anywhere in this document.

## Target user

**First target user (strategy decision, hypothesis about demand):**

> A process engineer (individually or in a small team) who owns a small process
> technology — a pilot, a scale-up, a research or early-design fragment — and who
> wants to express, edit, validate, and version that engineering intent as
> explicit semantic data rather than only as drawings and documents.

This user is deliberately narrower than the eventual audience. The strategy
optimizes the first MVP for a single capable engineer working locally on one
bounded process fragment, not for a large multi-discipline EPC organization.

Candidate segments this user is drawn from (all **hypotheses**, from the product
philosophy evidence — see [product.md](product.md#users) and Issue #77):

```text
independent / freelance process engineers
small engineering teams
process R&D and scale-up engineers
engineering researchers
engineers seeking programmable or open engineering tooling
```

**Established context (not a hypothesis):** the semantic engineering model is
the product core, and its consumers — CLI, GUI, renderers, adapters — depend on
it, never the reverse ([ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md)).
That constrains who the first tooling is built for: a user who benefits from an
explicit model, not one who only wants a faster drawing.

## Core user problem

**Established (thesis, from [VISION.md](../../../VISION.md)):** process
engineering intent is trapped inside drawings, documents, spreadsheets, and
tool-specific databases. As a result intent cannot be queried, validated,
diffed, reviewed, or reused across tools, and the same meaning is duplicated and
drifts.

**Strategy consequence:** the product must make engineering intent explicit and
editable as semantic data **while still offering the graphical views engineers
expect**. A tool that only produces a model, or only produces drawings, does not
solve the problem for this user.

## Value proposition

Working proposition (**hypothesis**, echoing the strategy issue):

> DeepPlant lets an engineer design, edit, validate, and automate a process
> technology through one open semantic model shared by a graphical editor, YAML,
> Python, and Git.

The proposition is only credible if the same underlying semantic state is
reachable from more than one surface without drift. That is why bidirectional
graphical/textual authoring and Git-native persistence are strategic, not
incidental features.

## Differentiation

Ordered by strategic priority for the first MVP. The ranking is a **strategy
decision**; the underlying claims are **hypotheses** until the MVP demonstrates
them.

| Priority | Differentiator | Why it matters for the target user | Status |
|---|---|---|---|
| 1 | **Engineering as Code** — intent is explicit semantic data, not only graphics | The whole value proposition rests on this | Established thesis |
| 2 | **Semantic-model-first, multi-surface authoring** — graphics and text are views of one model | Lets one engineer move between drawing and data without divergence | Hypothesis (MVP must prove it) |
| 3 | **Git-native projects** — reviewable, diffable engineering change | Fits how the target user already uses version control | Hypothesis |
| 4 | **Local-first, open-source Core** — usable without cloud, auth, or a database | Removes adoption friction for an individual/small team | Established constraint (ADR-0001, product non-goals) |
| 5 | **Open semantic model + Python API/CLI** — programmable and automatable | Enables automation and scale-up workflows | Established (contracts, CLI) |
| 6 | **Standards-based interoperability** (e.g. DEXPI) | Protects the user's data and eases exchange | Directional; only a narrow subset exists |
| 7 | **AI-assisted engineering over the same model** | Potential future leverage | Long-term direction, not MVP |

Deliberately **not** differentiators: being a full CAD replacement, a process
simulator, a COMOS/AVEVA replacement, or a cloud collaboration platform. DeepPlant
complements rather than replaces existing engineering tools
([VISION.md](../../../VISION.md)).

## Strategic priorities

1. **Prove the central thesis through one real vertical workflow.** A single
   engineer must be able to go from an empty project to a validated, persisted,
   Git-reviewable process fragment using both a graphical editor and YAML.
2. **Keep the semantic model authoritative and surface-neutral.** No surface may
   become a second source of engineering truth.
3. **Stay local-first and file-based.** No hosted service, account, or database
   is required for the MVP.
4. **Grow capability by bounded vertical slices.** Each milestone adds outcome,
   not breadth; the model grows only when a real consumer needs it.
5. **Preserve the engineering boundaries** (see below) at every step.

## Deliberate trade-offs

These are choices, not accidents:

- **Depth over breadth.** A small supported PFD and a minimal P&ID subset are
  chosen over broad but shallow coverage. Unsupported engineering semantics are
  refused by name rather than approximated.
- **One strong user over many weak ones.** The MVP targets a single local
  engineer rather than collaboration, multi-user editing, or organizational
  workflows.
- **Explicit data over convenience.** The user authors non-positional identity
  and real semantics; DeepPlant does not invent tag or line numbers to make a
  drawing look complete.
- **Local-first over cloud-first.** Simplicity and data ownership are preferred
  to reachability.
- **Separation over convenience coupling.** Semantic state, presentation state,
  and framework state stay separate even where collapsing them would be quicker.

## Non-goals

Strategy-level non-goals (durable product non-goals live in
[product.md](product.md#long-term-non-goals); these are the *strategic* ones):

- Being all things to all engineering disciplines before the first user workflow
  works for one.
- Competing as a CAD, simulation, or enterprise-suite replacement.
- Optimizing for organizational scale, real-time collaboration, or hosted
  multi-tenancy in the MVP.
- Claiming standards compliance or engineering completeness beyond what is
  implemented and verified.

## Assumptions requiring validation

Each is a **hypothesis** the MVP is intended to test, not a fact:

1. An engineer will accept a graphical editor whose graphics are a view of
   explicit semantic data rather than the source of truth.
2. Bidirectional graphical/YAML editing is genuinely useful and can be made
   understandable (no silent loss, clear unsaved and conflict states).
3. A small process fragment (roughly 20–50 engineering objects) is enough to be
   useful to the target user.
4. Locally persisted, Git-reviewable projects are an improvement over the user's
   current document-centric workflow.
5. The chosen target user (independent/small-team process engineer) experiences
   the stated problem strongly enough to adopt a new tool.

If an assumption is disproved by real evidence, that is a legitimate reason to
reconsider the strategy or milestone order (see [planning.md](index.md)).

## Preserved engineering boundaries

Strategy does not relax any accepted boundary:

```text
Process/PFD != Physical/P&ID != Simulation
ProcessStep != Equipment
ProcessPort != physical Port/Nozzle
ProcessStream != Connection/PipingLine

engineering semantics != presentation state
YAML serialization != semantic domain model
frontend framework state != canonical engineering state
```

These are established by [ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md),
[ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
[ADR-0004](../decisions/ADR-0004-yaml-is-a-serialization-format.md),
[ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md),
and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md),
and are invariants of every milestone.

## Related

- [VISION.md](../../../VISION.md) — the durable thesis and destination.
- [product.md](product.md) — product definition, MVP scope, and user workflows.
- [roadmap.md](roadmap.md) — the milestones that pursue this strategy.
- [index.md](index.md) — planning governance and the idea-to-delivery workflow.
- [direction.md](direction.md) — long-term capability progression (context, not
  authorization).
