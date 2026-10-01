---
type: product
status: active
canonical_for:
  - product-vision
  - long-term-non-goals
read_when:
  - discovery
  - roadmap-change
update_when:
  - product-vision-change
depends_on: []
decision: []
evidence: []
superseded_by: null
---

# Product

The durable long-term thesis and capability map live in
[VISION.md](../VISION.md); this page is the product-level view of the same
direction. Planning governance is in [planning.md](planning.md).

## Vision — Engineering as Code

DeepPlant is the first product implementing the broader idea of **Engineering as
Code** for process plants:

> Engineering intent should exist as explicit, machine-readable, versionable
> semantic data rather than being trapped primarily inside drawings and
> documents.

The long-term destination is a canonical semantic representation of a process
plant from which multiple engineering views and workflows are derived — PFDs,
P&IDs, line lists, validation reports, simulation inputs, and exchange formats.
That destination is reached one small vertical slice at a time
([roadmap.md](roadmap.md)), with the capability progression in
[direction.md](direction.md).

```text
                     engineers
                         │
                         ▼
                 DeepPlant model
                         │
      ┌──────────┬───────┼─────────┬──────────┐
      ▼          ▼       ▼         ▼          ▼
   CLI/API    PFD/P&ID validation  AI       adapters
                         │                    │
                         ▼             ┌──────┼───────┐
                       Git/CI          ▼      ▼       ▼
                                    DEXPI simulators tools
```

The diagram is conceptual, not a mandated architecture. What is actually
implemented today is described under "Where DeepPlant Is Now".

## Problem

Process plants are engineered through drawings and documents. The semantic
content — equipment, ports, connections, instruments, properties, and
relationships — is buried in symbols and coordinates, so engineering intent
cannot be queried, validated, diffed, or reused across tools. Engineering is
documented as graphics instead of expressed as data.

DeepPlant applies the **Engineering as Code** idea: engineering intent is an
explicit, versionable semantic model with tooling around it.

## PFD and P&ID Are Views, Not the Product Core

DeepPlant is not fundamentally "a P&ID editor". PFD and P&ID are initial
high-value engineering views over a deeper semantic model:

```text
                  Semantic model
                  /            \
                PFD            P&ID
          higher abstraction   more detail
```

If an interactive editor is ever built, it edits the same semantic model through
either view. Detailed view-projection rules are deliberately not decided here.

## Semantic Model as the Authoritative Record of Managed Intent

The semantic engineering model is the durable core artifact and the
authoritative system of record for engineering intent and project state managed
by DeepPlant (see [VISION.md](../VISION.md)). Conceptually it feeds the
engineering deliverables — where DeepPlant owns the information — instead of
each deliverable being authored in isolation:

```text
semantic engineering model
          │
          ├── PFD
          ├── P&ID
          ├── line lists
          ├── validation
          ├── reports
          ├── simulation inputs
          └── exchange formats
```

External systems and evidence (vendor data, measurements, material databases,
standards/legislation, as-built surveys, COMOS / AVEVA data owned by another
organization) remain authoritative for the data they own and are reached
through explicit adapters, references, and provenance. DeepPlant is therefore
not the ultimate source of every engineering fact, but it is authoritative for
what it manages.

This does **not** claim every document will necessarily be generated
automatically. The principle is that semantic information should be reusable
instead of manually duplicated wherever practical. Presentation data stays
separate from engineering semantics.

## Workflow, Judgment, and Product Position

Three durable positions are stated in full in [VISION.md](../VISION.md) and are
deliberately not repeated here:

- **Git-native engineering workflow** — semantic diff, validation, engineering
  review, and CI over a versionable model. The versionable YAML model and the
  `validate` CLI exist today; the rest is target direction.
- **Human engineering judgment remains essential** — only deterministic
  constraints should be automated. Judgment, trade-offs, and design intent stay
  human responsibilities, and this document designs no rules engine.
