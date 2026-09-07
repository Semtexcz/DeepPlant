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

## Problem

Process plants are engineered through drawings and documents. The semantic
content — equipment, ports, connections, instruments, properties, and
relationships — is buried in symbols and coordinates, so engineering intent
cannot be queried, validated, diffed, or reused across tools. Engineering is
documented as graphics instead of expressed as data.

DeepPlant applies the **Engineering as Code** idea: engineering intent is an
explicit, versionable semantic model with tooling around it.

## Users

- Process and piping engineers who produce and review PFDs and P&IDs.
- Engineering organizations that need review, CI, and auditability for
  engineering deliverables.
- Integrators who exchange plant models with DEXPI, simulators, and engineering
  tools.

## Value

DeepPlant makes the semantic engineering model the durable product artifact:
engineers and tools read and write YAML, validation happens on the semantic
model, and drawings (PFD/P&ID) become derived views. This enables Git diffs,
automated checks, and eventual exchange with the DEXPI ecosystem.

## Hypotheses

- A small process fragment of roughly 20–50 engineering objects can be
  represented and validated today.
- A semantic-model-first representation, kept free of presentation data,
  supports PFD/P&ID rendering and DEXPI exchange without redesign.
- Engineers accept YAML-authored models when validation and review are fast and
  actionable.

## Long-Term Capability Vision

Not implemented yet; the order of work lives in [roadmap.md](roadmap.md):

- semantic plant model (`Plant`, `Equipment`, `Port`, `Connection`, ...)
- YAML serialization
- PFD / P&ID rendering
- interactive editor
- validation and engineering rules
- Git diff / CI workflows
- DEXPI import/export
- later integration with simulators and engineering tools

## Product Principles

- The semantic engineering model is the product core. CLI, GUI, renderers, and
  adapters depend on it.
- Semantic engineering data and presentation data (sheet, symbol, coordinates,
  geometry, routing, labels) stay strictly separate.
- YAML is a serialization format, not the domain model.
- Connectivity is expressed through generic `Component -> Ports -> Connections`
  relationships, not hard-coded equipment-to-equipment links.

## Long-Term Non-Goals

- Do not add databases, ORMs, web backends, or containers before a concrete
  requirement justifies them.
- Do not embed drawing coordinates or SVG concepts into core engineering
  objects.
- Do not let any consumer (renderer, adapter, agent) become the reason the
  domain model changes shape.
