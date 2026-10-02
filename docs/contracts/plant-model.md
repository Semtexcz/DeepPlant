---
type: contract
status: active
canonical_for:
  - plant-model-contract
read_when:
  - authoring-plant-yaml
  - physical-model-change
  - validation-change
depends_on:
  - docs/contracts/yaml-format.md
  - docs/dev/architecture/index.md
decision:
  - docs/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md
  - docs/decisions/ADR-0011-canonical-physical-piping-realization.md
evidence:
  - docs/dexpi-plant-pid-spike.md
superseded_by: null
---

# Plant Model Contract

> **Question this document answers:** which physical/plant objects exist, what
> identifies them, and which structural and reference rules must hold?
>
> Implemented in `src/deepplant/model.py`; authored shape in
> [yaml-format.md](yaml-format.md); the process graph in
> [process-model.md](process-model.md); piping realization in
> [physical-piping.md](physical-piping.md).

## Scope

This contract owns the physical/topology layer of the canonical model: the root
aggregate, the equipment inventory, connection points, and directed adjacency.
It deliberately does **not** own:

- the process graph ([process-model.md](process-model.md));
- piping realization ([physical-piping.md](physical-piping.md));
- serialization mechanics ([yaml-format.md](yaml-format.md));
- presentation data, which never enters these models (ADR-0003).

## Objects

```text
PlantModel
├── plant: Plant
├── equipment: list[Equipment]
│   └── ports: list[Port]
├── connections: list[Connection]
│   └── source / target: PortRef(component, port)
├── piping: PipingModel | None      (see physical-piping.md)
└── process: ProcessModel | None    (see process-model.md)
```

| Object | Fields | Notes |
|---|---|---|
| `PlantModel` | `plant`, `equipment=[]`, `connections=[]`, `piping=None`, `process=None` | Root aggregate for one plant; `None` means the optional submodel is not authored, an explicitly present empty submodel is valid |
| `Plant` | `id`, `name=None` | `id` identifies the plant |
| `Equipment` | `id`, `type`, `name=None`, `ports=[]` | `type` is a required, open, non-empty string; no fixed equipment taxonomy exists |
| `Port` | `id` | A named connection point owned by exactly one equipment item |
| `PortRef` | `component`, `port` | Endpoint reference; `component` currently resolves only to `Equipment` |
| `Connection` | `id`, `source`, `target` | Required plant-unique `id` (C1); direction is recorded by `source`/`target` |

## Field and identity rules

1. **Semantic strings are non-empty.** Every `id`/`type`/reference field is a
   non-empty, non-whitespace string (leading/trailing whitespace is stripped
   before validation), so a typo cannot be stored as a blank semantic value.
2. **Unknown fields are rejected.** Every model forbids extra fields, so
   unsupported or misspelled engineering data fails instead of being silently
   discarded.
3. **Identity is authored, never positional.** `Connection.id`, `equipment.id`,
   and `port.id` come from the document. No id is generated from a list index.
4. **Namespaces are deliberate:**
   - `equipment.id` is unique within one `PlantModel`;
   - `port.id` is unique within the owning `Equipment` and local to it, so the
     same port id may exist on different equipment items;
   - `connection.id` is required, non-empty, and unique within one `PlantModel`
     (rule C1, ADR-0011);
   - process ids are a separate namespace ([process-model.md](process-model.md)).
5. **A globally resolvable endpoint is the pair `(component id, port id)`.**

## Reference rules

Every `Connection` endpoint must resolve inside the same `PlantModel`:

- `source.component` / `target.component` must name an existing `Equipment`;
- `source.port` / `target.port` must name a port owned by that equipment item.

Failures are reported deterministically as
`connections[<index>].<source|target>: unknown component '<id>'` or
`connections[<index>].<source|target>: component '<id>' has no port '<id>'`.

Reference validation enforces referential integrity only. It is not a
process-engineering topology check, and there is no generic `Component` base
class: `component` resolves to `Equipment` today (ADR-0010).

## Direction

`source` → `target` records the authored direction of the adjacency. It is
topology direction, not flow, and no simulation, stream, signal, or piping
meaning is attached to it.

## Authored shape

```yaml
plant:
  id: demo
  name: Minimal Process

equipment:
  - id: T-101
    type: tank
    name: Feed Tank
    ports:
      - id: outlet
  - id: P-101
    type: pump
    ports:
      - id: suction

connections:
  - id: C-001
    source:
      component: T-101
      port: outlet
    target:
      component: P-101
      port: suction
```

A runnable example is `examples/minimal-process/plant.yaml`.

## Deliberately not modelled here

Equipment taxonomy and tag-naming standards, `Nozzle`/`PipingNode` refinement,
valve/fitting component kinds, typed engineering quantities, insulation or
tracing data, instrumentation and signal semantics, and any presentation
(presentation symbol roles, coordinates, routing) or persistence concept.
Reasons and revisit conditions are recorded in ADR-0003, ADR-0010, and the
evidence documents they cite; none of these is authorized by their absence
here.

## Related

- [architecture.md](../dev/architecture/index.md) — boundary map and module layout.
- [process-model.md](process-model.md), [physical-piping.md](physical-piping.md),
  [yaml-format.md](yaml-format.md) — the sibling canonical contracts.
- [ADR-0010](../decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md),
  [ADR-0011](../decisions/ADR-0011-canonical-physical-piping-realization.md).
- [dexpi-plant-pid-spike.md](../dexpi-plant-pid-spike.md) — the evidence behind
  the `Port`/`Connection` boundary.
