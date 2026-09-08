# ADR-0005: Use ProcessModel as the Process-Graph Container

> Status: Accepted
> Date: 2026-09-08

## Context

The validated process fragment establishes an independently meaningful process
graph: `ProcessStep` owns `ProcessPort`; `ProcessStream` connects
`ProcessRef(step, port)` endpoints. The first hard structural rules are ids
unique within their owning collections (S1), step-local port ids (S2), endpoint
resolution (S3), and distinct source and target endpoints (S4).

The unresolved question is whether `PlantModel` owns process collections
directly or contains a dedicated semantic `ProcessModel`. This is a domain
ownership and validation-boundary decision. It does not decide YAML nesting,
file layout, or a separate repository-level document (ADR-0004).

## Options

- **C1 — `ProcessModel`:** a process-domain container owns steps and streams;
  `PlantModel` may contain one process model.
- **C2 — direct `PlantModel` ownership:** `PlantModel` owns process-step and
  process-stream collections alongside equipment and connections.

## Decision

Propose C1. `PlantModel` remains the overall semantic aggregate for one plant;
`ProcessModel` is its coherent process-domain submodel and the S1–S4
reference-validation boundary.

`ProcessModel` is independently constructible and structurally valid without
`Equipment`, current `Port`, `Connection`, or a physical realization. It owns
process-graph identity through the S1–S4 boundary. Step ids and stream ids live
in separate namespaces: a `ProcessStep` and a `ProcessStream` may use the same
string id. Process and physical ids are also separate namespaces, so a process
id may equal an equipment id unless a future cross-layer rule proves otherwise.

The structural rules this boundary defines are:

- **S1** — ids are unique within their owning collections: `ProcessStep.id`
  unique within `ProcessModel.steps`; `ProcessStream.id` unique within
  `ProcessModel.streams`. The two collections are separate namespaces.
- **S2** — `ProcessPort.id` is unique within the owning `ProcessStep`.
- **S3** — `ProcessRef` endpoints resolve within the `ProcessModel`.
- **S4** — source endpoint != target endpoint.

The first slice assumes zero or one `ProcessModel` per `PlantModel`; multiple
process models are not introduced.

## Consequences

### Positive

- The process graph validates and can be tested or consumed independently by a
  PFD renderer, a process exchange adapter, or a simulator transformation.
- `PlantModel` stays an aggregate root without becoming the validator for every
  internally coherent semantic graph.
- Explicit mixing, splitting, and boundary steps remain valid without matching
  `Equipment`, preserving process/physical independence.
- Future process↔physical mappings can be cross-layer relations without making
  either graph structurally depend on the other.

### Negative

- The root model gains one semantic nesting level and later needs deliberate
  serialization mapping.
- Cross-layer consistency validation will need a separately defined owner when
  mappings become real domain entities.

## Deferred

- Final `PlantModel` field name and optionality for one process model.
- YAML/document/file layout.
- Multiple process models, scenario-specific graphs, and operating-state
  overlays.
- Process↔Equipment, ProcessPort↔Nozzle/current `Port`, and
  ProcessStream↔physical-realization mappings.
- Physical piping, process-port roles, step-type rules, stream designations,
  rendering, DEXPI adapters, and simulator interfaces.

## Revisit When

A concrete requirement needs multiple process graphs for one plant, requires
process validity to depend on physical realization, or shows that a consumer
cannot work with the process submodel independently.

## Related

- [ADR-0002-semantic-model-is-the-core.md](ADR-0002-semantic-model-is-the-core.md)
- [ADR-0003-separate-semantic-and-presentation-models.md](ADR-0003-separate-semantic-and-presentation-models.md)
- [ADR-0004-yaml-is-a-serialization-format.md](ADR-0004-yaml-is-a-serialization-format.md)
- [../process-fragment-prototype.md](../process-fragment-prototype.md)
