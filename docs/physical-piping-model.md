---
type: specification
status: active
source_of_truth_for:
  - physical-piping-canonical-model
read_when:
  - physical-model-growth
  - piping-model-work
  - pfd-pid-modeling
  - dexpi-plant-pid-mapping
update_when:
  - canonical-model-change
  - piping-model-change
---

# Physical Piping Model

> Decision status: **the canonical boundary is decided and recorded in
> [ADR-0011](decisions/ADR-0011-canonical-physical-piping-realization.md).**
> This document is the specification/decision deliverable of Issue #24.
>
> Implementation status: **nothing is implemented by this document.** No
> `src/`, `tests/`, or `examples/` change, no new fixture, no adapter, no
> dependency. The current semantic model still has no piping layer.

> Scope: this document answers **what is the physical piping graph?** It does
> **not** answer how `ProcessStep` maps to `Equipment` or how `ProcessStream`
> maps to physical piping. Process ↔ physical realization remains a separate
> unresolved problem and is deliberately absent from this design.

## Purpose

DeepPlant can today represent *physical inventory plus directly known directed
adjacency* (`Equipment` with owned `Port`s, property-free `Connection`s) but it
cannot represent the piping between those items: no line identity, no property
boundary, no elementary realization. The DEXPI Plant/P&ID spike
([dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md), ADR-0010) showed that gap
is real engineering semantics present in the official DEXPI Reference P&ID and
that **none of it can be closed by changing `Port` or `Connection`**.

This document specifies the smallest canonical DeepPlant layer that closes it
faithfully enough for future P&ID work, using DEXPI `V2.0.0` as *evidence*, not
as a schema. It deliberately does not reproduce DEXPI's class hierarchy, and it
selects one minimal design rather than a family of options.

## Existing invariants

These remain in force after this decision:

```text
Connection  = directed, property-free physical adjacency between two Ports
Connection  != Pipe / piping segment / piping line / piping realization
Connection  != ProcessStream / Signal
ProcessStream != physical piping
ProcessPort  != Port (and != Nozzle)
semantic model != presentation model
```

Two ADR-0010 conclusions are preserved and are load-bearing here:

- `Port` remains sufficient for DeepPlant's currently claimed physical-topology
  abstraction (`Port` is a documented collapse of DEXPI `Nozzle` +
  `PipingNode`, not an equivalence).
- `Connection` remains directed semantic topology only; it must never absorb
  pipe, segment, line, stream, or signal semantics.

