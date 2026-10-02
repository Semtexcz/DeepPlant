---
type: contract
status: active
canonical_for:
  - process-model-contract
read_when:
  - authoring-process-yaml
  - process-model-change
  - renderer-implementation
depends_on:
  - docs/contracts/yaml-format.md
  - docs/contracts/plant-model.md
  - docs/dev/architecture/index.md
decision:
  - docs/dev/decisions/ADR-0005-process-model-container.md
  - docs/dev/decisions/ADR-0006-process-model-root-integration.md
  - docs/dev/decisions/ADR-0009-separate-process-function-from-symbol-role.md
  - docs/dev/decisions/ADR-0012-process-step-single-classification-axis.md
evidence:
  - docs/process-fragment-prototype.md
  - docs/process-step-classification.md
  - docs/dexpi-process-spike.md
superseded_by: null
---

# Process Model Contract

> **Question this document answers:** which process objects exist, who owns the
> process graph, and which structural rules (S1–S4) must hold?
>
> Implemented in `src/deepplant/model.py`; authored shape in
> [yaml-format.md](yaml-format.md); the physical layer in
> [plant-model.md](plant-model.md); presentation symbol roles in
> [rendering.md](rendering.md) and [../dev/reference/svg-symbols.md](../dev/reference/svg-symbols.md).

## Scope

The process graph is a **separate semantic layer** from the physical layer
(ADR-0002, ADR-0003). This contract owns the process-domain objects, the process
container, and the S1–S4 validation boundary. It does not own:

- the physical/plant layer ([plant-model.md](plant-model.md));
- piping realization ([physical-piping.md](physical-piping.md));
- symbol roles, packs, layout, or any presentation concept (ADR-0009);
- any process ↔ physical mapping (unresolved; see below).

## Objects

```text
PlantModel
└── process: ProcessModel | None
    ├── steps: list[ProcessStep]
    │   └── ports: list[ProcessPort]
    └── streams: list[ProcessStream]
        └── source / target: ProcessRef(step, port)
```

| Object | Fields | Notes |
|---|---|---|
| `ProcessModel` | `steps=[]`, `streams=[]` | Owns one process graph; independently constructible and structurally valid without any physical object or YAML |
| `ProcessStep` | `id`, `function`, `name=None`, `ports=[]` | `function` is canonical engineering semantics: an open, non-empty string, never a symbol role, equipment class, or DEXPI class identifier |
| `ProcessPort` | `id` | Identity only; no direction, kind, or engineering data |
| `ProcessRef` | `step`, `port` | Resolves only inside the owning `ProcessModel`, never to `Equipment` or a physical `Port` |
| `ProcessStream` | `id`, `name=None`, `source`, `target` | Binary directed process edge; no flow, thermodynamic, composition, or physical-piping semantics |

## Structural rules (S1–S4)

| # | Rule |
|---|---|
| S1 | `ProcessStep.id` is unique within `ProcessModel.steps`, and `ProcessStream.id` is unique within `ProcessModel.streams`; step ids and stream ids are **separate namespaces**, so one string may name both a step and a stream |
| S2 | `ProcessPort.id` is unique within the owning `ProcessStep` |
| S3 | `ProcessRef` endpoints (`source`, `target`) resolve to an existing step and to a port owned by that step in the same `ProcessModel` |
| S4 | A stream's `source` and `target` endpoints must not be identical |

S1–S4 are the complete structural boundary: cycles (recycle), mixing, and
splitting are structurally legal, and no rule depends on `Equipment`, `Port`, or
`Connection`. No cross-layer consistency rule exists yet.

## Function semantics

1. `ProcessStep.function` is the **engineering process function** performed by
   the step, e.g. `source`, `sink`, `mixing`, `splitting_material`, `pumping`,
   `heat_exchange`. The vocabulary is open and DeepPlant-native; no enum,
   controlled list, or hierarchy is imposed, so a new function needs no model
   change.
2. `unspecified` is a legal value and means the function has not been determined
   yet. Semantic uncertainty is valid model content.
3. `ProcessStep` has exactly **one** classification axis (`function`) today: no
   generic second classification, property bag, or metadata field exists
   (ADR-0012).
4. A `ProcessStep` is not an `Equipment` and does not require one. Process ids
   and physical ids are separate namespaces; one may equal the other without
   implying a relationship.
5. Symbol/presentation roles are resolved at the rendering boundary by
   presentation policy or explicit per-step overrides and are never stored here
   (ADR-0009).

## Root integration (`PlantModel.process`)

- Field: `PlantModel.process: ProcessModel | None = None`.
- A missing `process` key and `process: null` load as no process model;
  `process: {}` loads as an explicitly present, empty `ProcessModel`.
- Zero or one `ProcessModel` per `PlantModel` is supported; multiple process
  models are not introduced.
- S1–S4 stay owned by `ProcessModel`; `PlantModel` does not duplicate or extend
  them.

## Authored shape

```yaml
process:
  steps:
    - id: PS-feed
      function: source
      name: Fresh Feed Boundary
      ports:
        - id: out_feed
    - id: PS-pump
      function: pumping
      ports:
        - id: suction
        - id: discharge
  streams:
    - id: S-001
      source:
        step: PS-feed
        port: out_feed
      target:
        step: PS-pump
        port: suction
```

Runnable example: `examples/realistic-process-fragment/plant.yaml` (seven steps,
seven streams, including recycle, mixing, and splitting).

## Deliberately not modelled

Process ↔ physical realization (`ProcessStep` ↔ `Equipment`,
`ProcessStream` ↔ piping realization, `ProcessPort` ↔ `Port`) is unresolved and
has no field. Qualified engineering quantities (value + unit), material or
energy stream data, a second step-classification axis, a step hierarchy, and a
process-stream numbering standard are all unimplemented. Each requires its own
evidence and Issue; ADR-0009, ADR-0011, and ADR-0012 record the unanswered
questions and their revisit conditions.

## Related

- [architecture.md](../dev/architecture/index.md) — boundary map.
- [plant-model.md](plant-model.md), [physical-piping.md](physical-piping.md),
  [yaml-format.md](yaml-format.md) — sibling contracts.
- [ADR-0005](../dev/decisions/ADR-0005-process-model-container.md),
  [ADR-0006](../dev/decisions/ADR-0006-process-model-root-integration.md),
  [ADR-0009](../dev/decisions/ADR-0009-separate-process-function-from-symbol-role.md),
  [ADR-0012](../dev/decisions/ADR-0012-process-step-single-classification-axis.md).
- [process-fragment-prototype.md](../process-fragment-prototype.md) — the
  evidence/prototype that validated these concepts.
