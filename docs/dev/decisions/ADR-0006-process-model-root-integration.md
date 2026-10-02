# ADR-0006: Integrate ProcessModel into the PlantModel Root

> Status: Accepted
> Date: 2026-09-08

## Context

ADR-0005 accepted C1: `ProcessModel` is the coherent process-domain submodel and
the S1–S4 validation boundary while `PlantModel` remains the overall semantic
aggregate. ADR-0005 deliberately deferred the final `PlantModel` field name and
optionality for one process model and the YAML/document/file shape. This
decision resolves those two points for the first loadable slice: how one
`ProcessModel` enters the root model and how the first YAML boundary serializes
it. It does not change the domain-ownership boundary, the S1–S4 rules, or the
physical/topology layer.

## Decision

`PlantModel` owns zero or one `ProcessModel` through a single optional
`process` field:

```python
class PlantModel(BaseModel):
    plant: Plant
    equipment: list[Equipment]
    connections: list[Connection]
    process: ProcessModel | None = None
```

The first YAML boundary mirrors the domain field: a `process` mapping at the
root of a plant document contains the process graph:

```yaml
process:
  steps: ...
  streams: ...
```

Recorded semantics:

- A missing `process` key is equivalent to `process: None`; it means no authored
  process model and keeps existing plant YAML backward compatible.
- `process: null` also loads as `None`.
- `process: {}` constructs an explicitly present, empty `ProcessModel`.
- Zero or one `ProcessModel` per `PlantModel` is supported for now; multiple
  process models are not introduced.
- `ProcessModel` remains independently constructible and structurally valid
  without a `PlantModel`, a physical layer, or YAML.
- S1–S4 remain owned by `ProcessModel`; `PlantModel` does not duplicate or
  extend that internal validation.
- Process and physical namespaces remain separate: a process id never implies an
  equipment id or vice versa.
- Nesting `process` under `PlantModel` implies no process↔physical mappings and
  no cross-layer consistency validation.

## Consequences

### Positive

- `load_plant()` returns a fully populated aggregate — `PlantModel` with an
  optional process graph — through the existing YAML → Pydantic boundary
  (ADR-0004).
- Existing YAML files without a `process` section continue to load unchanged.
- The process graph stays independently consumable, testable, and valid
  (ADR-0005), preserving process/physical independence.

### Negative

- The root model gains one optional semantic nesting level.
- Serialization (save/round-trip) for the new field is not yet implemented.

## Deferred

- YAML save / round-trip for the root model including the `process` section.
- Multiple process models, scenario-specific graphs, and operating-state
  overlays.
- Broader YAML document / file layout beyond the single root `process` section.
- Process↔Equipment, ProcessPort↔Port/Nozzle, and ProcessStream↔physical
  mappings and their cross-layer consistency validation.

## Revisit When

A concrete requirement needs multiple process graphs for one plant, requires
process validity to depend on physical realization, or needs YAML save/round-trip
semantics that conflict with the accepted shape.

## Related

- [ADR-0002-semantic-model-is-the-core.md](ADR-0002-semantic-model-is-the-core.md)
- [ADR-0004-yaml-is-a-serialization-format.md](ADR-0004-yaml-is-a-serialization-format.md)
- [ADR-0005-process-model-container.md](ADR-0005-process-model-container.md)
