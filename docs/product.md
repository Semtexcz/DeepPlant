---
type: product
status: draft
source_of_truth_for:
  - product-vision
  - long-term-non-goals
read_when:
  - discovery
  - roadmap-change
update_when:
  - product-vision-change
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
([roadmap.md](roadmap.md)).

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

## Git-Native Engineering Workflow

DeepPlant should enable engineering workflows analogous to modern software
development:

```text
change
  ↓
semantic diff
  ↓
validation
  ↓
engineering review
  ↓
CI checks
  ↓
approved version
```

Intended benefits: traceability, reviewability, reproducibility, automated
consistency checks, and collaboration between engineers and agents. Today the
versionable YAML model and the `validate` CLI exist; the rest is target
direction.

## Human Engineering Judgment Remains Essential

DeepPlant is not intended to replace engineering judgment. A useful future
hierarchy of constraints is:

1. physical laws
2. legislation and mandatory standards
3. organizational / company rules
4. project configuration
5. engineering judgment

Hard deterministic constraints should increasingly be machine-checkable.
Judgment, trade-offs, and design intent remain human responsibilities. This
document designs no rules engine; rules appear only as a directional roadmap
stage.

## Product Position — a Semantic and Automation Layer

DeepPlant should not necessarily replace every engineering tool. A major value
proposition may be acting as a semantic and automation layer across
heterogeneous engineering tools:

```text
                    DeepPlant
               canonical plant model
                       │
       ┌────────┬──────┼───────┬────────────┐
       ▼        ▼      ▼       ▼            ▼
     DEXPI    COMOS  AVEVA  simulators  calculations
                                     
                       │
                       ▼
             other engineering systems
```

This is analogous in spirit to control-plane approaches such as Infrastructure
as Code, without claiming identical architecture. External ecosystems are
adapters around the canonical model. Consumer-specific representation concerns
must not leak into the semantic domain model; a genuine engineering concept
discovered through DEXPI, simulation, or another integration may legitimately
cause the domain model to evolve, but an external schema shape alone must not
dictate the canonical model.

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

Implemented today:

- `Plant` and `Equipment` objects with strict, non-empty semantic ids.
- Equipment owns `Port` objects. Port identity is local to the owning
  equipment/component; the same port id may exist on different equipment.
- `Connection` is a **directed semantic topological relationship** between two
  `PortRef` endpoints, from `source` to `target`.
- A `PortRef` resolves by `(component id, port id)`, and reference validation
  rejects unknown components and unknown ports.
- strict YAML loading into typed Pydantic models and the `deepplant validate`
  CLI on a runnable example.

This does **not** yet define process streams, pipes, signals, physical lines,
or nozzles. `Connection` remains topology only; what should represent process
piping / streams in the canonical model is the next open modeling question.
See [architecture.md](architecture.md) for the current technical shape and
[roadmap.md](roadmap.md) for what is next.

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

The initial semantic core is implemented: `Plant`, `Equipment`, equipment-owned
`Port` objects, `PortRef` endpoints, directed `Connection` edges, and reference
validation. This is not yet the complete canonical plant model — process
streams, pipes / pipelines, nozzle semantics, and instrumentation topology
remain unresolved. The open pipes/process-stream representation question is the
next modeling decision. The remaining order of work lives in
[roadmap.md](roadmap.md):

- pipes / process-stream representation (open modeling question)
- YAML save / round-trip serialization
- PFD / P&ID rendering
- interactive editor
- validation and engineering rules
- Git diff / CI workflows
- DEXPI import/export
- later integration with simulators and engineering tools

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

- [architecture.md](architecture.md) — current architecture and directional
  architecture invariants.
- [roadmap.md](roadmap.md) — current implementation roadmap, directional
  capability roadmap, and anti-roadmap.
- [workflow.md](workflow.md) — the daily change loop.
- [decisions/index.md](decisions/index.md) — architectural decisions.