- **Product position: a semantic and automation layer** — DeepPlant complements
  rather than replaces heterogeneous engineering tools. External ecosystems
  (DEXPI, COMOS, AVEVA, simulators, calculations) are adapters around the
  canonical model, and no external schema shape dictates that model.

## Users

- Process and piping engineers who produce and review PFDs and P&IDs.
- Engineering organizations that need review, CI, and auditability for
  engineering deliverables.
- Integrators who exchange plant models with DEXPI, simulators, and engineering
  tools.

Product hypothesis (not a validated market fact): DeepPlant may be especially
useful for individual engineers, freelancers, small engineering teams,
organizations that cannot justify expensive integrated engineering platforms,
and teams wanting automation around existing engineering tools. It may
complement rather than replace systems such as COMOS or AVEVA. No business model
is assumed by this document.

## Where DeepPlant Is Now

Current implementation facts are not repeated here. The boundary map is
[architecture.md](architecture.md); the current obligations are the
[contracts](contracts/index.md) (plant model, process model, physical piping,
YAML format, CLI, renderer, symbol pack, DEXPI Process adapter); the actionable
current and next state is [roadmap.md](roadmap.md).

## Hypotheses

Current working hypotheses, not validated facts:

- A small process fragment can be represented and validated as a semantic model;
  the near-term target is a real fragment of roughly 20–50 engineering objects.
- A semantic-model-first representation, kept free of presentation data,
  supports PFD/P&ID rendering and DEXPI exchange without redesign.
- Engineers accept YAML-authored models when validation and review are fast and
  actionable.
- The audiences and the complement-not-replace position under "Users" describe a
  real market need.

## Long-Term Capability Vision

The capability progression — the stages, their goals, their dependencies, and
the questions deliberately left open in each — is recorded in
[direction.md](direction.md). It is product context, not implementation
authorization: the [anti-roadmap](roadmap.md#anti-roadmap--what-must-not-be-implemented-prematurely)
still governs, and the actionable current/next state lives in
[roadmap.md](roadmap.md).

## Product Principles

- The semantic engineering model is the product core. CLI, GUI, renderers, and
  adapters depend on it.
- PFD and P&ID are engineering views over the model, not the fundamental data
  model.
- Semantic engineering data and presentation data (sheet, symbol, coordinates,
  geometry, routing, labels) stay strictly separate.
- YAML is a serialization format, not the domain model.
- Connectivity points toward generic `Component -> Ports -> Connections`
  relationships rather than hard-coded equipment-to-equipment links.
- External engineering ecosystems (DEXPI, COMOS, AVEVA, simulators) are
  reachable through adapters; external schema shape must not dictate the
  canonical model.
- Consumer-specific representation concerns must not leak into the semantic
  domain model. A genuine engineering concept discovered through DEXPI,
  simulation, or another integration may legitimately cause the domain model to
  evolve.

## Long-Term Non-Goals

- Do not add databases, ORMs, web backends, or containers before a concrete
  requirement justifies them.
- Do not embed drawing coordinates or SVG concepts into core engineering
  objects.
- The directional roadmap is product context, not implementation authorization;
  a future stage never justifies premature architecture (see the Anti-Roadmap in
  [roadmap.md](roadmap.md)).
- No automated safety approval is implied by any safety-related direction.
- No standards compliance is claimed beyond what is implemented and verified.

## Related

- [architecture.md](architecture.md) — boundary map of what exists, and the
  durable invariants.
- [contracts/index.md](contracts/index.md) — current model, format, CLI,
  renderer, and adapter obligations.
- [direction.md](direction.md) — long-term capability progression (product
  context, not authorization).
- [roadmap.md](roadmap.md) — current state, next direction, anti-roadmap.
- [workflow.md](workflow.md) — the daily change loop.
- [decisions/index.md](decisions/index.md) — architectural decisions.
- [VISION.md](../VISION.md) — the durable long-term thesis and capability map.
