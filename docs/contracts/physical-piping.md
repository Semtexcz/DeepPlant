---
type: contract
status: active
canonical_for:
  - physical-piping-contract
read_when:
  - authoring-piping-yaml
  - physical-model-growth
  - piping-model-work
depends_on:
  - docs/contracts/plant-model.md
  - docs/contracts/yaml-format.md
  - docs/dev/architecture/index.md
decision:
  - docs/dev/decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md
  - docs/dev/decisions/ADR-0011-canonical-physical-piping-realization.md
evidence:
  - docs/physical-piping-model.md
  - docs/dexpi-plant-pid-spike.md
superseded_by: null
---

# Physical Piping Contract

> **Question this document answers:** how is physical piping realized over
> identified connections, and which rules (C1, P1–P5) must hold?
>
> Implemented in `src/deepplant/model.py`; authored shape in
> [yaml-format.md](yaml-format.md); the topology it references in
> [plant-model.md](plant-model.md). Design rationale, rejected candidates, and
> worked diffs are evidence in
> [../physical-piping-model.md](../physical-piping-model.md).

## Invariants this layer preserves

```text
Connection   = directed, property-free physical adjacency between two Ports
Connection  != Pipe / piping segment / piping line / piping realization
Connection  != ProcessStream / Signal
ProcessStream != physical piping
ProcessPort  != Port (and != Nozzle)
```

Piping **references** identified connections and never restates endpoints, so
adjacency stays authored exactly once (ADR-0011, ADR-0010).

## Objects

```text
PlantModel
└── piping: PipingModel | None
    └── lines: list[PipingLine]
        ├── id, line_number?, name?
        └── segments: list[PipingSegment]
            ├── id, segment_number?
            ├── nominal_diameter?, piping_class?, fluid_code?
            └── realizations: list[PipingRealization]
                ├── connection: <Connection id>
                └── kind: "pipe" (default) | "direct"
```

| Object | Fields | Notes |
|---|---|---|
| `PipingModel` | `lines=[]` | Optional container on `PlantModel`; mirrors the `PlantModel.process` submodel precedent |
| `PipingLine` | `id`, `line_number=None`, `name=None`, `segments=[]` | `id` is canonical line identity; `line_number` is a human/external designation |
| `PipingSegment` | `id`, `segment_number=None`, `nominal_diameter=None`, `piping_class=None`, `fluid_code=None`, `realizations=[]` | `id` is canonical identity local to the owning line; the property strings are open, optional, and never canonical identity |
| `PipingRealization` | `connection`, `kind="pipe"` | A statement *about* an existing adjacency, not an edge with its own endpoints |

## Rules (C1, P1–P5)

| # | Rule |
|---|---|
| C1 | `Connection.id` is required, non-empty, and unique within the `PlantModel` |
| P1 | `PipingLine.id` is unique within `PipingModel.lines` |
| P2 | `PipingSegment.id` is unique within the owning `PipingLine` |
| P3 | every `PipingRealization.connection` resolves to a `Connection` of the same `PlantModel` |
| P4 | **first-slice invariant:** a `Connection` is referenced by at most one realization across the whole `PipingModel` |
| P5 | a segment has at least one realization (an empty property boundary is meaningless) |

C1 is a documented pre-1.0 breaking change to authored YAML: every authored
`Connection` needs a stable id. P4 is intentionally conservative and 1:1; it may
be relaxed only through later evidence and an ADR change.

**Validation ownership** (narrowest first): C1 required/non-empty is a field rule
on `Connection`; C1 uniqueness and P3 live on `PlantModel` (they need physical
context); P1 and P4 live on `PipingModel`; P2 on `PipingLine`; P5 on
`PipingSegment`. `PipingModel` is independently structurally valid for its local
rules (P1, P2, P4, P5), but it is not fully referentially validated in isolation:
P3 requires `PlantModel` context because realization `connection` references must
resolve against `PlantModel.connections`. `ProcessModel`, by contrast, owns and
resolves its independent semantic graph (S1–S4).

These are **structural and referential** rules only. DN continuity, reducer
requirements, piping-class continuity, line-number consistency, and
missing-realization reports are engineering-rule concerns for a future rule
engine and are deliberately not implemented.

## Field semantics

1. **`PipingModel` mirrors `PlantModel.process`.** It is optional: a plant with no
   authored piping stays valid.
2. **Piping is a dependent layer, not an independent graph.** Unlike
   `ProcessModel`, `PipingModel` is independently structurally valid for local
   rules (P1, P2, P4, P5), but P3 needs `PlantModel` context to resolve
   realization references against `PlantModel.connections`. This asymmetry is
   intentional.
