---
type: guidance
status: active
canonical_for:
  - deepplant-overview
read_when:
  - start-work
  - understanding-deepplant
  - using-deepplant
update_when:
  - user-documentation-change
depends_on:
  - docs/contracts/yaml-format.md
  - docs/contracts/plant-model.md
  - docs/contracts/process-model.md
  - docs/contracts/physical-piping.md
  - docs/contracts/rendering.md
decision: []
evidence: []
superseded_by: null
---

# What Is DeepPlant?

> **Question this page answers:** what is DeepPlant, and what does "semantic
> model" mean in practice?

## In one paragraph

DeepPlant is a **Git-native semantic engineering platform** for process plants.
Engineering intent is kept as machine-readable **semantic data** instead of living
mainly inside drawings and documents. You author that intent as YAML, load it into
typed model objects, validate it, and derive views — such as a process diagram —
from it. Because the intent is plain text, Git can version and diff it like any
other code.

```text
authored YAML  →  validated semantic model  →  derived views (e.g. process SVG)
```

## Semantic model, drawing, and simulation model are different things

Three artefacts are easy to confuse; DeepPlant keeps them apart:

| Artefact | What it is | Where it lives |
|---|---|---|
| **Semantic model** | Engineering intent: equipment, ports, connections, process steps and streams, piping realization | Typed objects loaded from YAML — the product core |
| **Drawing** | A visual presentation derived from the model (symbols, layout, routing) | Generated output; never stored in the semantic model |
| **Simulation model** | Numerical/thermodynamic data for a solver | Not implemented |

A drawing is a **view**, not the source of truth. Changing how a diagram looks
never changes engineering meaning, and no symbol role, coordinate, or layout value
is stored in the model or in YAML.

## Three distinct semantic concerns today

DeepPlant keeps three concerns separate instead of merging them into one graph:

- **`PlantModel`** — physical plant topology: `Equipment`, `Port`, and identified
  `Connection`s between ports. A connection is adjacency only: not a pipe, not a
  flow, not a signal.
- **`ProcessModel`** — the process graph: `ProcessStep` (with its engineering
  `function`) and directed `ProcessStream`s between step ports.
- **`PipingModel`** — physical realization: piping lines and segments that
  reference existing connections, so adjacency is authored exactly once.

They share no cross-layer mapping yet, and ids in one layer imply nothing about
ids in another. Exact semantics live in the canonical contracts:
[plant-model.md](../../contracts/plant-model.md),
[process-model.md](../../contracts/process-model.md), and
[physical-piping.md](../../contracts/physical-piping.md).

## What you do with DeepPlant today

1. **Author** intent in YAML — authored shape:
   [yaml-format.md](../../contracts/yaml-format.md).
2. **Validate** structure and references with `deepplant validate` —
   [cli.md](../../contracts/cli.md).
3. **Render** a `ProcessModel` to a standalone SVG through the Python API —
   [rendering.md](../../contracts/rendering.md).

## Implemented today

- `PlantModel` / `Equipment` / `Port` / `Connection`
- `ProcessModel` / `ProcessStep` / `ProcessStream`
- `PipingModel` with lines, segments, and realizations
- YAML load and save into typed models
- the `deepplant validate` CLI
- a headless read-only renderer: `ProcessModel` → standalone SVG
- a narrow DEXPI 2.0.0 **Process** import/export adapter

## Not implemented yet

DeepPlant does **not** currently provide:

- an interactive editor
- a P&ID renderer
- full DEXPI support, or DEXPI Plant/P&ID import/export
- COMOS or AVEVA adapters
- an engineering-rule engine (DN continuity, line-number consistency, and similar
  checks)
- any process ↔ physical mapping

Those are direction, not shipped behaviour. Do not build expectations on them
yet.