This document adds one precise requirement that ADR-0010 could not have stated
yet: **the piping layer references identified `Connection`s instead of restating
physical connectivity**, so `Connection` needs canonical identity (see
[Why `Connection` gains identity](#why-connection-gains-identity)). Identity is
not an engineering property; the non-physical, property-free meaning of
`Connection` is unchanged.

## Engineering requirements

Requirements are grouped by evidence strength. They are the reason the selected
shape exists; they are not a wish list.

### Required for the first useful slice

| # | Requirement | Why it is required |
|---|---|---|
| R1 | **Line identity:** state which piping line a physical connection belongs to | "What piping line is this connection part of?" has no home today; DEXPI puts it on `PipingNetworkSystem.LineNumber`, above the edge |
| R2 | **Property boundary:** represent nominal-diameter, piping-class, and fluid/service-code changes that coincide with canonical physical-topology boundaries | The first piping slice can state a DN or piping-class change where topology already provides separate `Connection`s; a mid-connection property break needs additional semantics and is explicitly deferred |
| R3 | **Elementary realization kind:** distinguish pipe-realized adjacency from direct (not pipe-realized) adjacency | DEXPI's `Pipe` vs `DirectPipingConnection` distinction is real (2 of 31 elementary connections in the official instance are direct); "not yet modelled" and "direct by design" must not collapse into one state |
| R4 | **One authored topology fact:** the piping layer must not restate endpoints or create a second connectivity representation | Engineering-as-Code invariant: two independently authored connectivity facts are a synchronization liability ([process-topology.md](process-topology.md)) |
| R5 | **Inline items as endpoints:** an inline valve/fitting terminates one adjacency and starts the next; it is an ordinary physical item owning its connection points | Instance-proven in DEXPI; already true in DeepPlant's `Connection` pair for `FV-101` (spike Finding I1) |
| R6 | **Branch expressibility:** a branch point must be representable without a second graph or a node concept | A piping model that only handles linear chains is insufficient; branches are normal P&ID content |
| R7 | **Git-native review:** a small engineering change must produce a small, local, human-verifiable diff | Engineering-as-Code is DeepPlant's core thesis, not a nice-to-have |

### Likely future requirements (not designed for, but not blocked)

| # | Requirement | Note |
|---|---|---|
| F1 | Line-level property defaults inherited by segments | DEXPI carries the same templates on `PipingNetworkSystem` and `PipingNetworkSegment`; DeepPlant defers inheritance and keeps properties segment-local |
| F2 | Typed quantities with units for DN, design/operating pressure and temperature, thickness | Same open gap the DEXPI Process spike recorded for stream quantities |
| F3 | Insulation, heat tracing, slope, pressure-test circuit attributes | Present on `PipingNetworkSegment` in DEXPI; the segment is the right future home |
| F4 | Off-page / continuation connectors and cross-sheet semantics | DEXPI `PipeOffPageConnector`; needs its own evidence |
| F5 | Parallel, replacement, or as-built realizations for one adjacency, and revision status | Would force the currently unresolved `1:N` cardinality question |
| F6 | A canonical branch/junction kind distinct from a generic physical item | Only if `Equipment` + `type` provably cannot carry a tee |

### Not currently justified

| # | Rejected now | Why not |
|---|---|---|
| N1 | `Nozzle` and `PipingNode` (item + node endpoints) | Node refinement only becomes necessary when two connections must attach to the *same* connection point; no DeepPlant requirement or example produces that |
| N2 | Nozzle engineering data and purpose classification | Capability DeepPlant does not have; conditional on N1 |
| N3 | A piping-component taxonomy (valve/fitting/reducer subclasses) | The piping layer never needs item classification: inline items appear only as connection endpoints |
| N4 | Line-number, fluid-code, or piping-class libraries and standard enforcement | External data ownership; belongs to adapters/references, not the canonical model |
| N5 | Flow direction, thermodynamic state, or simulation topology in the piping layer | That is `ProcessStream`/simulator semantics; DEXPI's segment `FlowDirection` is deferred |
| N6 | Coordinates, routing, symbol ids, sheet/layout metadata | Presentation (ADR-0003) |
| N7 | A generic `Component` / `Entity` / physical-item hierarchy | Anti-roadmap: no repetition, coupling, or current requirement justifies it |

## Evidence from DEXPI / ADR-0010

This section reuses the evidence already established in
[dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md) §7–§8 and ADR-0010 and does
not repeat that investigation. The DEXPI pin is unchanged: official stable
`V2.0.0` (tag `V2.0.0`, commit `260c81c5`, 2025-10-10, CC BY 4.0), plus the
official Reference P&ID instance.

| DEXPI fact (evidence level) | Engineering meaning | Consequence for DeepPlant |
|---|---|---|
| `PipingNetworkSystem.LineNumber` identifies a piping line; `PipingNetworkSegment.SegmentNumber` identifies a segment; neither is on the connection (model + instance) | Line and segment designations, and property grouping, live *above* the elementary edge | Preserve optional external/human designations separately from canonical line and segment identities (R1, R2) |
| `PipingNetworkSegment` owns `Connections` and `Items` and carries `FluidCode`, `PipingClassCode`, `NominalDiameter*`, insulation, tracing, slope, test circuit (model) | A segment is the engineering property boundary of a line | Properties belong on a property boundary, not on equipment or on `Connection` (R2) |
| `Pipe` is "an elementary piece of piping, i.e. not interrupted by any item"; an inline valve splits a run into two `Pipe`s (instance) | Ends of elementary pieces are items, so an inline item terminates one piece and starts the next | Elementary realization is a per-adjacency fact; DeepPlant's existing `Connection` already has exactly that granularity (R5) |
| `Pipe` vs `DirectPipingConnection` (model + instance: 29 vs 2) | Realization is either pipe-realized or direct | The *distinction* matters; DEXPI's two classes do not (R3) |
| Endpoints are item + `PipingNode`; `PipingComponent` owns nodes and is both source and target item (model + instance) | Node refinement exists because DEXPI refines a physical side into nodes | DeepPlant already names sides as `Port`s; node refinement is only needed if two connections must meet on one `Port` (N1, R5) |
| Instance scale: 11 systems, 23 segments, 29 pipes, 5 `PipeTee` | Branches are normal content; segments outnumber systems | A linear-only model is insufficient (R6) |
| DEXPI puts engineering objects in `Core.ConceptualModel` and drawing data in `Core.Diagram`/`Plant.Diagram` (model) | Line/segment semantics are not drawing data | No coordinates, routing, or symbol ids enter this layer (N6, ADR-0003) |
| DEXPI establishes **no** `ProcessStep` ↔ equipment or `ProcessStream` ↔ piping mapping and no cardinality (spike §10) | Process realization is unproven by this evidence | Process ↔ physical mapping stays out of scope here |

What is deliberately **not** taken from DEXPI: the class hierarchy and its names
(`PipingNetworkSystem`, `PipingNetworkSegment`, `PipingConnection`,
`DirectPipingConnection`, `PipingNodeOwner`), the system/segment dual template
inheritance, `PipingNode` identity, off-page connectors, jacketed-pipe variants,
and the `PipingComponent` taxonomy (N1–N4, N7).

## Concept boundaries

Five levels must be reasoned about separately. Only some of them need their own
canonical object.

```text
level 1  physical plant item          Equipment            (pump, exchanger, inline valve, tee)
level 2  physical connection point    Port                 (owned, owner-local id)
level 3  physical topological adjacency Connection         (directed, property-free)
level 4  elementary piping realization PipingRealization   (kind: pipe | direct)
level 5  piping grouping / identity   PipingSegment, PipingLine
```

| Level | Canonical object after this decision | Justified by |
|---|---|---|
| 1 physical plant item | `Equipment` — **unchanged**; potentially a second physical-item kind later (N7, F6) | Existing model; inline items already work as endpoints (R5) |
| 2 connection point | `Port` — **unchanged** | ADR-0010; nozzle/node refinement not required (N1) |
| 3 topological adjacency | `Connection` — **unchanged meaning**, gains canonical identity | R4: the piping layer must reference it instead of restating endpoints |
| 4 elementary realization | **new:** `PipingRealization` | R3; required to keep "unmodelled" and "direct" distinguishable |
| 5 grouping / identity | **new:** `PipingSegment` (property boundary) and `PipingLine` (line identity) | R1, R2; these are the two genuine engineering identities above the edge |

Levels 4 and 5 are the *only* new canonical concepts. Nothing else is
introduced: no node type, no component hierarchy, no second graph container per
item, and no property on `Connection`.

## Candidate A — line metadata over topology

Line owns connection references and one property set; there is no segment level
and no separate realization object.

```yaml
piping:
  lines:
    - id: PL-101
      line_number: 3"-P-101-A1A
      nominal_diameter: DN80
      piping_class: A1A
      fluid_code: P
      connections: [C-001, C-002]
```

Assessment:

- Meets R1, R4, R5, R6 (a branch is just another line referencing connections).
- **Fails R2 and R3.** One property set per line cannot express a DN or class
  change inside one line, and there is no way to say that one adjacency is
  direct while another is pipe-realized. A property change would have to be
  faked as a second "line", which asserts a different line identity that the
  engineering data does not support.
- Smallest possible shape, so it is the natural *degenerate case* of the
  selected candidate (one line with one segment).

## Candidate B — line + segment + realization, referencing topology

Line groups segments; segment is the property boundary and owns elementary
realizations; a realization references one `Connection` and states how that
adjacency is realized.

```yaml
piping:
  lines:
    - id: PL-101
      line_number: 3"-P-101-A1A
      segments:
        - id: SEG-1
          segment_number: 1
          nominal_diameter: DN80
          piping_class: A1A
          fluid_code: P
          realizations:
            - connection: C-001
            - connection: C-002
```

Assessment:

- Meets R1–R7.
- Every reference is by canonical id, so no positional or restated topology.
- Strictly generalizes candidate A: the extra level appears only where
  properties or realization kind actually differ, so the extra cost is
  conditional rather than structural.
- Cost: two new identity levels plus one reference object; five structural
  rules to validate (see
  [Selected minimal canonical shape](#selected-minimal-canonical-shape)).

## Candidate C — independent piping graph

The piping layer owns its own nodes and edges, with equipment attachments
represented as node references.

```yaml
piping:
  graph:
    nodes:
      - id: N-1
        kind: equipment-port
        component: P-101
        port: discharge
      - id: N-2
        kind: component-port
        component: FV-101
        port: inlet
    edges:
      - id: E-1
        kind: pipe
        source: N-1
        target: N-2
        line: PL-101
```

Assessment:

- **Rejected.** It authors physical connectivity a second time (endpoints
  restated as graph nodes), which is exactly the duplication class
  [process-topology.md](process-topology.md) rejected for `ProcessStream`.
  Any change to equipment or ports must then be synchronized in two places.
- It also drags in the concepts the evidence does not justify: piping node
  identity, a `kind` taxonomy of nodes, and a second identity namespace for
  physical endpoints — while `Port` already provides the identity it needs.
- It would be needed only if DeepPlant had node-level connectivity that `Port`
  cannot express (N1).

## Rejected variant D — widen `Connection` with piping properties

Put `line`, `nominal_diameter`, `piping_class`, and `fluid_code` directly on
`Connection`. Rejected by the anti-roadmap in [roadmap.md](roadmap.md) and by
ADR-0010: it makes the topology primitive a physical engineering object,
collapses "one connection = one property set" onto an adjacency that can share
a property set with many adjacencies, and gives every connection a copy of
line-level engineering data. It does not remove the need for line and segment
identity, so it is not even smaller.

## Comparison

| Dimension | A: line over topology | B: line + segment + realization **(selected)** | C: independent graph |
|---|---|---|---|
| Semantic precision | Line identity only | Line, property boundary, realization kind | Highest apparent fidelity, but duplicates authorship |
| Minimality | Smallest, but insufficient for R2/R3 | Adds levels only where engineering differs; A is its single-segment case | Largest: second graph, node identity, item taxonomy |
| Fit with current model | Good | Good: reuses `Equipment`/`Port`/`Connection` unchanged in meaning | Poor: parallel connectivity namespace beside `Connection` |
| Git/YAML readability | Very readable | Readable: one reference line per elementary realization; ids keep diffs local | Noisy: touching an item edits nodes **and** edges |
| Validation complexity | Low | Low: resolution, uniqueness, membership, non-empty segment | High: two graphs must stay mutually consistent |
| Future engineering rules | Cannot check DN/class continuity across property changes | DN/class continuity, reducer requirement at boundaries, missing/direct realization, line-number consistency all checkable | Possible, but rules operate on a duplicated graph |
| DEXPI import/export | Line only; segments and pieces have nowhere to map | Line, segment, and elementary piece map without inventing structure | Requires deriving a graph from DEXPI items and nodes |
| P&ID rendering | Cannot place property-change annotations | Segment boundaries aligned with `Connection` boundaries and realization kind are renderable inputs; a renderer must not invent mid-connection breaks | Renderer would need to reconcile two graphs |
| Migration path | Requires a later reshape to B → churn | Additive to current model; `Connection` only gains identity | Separate layer to keep in sync forever |
| Premature-abstraction risk | Low but functionally insufficient | Low: each level answers a named requirement | High: designs for N1/N7 that are not justified |

## Selected minimal canonical shape

**Candidate B is selected.** Two identity levels (`PipingLine`,
`PipingSegment`) plus one reference object (`PipingRealization`), referencing
identified `Connection`s.

```text
PlantModel
├── Plant
├── Equipment[]              physical plant items (unchanged; inline valve/tee are items)
│   └── Port[]               physical connection points (unchanged)
├── Connection[]             directed, property-free physical adjacency — meaning unchanged
│   ├── id                   canonical identity (new; required by the piping layer)
│   ├── source: PortRef
│   └── target: PortRef
├── PipingModel (optional)   mirrors PlantModel.process
│   └── PipingLine[]
│       ├── id               canonical line identity (never a drawing or DEXPI id)
│       ├── line_number      optional human line designation
│       ├── name             optional
│       └── PipingSegment[]
│           ├── id           canonical identity local to the owning line
│           ├── segment_number     optional human/external engineering designation
│           ├── nominal_diameter   optional open string (DN80, 3", NPS3)
│           ├── piping_class       optional open string (A1A)
│           ├── fluid_code         optional open string (P)
│           └── PipingRealization[]
│               ├── connection     id of one PlantModel Connection
│               └── kind           "pipe" (default) | "direct"
└── ProcessModel (optional)  unchanged, still independent of everything above
```

Recorded semantics:

1. **`PipingModel` is the piping container, mirroring `PlantModel.process`**
   (ADR-0005/ADR-0006 precedent). It is optional: a plant without authored
   piping stays valid, exactly as today's fixtures do.
2. **Piping is a dependent layer, not an independent graph.** Unlike
   `ProcessModel`, a `PipingModel` cannot be valid on its own: it references
   `Connection`s owned by the physical layer. Its validation boundary is
   therefore *cross-layer* (plant + its connections), and this asymmetry with
   `ProcessModel` is intentional and recorded.
3. **`PipingLine.id` is the canonical identity** of a piping line.
   `line_number` is the human designation (for example `3"-P-101-A1A`) and is
   an open, optional string: designations follow company/line-numbering
   practice, may be revised, and are not guaranteed unique across a project.
   A DEXPI `PipingNetworkSystem` XML object id never becomes `PipingLine.id`.
4. **`PipingSegment.id` is canonical identity local to the owning line.**
   `segment_number: str | None` is an optional human/external engineering
   designation, including DEXPI `PipingNetworkSegment.SegmentNumber` when an
   adapter can preserve it. Neither a DEXPI XML `Object@id` nor `SegmentNumber`
   becomes canonical identity automatically.
5. **Segment properties are segment-local and optional.** No inheritance from
   the line is defined (F1 deferred). An absent property means *not specified
   yet*, which is honest engineering state rather than a default value. In this
   first slice, a segment boundary must coincide with a `Connection` boundary;
   a property change inside one `Connection` is not representable yet.
6. **`PipingRealization.kind` is a closed first-slice vocabulary:** `"pipe"` or
   `"direct"`; any other value is a validation error. It defaults to `"pipe"`
   because authoring a realization explicitly states that the adjacency has a
   physical realization. No `PipingRealization` means the realization is not
   modelled; `kind: pipe` means it is explicitly/semantically pipe-realized;
   `kind: direct` means it is explicitly direct. Serialization may omit the
   default so common authored YAML stays one line per realization.
7. **`PipingRealization` is not `PipingConnection`.** It is not an edge with
   its own endpoints; it is a statement *about* an existing adjacency. It is
   deliberately named after the engineering act (realization), not after
   DEXPI's class.
8. **A `Connection` is referenced at most once in the first slice** across all
   segments of all lines. This conservative 1:1 invariant is not a universal law
   of physical engineering; parallel, as-built, or alternative realizations are
   a deferred 1:N question. `ConnectionRef` is not introduced: connection ids
   are plant-unique, so a plain id string is a sufficient reference.
9. **Segment order is authoring order**, not flow direction. No flow semantics
   exist in this layer (N5).

### Structural rules (the piping layer's validation boundary)

| # | Rule |
|---|---|
| C1 | `Connection.id` is required, non-empty, and unique within `PlantModel` |
| P1 | `PipingLine.id` is unique within `PipingModel.lines` |
| P2 | `PipingSegment.id` is unique within the owning `PipingLine` |
| P3 | every `PipingRealization.connection` resolves to a `Connection` in the same `PlantModel` |
| P4 | **First-slice invariant:** a `Connection` is referenced by at most one realization across the whole `PipingModel` |
| P5 | a segment has at least one realization (an empty property boundary is meaningless) |

These are structural and referential rules, comparable in kind to the physical
layer's existing endpoint resolution and to S1–S4 in `ProcessModel`. C1 is a
pre-1.0 breaking change to authored YAML. P4 is intentionally conservative and
may be relaxed only through a later evidence-backed ADR change. These are **not**
engineering rules: DN continuity, reducer requirements, and line-number
consistency are rule-engine concerns described below.

### First-slice property-boundary limitation

A first-slice segment boundary must coincide with an existing canonical
physical-topology boundary between `Connection`s. For example, a reducer item
between `C-001` and `C-002` supports `SEG-1 → C-001` and `SEG-2 → C-002`.

By contrast, one `Connection` with DN80 over its first part and DN50 over its
second part, without an explicit topology item or boundary, is not representable
canonically yet. DEXPI has explicit `PropertyBreak` and related break semantics;
DeepPlant does not introduce `PropertyBreak` now. This is a known fidelity
limitation, explicitly deferred. Revisit when DeepPlant needs to represent a DN,
piping-class, insulation, or similar property change that does not coincide with
an existing topology item or `Connection` boundary.

### Why `Connection` gains identity

The realization level must point at a specific adjacency. The alternatives were:

| Option | Verdict |
|---|---|
| Reference the connection by restating its `PortRef` pair | **Rejected:** restates topology, so equipment/port edits must be synchronized in two places (R4 — candidate C's defect) |
| Reference by position/index inside `PlantModel.connections` | **Rejected:** insertion renumbers siblings, producing exactly the noisy churn R7 forbids |
| Reference by canonical `Connection.id` | **Selected** |
| Reference by a derived key (for example a hash of the endpoints) | **Rejected:** identity changes whenever an endpoint is retargeted, and diffs lose a readable name |

A required, plant-unique `Connection.id` is a **pre-1.0 breaking change** to
authored YAML (existing examples and fixtures must add ids). It is still the
smallest change that satisfies R4 and R7: it adds identity only, no engineering
property and no piping semantics, and it lets validation messages and code
review name a specific connection instead of `connections[0]`. The exact field
rules belong to the implementation slice named below.

`Connection` remains:

```text
directed semantic topology between two physical connection points
```

and nothing more. It does not gain line, segment, DN, class, fluid, insulation,
flow, or realization data.

### Why no canonical `Pipe` class

DeepPlant does **not** need a `Pipe` object in the first slice:

- An elementary pipe piece is already the granularity of a `Connection`,
  because inline items terminate adjacencies (spike Finding I1, R5). A `Pipe`
  object would be a second object with the same extent as a `Connection`.
- Pipe-piece identity carries no independent engineering meaning for DeepPlant
  today: DEXPI's `Pipe` has no properties of its own, and the line/segment data
  lives on the segment.
- The only fact DeepPlant currently lacks is the *kind* of realization, which
  `PipingRealization.kind` records without introducing elementary-piece
  identity.
- Isolated pipe-piece identity matters for spool/material take-off, stress, and
  fabrication workflows — future concerns over external data (F5, N4), not
  current canonical-model requirements.

Result: `Pipe` is **deferred**, and `DirectPipingConnection` is **collapsed**
into `kind: direct` rather than becoming a class.

### Why inline components stay `Equipment`

| Strategy | Verdict |
|---|---|
| **A — inline components remain `Equipment`** | **Selected for the first slice.** `FV-101` already owns `inlet`/`outlet` and already terminates two `Connection`s, which is DEXPI's structural role for a piping component. No piping-layer object needs to know that an item is a valve. |
| **B — separate `PipingComponent` kind now** | **Deferred.** It would duplicate `Equipment`'s identity, ownership, and port mechanics without a requirement that distinguishes them. Trigger: a concrete engineering need `Equipment` + open `type` cannot carry (N3, F6). |
| **C — common physical-item abstraction later** | Deferred; an anti-roadmap item (N7). The generic `Component` base class does not exist today and is not introduced here. |

Consequence to accept honestly: an inline valve and a pressure vessel are both
`Equipment` for now. That is a deliberate simplification, recorded rather than
hidden, and the piping layer is not blocked by it because it treats items only
as connection endpoints.

### Why no `Nozzle` / `PipingNode`

`Port` remains the canonical connection point (ADR-0010). Node refinement is
required only when two connections must attach to *one* physical connection
point. In DeepPlant, sides are named ports: a valve has `inlet`/`outlet`, a tee
has `run_in`/`run_out`/`branch_out`. No requirement, example, or rule in this
layer produces two connections on one port, so DEXPI's item/node pair stays an
adapter concern and the unresolved DEXPI → `Port.id` derivation recorded by
ADR-0010 remains unresolved.

### Branch handling

A branch point is a **physical item with three ports plus three ordinary
`Connection`s** — not a graph node and not a piping-layer concept:

```text
P-101.discharge ── C-001 ──→ TEE-101.run_in
                              TEE-101.run_out    ── C-002 ──→ FV-101.inlet
                              TEE-101.branch_out ── C-004 ──→ V-101.feed_inlet
FV-101.outlet   ── C-003 ──→ E-101.process_inlet
```

Two properties make that sufficient:

- Topology already encodes the branch; the piping layer only *groups*
  adjacencies into segments and lines, so branching needs no extra structure.
- A tee's third port being unconnected (a spare) or leading to another line is
  an ordinary topology state, not a new concept.

Deliberately **not** decided here: whether a tee deserves a distinct
physical-item kind (F6), and whether a spare port is a violation (it is not; it
is a reportable spare).

## Worked realistic fragment

The committed fixture
([examples/realistic-process-fragment/plant.yaml](../examples/realistic-process-fragment/plant.yaml))
already contains the required physical chain. The YAML below is **illustrative
of the decided canonical shape** (it is not yet loadable: `Connection.id` and
the `piping` section do not exist on `main`).

### Linear case: `P-101 → FV-101 → E-101`

```yaml
equipment:
  - id: P-101
    type: pump
    ports:
      - id: suction
      - id: discharge

  - id: FV-101
    type: control-valve
    ports:
      - id: inlet
      - id: outlet

  - id: E-101
    type: heat-exchanger
    ports:
      - id: process_inlet
      - id: process_outlet

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
      port: process_inlet

piping:
  lines:
    - id: PL-P101-DISCHARGE
      line_number: DN80-P-101-A1A
      segments:
        - id: SEG-1
          nominal_diameter: DN80
          piping_class: A1A
          fluid_code: P
          realizations:
            - connection: C-001
            - connection: C-002
```

What this states, and why it is faithful:

- `FV-101` is **not crossed** by one realization. It terminates `C-001` and
  starts `C-002`, exactly as DEXPI needs two `Pipe` objects around the globe
  valve — but expressed with two existing `Connection`s and no `Pipe` class.
- Line identity (`DN80-P-101-A1A`), the property boundary (SEG-1: DN80, A1A,
  fluid P), and the elementary realizations are separate facts: none of them
  touches `Connection` or `Port`.
- The pump's `suction` port and the exchanger's `process_outlet` remain
  unconnected, which stays legal and unchanged from today's behaviour: an
  unmodelled adjacency is still reported as absent rather than invented.
- No `PipingRealization.kind` is authored, so both adjacencies mean
  `kind: pipe`. A nozzle-to-nozzle abutting connection would instead read:

  ```yaml
            - connection: C-007
              kind: direct
  ```

### Branch case: a tee on the discharge line

Physical reality:

```text
P-101.discharge    ── C-001 ──→ TEE-101.run_in
                                 TEE-101.run_out    ── C-002 ──→ FV-101.inlet
                                 TEE-101.branch_out ── C-004 ──→ V-101.feed_inlet
FV-101.outlet      ── C-003 ──→ E-101.process_inlet
```

```yaml
equipment:
  - id: TEE-101
    type: pipe-tee        # ordinary item with three ports; no tee class exists yet
    ports:
      - id: run_in
      - id: run_out
      - id: branch_out

connections:
  - id: C-001           # P-101.discharge → TEE-101.run_in
    source:
      component: P-101
      port: discharge
    target:
      component: TEE-101
      port: run_in

  - id: C-002           # TEE-101.run_out → FV-101.inlet
    source:
      component: TEE-101
      port: run_out
    target:
      component: FV-101
      port: inlet

  - id: C-003           # FV-101.outlet → E-101.process_inlet
    source:
      component: FV-101
      port: outlet
    target:
      component: E-101
      port: process_inlet

  - id: C-004           # TEE-101.branch_out → V-101.feed_inlet
    source:
      component: TEE-101
      port: branch_out
    target:
      component: V-101
      port: feed_inlet

piping:
  lines:
    - id: PL-P101-DISCHARGE
      line_number: DN80-P-101-A1A
      segments:
        - id: SEG-1
          nominal_diameter: DN80
          piping_class: A1A
          fluid_code: P
          realizations:
            - connection: C-001
            - connection: C-002
            - connection: C-003

    - id: PL-V101-FEED
      line_number: DN50-P-101-A1A-B1
      segments:
        - id: SEG-1
          nominal_diameter: DN50
          piping_class: A1A
          fluid_code: P
          realizations:
            - connection: C-004
```

Observations the branch case forces:

- The branch is expressed purely by topology (the tee, its three ports, three
  ordinary connections) plus ordinary line grouping. No node object, no
  branch flag, no junction class.
- The run through the tee (`C-001`, `C-002`) stays **one segment** because the
  properties do not change at the tee; only where properties change does a
  segment boundary appear. The tee itself does not split a segment.
- The branch line is a separate `PipingLine` with its own number and its own
  smaller DN, which is normal in line-listing practice.

## Git/YAML implications

The design was checked against the diffs engineers and reviewers actually make.
Every reference is a canonical id, so no positional index ever shifts and no
sibling is renumbered.

**Change DN80 → DN100 on a segment** — one line, no structural change:

```diff
         - id: SEG-1
-          nominal_diameter: DN80
+          nominal_diameter: DN100
           piping_class: A1A
```

**Change the piping class on part of a line** — the property change appears as a
segment split, and the affected realization moves with a one-line edit:

```diff
       segments:
         - id: SEG-1
           nominal_diameter: DN80
-          piping_class: A1A
+          piping_class: A2A
           fluid_code: P
           realizations:
             - connection: C-001
+        - id: SEG-2
+          nominal_diameter: DN80
+          piping_class: A1A
+          fluid_code: P
+          realizations:
             - connection: C-002
```

**Insert a valve into a run** — the topology genuinely changes (one adjacency
becomes two), and the piping layer follows with a single added reference; the
existing realization line is untouched:

```diff
 connections:
   - id: C-002
     source:
       component: FV-101
       port: outlet
     target:
-      component: E-101
-      port: process_inlet
+      component: FV-101-B
+      port: inlet
+  - id: C-005
+    source:
+      component: FV-101-B
+      port: outlet
+    target:
+      component: E-101
+      port: process_inlet

 piping:
   ...
           realizations:
             - connection: C-002
+            - connection: C-005
```

Note that `C-002` keeps its identity when only its target is retargeted; the new
adjacency gets a new id (`C-005`) instead of renumbering its siblings.

**Split a line at a reducer** — a new segment boundary plus the new item; no
realization is renumbered, because membership is by id:

```diff
       segments:
         - id: SEG-1
           nominal_diameter: DN80
           realizations:
             - connection: C-001
+        - id: SEG-2
+          nominal_diameter: DN50
+          realizations:
             - connection: C-002
```

**Add a branch** — a new item, ports, connections, and a second line; larger,
but localized and reviewable as engineering change:

```diff
+  - id: TEE-101
+    type: pipe-tee
+    ports:
+      - id: run_in
+      - id: run_out
+      - id: branch_out
 ...
+piping:
+  lines:
+    - id: PL-V101-FEED
+      line_number: DN50-P-101-A1A-B1
+      segments:
+        - id: SEG-1
+          realizations:
+            - connection: C-004
```

**Rename or re-designate a line** — one line, and the canonical id is
unaffected, so nothing else in the file changes:

```diff
     - id: PL-P101-DISCHARGE
-      line_number: DN80-P-101-A1A
+      line_number: DN80-P-101-A1B
```

Assessment against R7:

- Small engineering changes produce small diffs; the largest noise source is
  the topology change itself, which is legitimate.
- No diff requires renumbering, re-ordering, or re-indenting unrelated
  content, and there is no second place to keep synchronized (contrast with
  candidate C: editing an item would touch nodes *and* edges).
- The design deliberately avoids the two shapes that would be noisy: piping
  properties on `Connection` (every connection line in the file would grow) and
  positional connection lists inside a line (insertions would shift ranges).
- One readability trade-off is accepted: `connection: C-001` is an opaque id,
  so reviewing a piping diff sometimes means jumping to the `connections`
  section — the same jump engineers already make for `PortRef`s today.

## Engineering-rule implications

No rule is implemented. The test is whether the model makes honest checks
*possible later* without inventing data:

| Future check | Supported by | Type |
|---|---|---|
| DN continuity: adjacent segments of one line differ in DN | `PipingSegment.nominal_diameter` + aligned topology boundary | engineering rule (first slice requires a `Connection` boundary; a reducer specifically requires item classification) |
| Piping-class continuity along a line | `PipingSegment.piping_class` + topology | engineering rule |
| Required reducer at a DN transition | topology at the boundary + `Equipment.type` (open string) | engineering rule; needs no taxonomy to be reported |
| Line-number consistency (one line, one designation) | `PipingLine.line_number` | engineering rule (warning-level: variants and revisions are legitimate) |
| Duplicate line identifiers | `PipingLine.line_number` | rule candidate; **not** structural, because designations are not guaranteed unique by practice |
| Branch topology: a tee's ports are each connected at most once | `Connection` + `Port` (existing rules) | topology rule; does **not** need the piping layer |
| Inline-component connectivity: an inline item is an endpoint of exactly the expected number of adjacencies | `Connection` + `Port` | rule candidate; a spare/blank port is reported, not rejected |
| Missing endpoints: a port with no connection | `Connection` (existing) | reportable information, not an error |
| Unrealized adjacency: a `Connection` with no realization | piping membership (the absence of a realization entry) | reportable information: "no piping realization modelled" is honest, unlike inventing a pipe |
| Direct vs pipe-realized routing for a check | `PipingRealization.kind` | engineering rule |
| Orphan/duplicate membership | P3, P4 (structural) | structural validation, part of the layer itself |

Conclusions:

- **Segments are an engineering boundary, not bookkeeping:** most useful checks
  (DN, class, reducer) need a property boundary that `Connection` and `Port`
  cannot express.
- **The piping layer is not needed for topology checks.** Branches, missing
  endpoints, and inline-component connectivity are derivable from `Equipment` /
  `Port` / `Connection` alone. That is a strong signal that no node/junction
  concept belongs in this layer.
- **`kind` must fail fast.** The closed first-slice vocabulary accepts only
  `pipe` and `direct`; for example, `kind: ppie` is a validation error rather
  than an unmodelled or silently reinterpreted realization.

## DEXPI adapter implications

Conceptual mapping for a future Plant/P&ID adapter. No adapter is implemented
and Plant import remains unimplemented and fail-closed (ADR-0010).

| DEXPI `V2.0.0` concept | DeepPlant after this decision | Class |
|---|---|---|
| `PipingNetworkSystem` (`LineNumber`, system grouping) | `PipingLine` (`line_number`); system grouping itself is dropped | **collapsed** |
| `PipingNetworkSystem` templates (fluid code, piping class, DN, insulation) | `PipingSegment` fields when not overridden; inheritance is not reproduced | **lossy** (documented drop of system-level defaults) |
| `PipingNetworkSegment.SegmentNumber` | `PipingSegment.segment_number` | **direct as optional engineering designation**; neither it nor XML `Object@id` is canonical identity |
| `PipingNetworkSegment` properties | `PipingSegment` properties | **collapsed**, subject to the first-slice property-boundary limitation |
| `PipingNetworkSegment.Connections` | `PipingSegment.realizations` | **direct** (per elementary connection) |
| `PropertyBreak` / property change not aligned to a `Connection` boundary | no first-slice canonical representation | **unsupported / deferred**; a future importer must report this fidelity loss rather than invent a boundary |
| `Pipe` (elementary piece, no own data) | `PipingRealization(kind: pipe)` | **collapsed** — piece identity is not preserved |
| `DirectPipingConnection` | `PipingRealization(kind: direct)` | **direct as a kind**, no class |
| `PipingConnection.SourceItem`/`TargetItem` + `SourceNode`/`TargetNode` | `Connection.source`/`target` (`PortRef`) | **collapsed** (item + node collapses into `Port`) |
| `Nozzle` / `PipingNode` | `Port` (unchanged collapse from ADR-0010) | **lossy / unresolved** — the `Port.id` derivation is still open |
| `PipingComponent` (valve, fitting) and subclasses | `Equipment` + open `type` | **lossy / deferred** |
| `PipeTee`, `PipeReducer` | `Equipment` + open `type` (physics in topology) | **lossy / deferred** |
| Insulation, tracing, slope, pressure-test circuit | nothing yet | **unsupported** (must fail closed or be an explicit documented drop) |
| `JacketLineNumber`, `PipingNetworkSystemGroupNumber`, jacketed-pipe data | nothing | **unsupported** |
| `PipeOffPageConnector` (by number / by object) | nothing | **unsupported / unresolved** (dangling endpoint handling) |
| `Core.Diagram`/`Plant.Diagram` piping labels, `PipingNodePosition` | nothing | **presentation-only** (ADR-0003) |
| DEXPI XML `Object@id` | nothing | **adapter-generated** only; never canonical identity |

Import direction is therefore viable for a defined subset (system → line,
segment → segment, connection → realization, item+node → `Port`), with the
losses above stated explicitly. Export direction is *asymmetric and partial*:
DeepPlant can emit a `Pipe` per `kind: pipe` realization, but it cannot emit
system-level templates it does not store, property breaks it cannot represent,
or node identities. `segment_number` can be emitted only when authored or
preserved; neither it nor an XML `Object@id` may be invented as canonical
identity. Both directions belong to a later Issue.

## P&ID rendering implications

The boundary stays exactly as ADR-0003 requires:

```text
canonical semantics
        ↓
presentation / view policy
        ↓
P&ID view
```

| Semantic input a future P&ID view may consume | Use |
|---|---|
| `PipingLine.line_number` | line designation label |
| `PipingSegment` boundaries aligned with `Connection` boundaries | where a first-slice property-change annotation belongs (DN/class change, reducer symbol) |
| `PipingRealization.kind` | how the run is drawn between two items (`direct` = abutting items, no pipe body) |
| `Equipment` + inline items | item symbols (valve, tee, equipment outline) |
| `Port` | attach points for routes — never drawn as symbols themselves |
| `Connection` | which two attach points a route connects |

What this layer deliberately does **not** provide, and what a renderer must
therefore own: coordinates, symbol ids, routing, line breaks, sheet assignment,
label placement, and insulation/tracing annotation. Also:

- A pipeless `Connection` (no realization) must not make P&ID rendering
  impossible: the presentation policy decides whether to draw it as a plain
  connection. Semantic completeness is not presentation completeness.
- A segment boundary aligned with a `Connection` boundary is representable.
  A mid-`Connection` property break is not yet representable canonically; a
  future renderer must not invent such a boundary.
- Segment order is not a route: renderers may not assume `realizations` are in
  geometric order, only that they are grouped. A future *routing* need is a
  presentation/view concern, not a piping-model field.
- Rendering must not require `PipingRealization` to exist at all: today's
  fixtures remain renderable, which keeps rendering decoupled from this layer.

## Explicitly deferred concepts

Recorded so that no reader mistakes a deferral for an oversight:

```text
canonical Pipe class or elementary pipe-piece identity
canonical DirectPipingConnection class (kind value only)
Nozzle, PipingNode, item + node endpoints
PipingComponent kind, valve/fitting/reducer taxonomy, tee class
PipingNetworkSystem-style system grouping, jacketing, system-level templates
line/segment numbering schemes; fluid-code, piping-class, line-number libraries
quantity/unit typing for DN, pressure, temperature, wall thickness
insulation, heat tracing, slope, pressure-test circuit
flow direction, thermodynamic state, simulation topology
off-page / continuation connectors and cross-sheet semantics
multiple or as-built realizations per adjacency; revision status
DEXPI `PropertyBreak` / mid-`Connection` property-break semantics
piping-related drawing data (coordinates, routing, symbols, sheets)
instrumentation and signal layers (separate future layer, ADR-0010)
process <-> physical realization (see below)
```

## Unresolved questions

1. **`Connection.id` field rules.** Required vs optional, uniqueness scope, and
   guidance for authoring ids. Decided as *required and plant-unique* in
   principle; the exact Pydantic rules belong to the implementation slice.
2. **Default `kind: pipe`.** A default keeps YAML short but could silently
   claim pipe realization. The current choice is a documented default; if
   evidence shows rules need certainty, `kind` becomes explicit.
3. **Open `kind` vocabulary.** Consistent with `ProcessStep.function`, but it
   permits typos. Revisit if only the two evidenced values ever matter.
4. **Segment maximality.** Adjacent segments with identical properties are
   allowed and not flagged; whether they should be merged is an engineering
   rule question, not a structural one.
5. **Realization cardinality.** `1:1` (one realization per connection) is the
   first-slice assumption. `1:N` (parallel/as-built realizations) is unresolved
   and deliberately deferred (F5).
6. **Line-level property defaults.** DEXPI carries templates at both system and
   segment level; DeepPlant keeps properties segment-local until evidence
   requires inheritance (F1).
7. **Branch-item identity.** Whether a tee/junction deserves a canonical kind
   distinct from `Equipment` is deferred (F6) with the stated trigger.
8. **`PipingModel` validation ownership.** Cross-layer validation (P3/P4) needs
   an explicit owner; today the closest precedent is `PlantModel`'s existing
   reference validation over `Equipment`/`Port`.
9. **DEXPI `Port.id` derivation** from `Nozzle` + `PipingNode` identity —
   carried forward unresolved from ADR-0010, now also relevant to realization
   endpoints.
10. **Off-page/continuation connectors:** whether DEXPI's dangling-endpoint
    concept needs a canonical representation or stays adapter-visible.

## Process ↔ physical realization remains out of scope

Repeating ADR-0010 explicitly, because the temptation to smuggle it in here is
real:

```text
ProcessStep   ↔ Equipment                                          unresolved
ProcessStream ↔ PipingLine / PipingSegment / PipingRealization     unresolved
ProcessPort   ↔ Port                                               unresolved
```

No `process_ref`, `stream_ref`, `realized_by`, `implements`, or `maps_to` field
is introduced, and nothing in the selected shape requires one. The piping layer
is deliberately useful **independently** of the process graph: it is about
physical reality, not about which process function motivated it. DEXPI `V2.0.0`
establishes no such mapping and no cardinality (spike §10/§12), so inventing one
here would be unbacked design.

## Recommended first implementation slice

Exactly one next slice is recommended, and it is **not** implemented here:

> **Add the piping container and the elementary realization layer as a small
> vertical slice with executable tests:** `PipingModel` with
> `PipingLine` → `PipingSegment` → `PipingRealization`, a required plant-unique
> `Connection.id`, `PlantModel.piping`, YAML load/save round-trip, structural
> rules P1–P5, and an extension of the realistic fragment example that realizes
> `P-101 → FV-101 → E-101` as a pipe-realized line plus at least one
> `kind: direct` realization.

Scope notes for that slice:

- It changes `Connection` by **identity only**; `Connection` stays property-free
  topology. It must not widen `Connection` with piping properties.
- It is a documented pre-1.0 breaking change: existing YAML (`examples/`),
  fixtures, and tests that author connections gain ids.
- It includes tests for P1–P5 (including the negative cases: duplicate
  realization, dangling connection reference, empty segment) and for the
  round-trip.
- It excludes: DEXPI Plant import/export, any rule engine, P&ID rendering,
  process↔physical mapping, `Nozzle`, `Pipe`, `PipingComponent`, a tee class,
  and insulation/tracing attributes.
- If the slice finds that P4 (one realization per connection) or the `kind`
  default is wrong in practice, that is evidence for revisiting ADR-0011 rather
  than silently widening the layer.

## Related

- [docs/dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md) — the DEXPI
  `V2.0.0` model + Reference P&ID evidence this specification builds on.
- [ADR-0011](decisions/ADR-0011-canonical-physical-piping-realization.md) —
  the durable decision this document specifies.
- [ADR-0010](decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md) —
  `Port`/`Connection` boundary and the deferred piping/instrumentation layers.
- [ADR-0005](decisions/ADR-0005-process-model-container.md),
  [ADR-0006](decisions/ADR-0006-process-model-root-integration.md) — the
  submodel-container precedent this layer follows.
- [docs/process-topology.md](process-topology.md) — the duplication invariant
  that motivates referencing `Connection` instead of restating endpoints.
- [docs/architecture.md](architecture.md), [docs/roadmap.md](roadmap.md),
  [docs/rendering.md](rendering.md).