3. **`PipingLine.id` is canonical identity.** `line_number` is the human
   designation (for example `3"-P-101-A1A`), follows company practice, may be
   revised, and is not guaranteed unique across a project. A DEXPI
   `PipingNetworkSystem` XML object id never becomes `PipingLine.id`.
4. **`PipingSegment.id` is canonical identity local to the owning line.**
   `segment_number` is an optional human/external designation (a DEXPI
   `PipingNetworkSegment.SegmentNumber` maps here when an adapter can preserve
   it). Neither it nor an XML `Object@id` becomes canonical identity
   automatically.
5. **Segment properties are segment-local and optional; nothing is inherited
   from the line.** An absent property means *not specified yet*, not a default
   value. `nominal_diameter`, `piping_class`, and `fluid_code` are open strings
   (`DN80`, `3"`, `A1A`, `P`) because no canonical quantity or vocabulary model
   exists yet.
6. **`kind` is a closed two-value vocabulary:** `"pipe"` or `"direct"`; any other
   value is a validation error rather than a silently reinterpreted
   realization. It defaults to `"pipe"` when omitted on input, because authoring a
   realization states that the adjacency has a physical realization. No
   realization means the realization is not modelled; `kind: pipe` means it is
   explicitly pipe-realized; `kind: direct` means it is explicitly direct.
   Canonical save currently serializes the resulting value explicitly as
   `kind: pipe`, because `save_plant()` excludes `None` values but does not
   exclude defaults.
7. **`PipingRealization` is not a `PipingConnection`.** It has no endpoints of its
   own. `Connection` ids are plant-unique, so a plain id string is a sufficient
   reference and no `ConnectionRef` wrapper exists.
8. **Segment order is authoring order**, not flow direction; this layer carries
   no flow semantics.

## Property-boundary limitation (first slice)

A segment boundary must coincide with an existing `Connection` boundary. A
property change *inside* one `Connection` is not representable yet
(mid-connection `PropertyBreak` semantics are deferred), and therefore a segment
is not "maximal": adjacent segments with identical properties are allowed and are
not flagged.

## Authored shape

```yaml
plant:
  id: demo

equipment:
  - id: P-101
    type: pump
    ports:
      - id: discharge
  - id: FV-101
    type: valve
    ports:
      - id: inlet
      - id: outlet
  - id: E-101
    type: heat_exchanger
    ports:
      - id: inlet

connections:
  - id: C-001
    source:
      component: P-101
      port: discharge
    target:
      component: FV-101
      port: inlet
  - id: C-002
    source:
      component: FV-101
      port: outlet
    target:
      component: E-101
      port: inlet

piping:
  lines:
    - id: PL-P101-DISCHARGE
      line_number: DN80-P-101-A1A   # optional, never canonical identity
      segments:
        - id: SEG-1
          nominal_diameter: DN80    # optional, open string
          piping_class: A1A
          fluid_code: P
          realizations:
            - connection: C-001
              kind: pipe
            - connection: C-002
              kind: pipe
```

Existing example: `examples/realistic-process-fragment/plant.yaml` realizes its
evidenced `P-101 → FV-101 → E-101` run and deliberately carries no
`line_number`, `segment_number`, `nominal_diameter`, `piping_class`, or
`fluid_code`, because the fragment has no engineering evidence for them.
`kind: direct` is exercised by focused synthetic tests.

## Deliberately not modelled

Mid-`Connection` property breaks (`PropertyBreak`), `1:N` / parallel / as-built
realizations, revision status, canonical `Pipe` or pipe-piece identity,
`PipingComponent` and tee/valve/fitting taxonomy, `Nozzle`/`PipingNode`
refinement, line-level property inheritance or defaults, typed quantities with
units, insulation/heat tracing/slope/pressure-test-circuit/flow-direction data,
off-page or continuation connectors, instrumentation and signals, DEXPI
Plant/P&ID import or export, P&ID rendering, and any process ↔ physical
realization mapping.

Each item has a stated trigger in ADR-0011's *Revisit When* list; none is
authorized by its absence here.

## Related

- [plant-model.md](plant-model.md) — the topology this layer references.
- [yaml-format.md](yaml-format.md) — load/save mechanics.
- [ADR-0011](../dev/decisions/ADR-0011-canonical-physical-piping-realization.md) —
  the decision; [ADR-0010](../dev/decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md)
  — the `Port`/`Connection` boundary.
- [../physical-piping-model.md](../physical-piping-model.md) — the design
  evidence: requirement analysis, candidate B selection, worked fragment, Git
  diff behaviour, and rule/adapter/rendering implications.
- [../dexpi-plant-pid-spike.md](../dexpi-plant-pid-spike.md) — the official
  DEXPI `V2.0.0` model and Reference P&ID evidence behind the shape.
