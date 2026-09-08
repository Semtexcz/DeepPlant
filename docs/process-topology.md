---
type: research
status: proposed
source_of_truth_for:
  - proposed-process-topology-model
read_when:
  - process-topology-decisions
  - pipes-streams-modeling
  - pfd-pid-modeling
update_when:
  - decision-changes
---

# Process Topology Model

> Decision status: **proposed — requires human review before implementation.**

This document is a research proposal only. It contains **no implemented schema,
no production code, and no example-file changes**. It answers the next open
architectural question of DeepPlant:

> What should represent process connectivity in the canonical model, and what is
> the semantic relationship between `Connection`, process streams,
> pipes/pipelines, equipment ports/nozzles, and inline components?

## Question

The current implementation intentionally stops at a topology-only
`Connection`. The open decision is whether that distinction is correct and which
semantic concepts should come next. This spike answers that from engineering
reality first:

```text
engineering reality
      ↓
domain concepts
      ↓
relationships / identity
      ↓
candidate canonical model
      ↓
possible serialization
```

not from "what YAML would look nice".

## Method and Evidence Rules

- This spike is documentation-only and does not implement, rename, or extend any
  model class (no `ProcessStream`, `Pipe`, `Pipeline`, `Nozzle`, `PipingLine`,
  or component hierarchy in code).
- Claims are grounded in: (a) the current DeepPlant model and ADRs,
  (b) primary DEXPI specification material and the pyDEXPI reference
  implementation, (c) publicly readable process-simulation source
  (DWSIM/CAPE-OPEN interfaces), and (d) public professional-system material
  where it exists.
- Claims that could not be verified from a primary or authoritative public
  source are explicitly marked **unverified / hypothesis**. Nothing here claims
  standards compliance.
- Numbered references `[S1]`…`[Sn]` resolve in the [Sources](#sources) section.

## Current DeepPlant Model

The shipped semantic model (`src/deepplant/model.py`) is:

```text
PlantModel
├── Plant
├── Equipment[]
│   └── Port[]
└── Connection[]
    ├── source: PortRef
    └── target: PortRef
```

Facts relevant to this question:

- `Port` is a named connection point owned by exactly one `Equipment` item.
  Port identity is local to the owning equipment; a global endpoint is the pair
  `(component id, port id)`.
- `PortRef` is the structured endpoint reference (`component` + `port`). Its
  field is deliberately named `component` (not `equipment`) so the reference
  format can survive further component types gaining ports later.
- `Connection` is a directed `source`→`target` semantic topological
  relationship. Direction records which endpoint is source and which is target;
  it does **not** add flow, stream, or piping meaning.
- `Connection` has **no identifier and no engineering properties** and is not a
  pipe, process stream, signal, or physical line.
- Reference validation resolves endpoints against `Equipment` and its `Port`s
  only; it enforces referential integrity, not engineering topology rules.

The shipped invariant:

```text
Connection
=
directed semantic topology

Connection
!=
pipe
!=
process stream
!=
signal
!=
physical line
```

The example `examples/minimal-process/plant.yaml` deliberately exercises only a
tank-outlet → pump-suction adjacency. ADR-0002, ADR-0003, ADR-0004 and the
architecture/product documents preserve this boundary; the pipes/streams
representation is the recorded open modeling question in `docs/roadmap.md`.

## Realistic Fragment

Reasoning only from `Tank → Pump` hides every interesting distinction. The
analysis below therefore uses a small conceptual fragment that is rich enough to
expose the modeling problems. Process chemistry is irrelevant; the fragment is
only a carrier for topology questions.

```text
                                   branch line
                                       │
                                       ▼
                         ┌──────────────────────────────► (other destination)
                         │
T-101 Feed Tank ──► P-101 Pump ──► FV-101 control valve ──► E-101 Heat Exchanger ──► V-101 Vessel
      │                                                                                     │
      └──────────────◄────────────── recycle line ──────────────────────────────────────────┘
                                 (recycle valve in the recycle line)
```

Physical-piping reality of the same fragment (one plausible reading):

- tank outlet nozzle → suction piping → pump suction nozzle;
- pump discharge nozzle → discharge piping, containing a control valve and
  reducers, → heat-exchanger inlet nozzle;
- exchanger outlet nozzle → piping → vessel inlet nozzle;
- a **tee** (branch point) in the exchanger outlet piping leads to another
  destination (its own line);
- a **recycle tee** in the vessel outlet or suction piping merges recycle flow
  into the feed piping ahead of the pump;
- one **spec break** in the discharge line changes nominal size and pipe
  specification mid-line (`DN100 / spec A → DN50 / spec B`);
- each connection between equipment passes through an equipment nozzle; the
  nozzles themselves carry sub-identities (typically `N1`, `N2`, …) and sizes.

The fragment is intended to expose at least these distinctions, all of which
recur below:

1. **process flow** — material that moves and can be described by state;
2. **physical piping** — real pipes with size, spec, insulation, tracing;
3. **topological connectivity** — which connection points touch which;
4. **branch points** — one upstream flow splitting into two destinations;
5. **inline components** — control valve, recycle valve, reducers, tees;
6. **equipment boundaries** — unit operations where state changes;
7. **line identity** — the line number and its continuity across sections;
8. **nozzle identity** — the physical equipment connection point;
9. **merges / recycles** — converging flows and loops;
10. **spec/line breaks** — physical property changes within a route.

None of this fragment is implemented in this spike; the fragment is used below
only to test candidate models.

## Engineering Concepts

This section defines each engineering concept independently of any serialization.
Every definition is then checked against what DEXPI, simulators, and DeepPlant
already do, so the model follows the engineering distinctions rather than
inventing them.

### Connection (as DeepPlant defines it today)

DeepPlant `Connection` is a **directed adjacency between two connection points**:
a pure graph edge that says "source port touches target port". Its properties:

- It is *binary*: one source, one target. It cannot branch or merge by itself;
  a branch requires two edges leaving a shared point, i.e. a junction.
- It records **topological adjacency only**. It has no medium, no direction of
  flow, no state, no physical realization.
- Today it connects equipment-owned ports, but the reference format is generic
  enough for later component types.

Engineering reality check: process engineers and P&ID engineers do not normally
number "adjacencies". What they number are streams (process level) and lines /
piping items (physical level). DEXPI reaches the same conclusion structurally:
its `PipingConnection` is an abstract "elementary connection between two piping
items", whose concrete subtypes are `Pipe` (a physical elementary pipe piece)
and `DirectPipingConnection` (a connection *not* realized by a pipe; in the
serialization it has **no element at all** and is implied by successive items)
[S3]. In other words, even DEXPI does not treat a bare adjacency as a tagged
first-class engineering object: direct adjacency is implicit, and physical
identity starts at the pipe piece / line level. pyDEXPI confirms the same shape
in code: `PipingConnection` with `sourceItem/sourceNode/targetItem/targetNode`
references and `Pipe`/`DirectPipingConnection` subtypes [S5].

Conclusion: `Connection` is a useful **canonical primitive** for the topology
layer, but it is not an engineering deliverable object. It should stay pure and
small. Making it carry stream or pipe meaning conflates three different facts
(adjacency, logical flow, physical realization).

### Process Stream

A process stream is the entity process engineers reason about when they say
"the feed stream", "stream 12", or read a PFD stream table:

- In **process design / PFD**, a stream is a logical material flow between
  process functions, typically identified by a stream number and summarized in a
  stream table with temperature, pressure, flow, and composition.
- In **process simulation**, a material stream is a first-class object that
  carries thermodynamic state between unit operations. It is not a pipe: it has
  no nominal size, wall thickness, insulation, or routing.

Two verified anchors:

- **DEXPI Process model**: `Stream` is a subtype of `ProcessConnection` that
  composes `MassFlow`, `Pressure`, `Temperature`, and `VolumeFlow` quantities
  and references a `MaterialState` (properties of the stream, total + per-phase)
  and a `MaterialTemplate` (the material/thermo-model structure). DEXPI 2.0
  states that `MaterialTemplate` "determines the legend for a stream table when
  the model is used to represent a Process Flow Diagram" [S2][S4]. DEXPI 2.0
  explicitly targets transfer of "simulation results (like stream tables)" for
  BFDs/PFDs [S4].
- **DWSIM** implements a `MaterialStream` class (a `Stream`-category simulation
  object) whose interface exposes phases, overall/per-phase composition,
  temperature, pressure, mass/molar/volumetric flow, enthalpy, and the attached
  thermodynamic property package — and implements CAPE-OPEN material interfaces
  (`ICapeThermoMaterial`…) [S6][S7]. A DWSIM `Pipe`, by contrast, is a **unit
  operation** (`Pipe` inherits `UnitOpBaseClass`, categorized under pressure
  changers) with length/hydraulic/heat-transfer calculations [S6]. The stream is
  the state-carrying connection; the pipe is a calculation object that the
  stream passes through.

Answers to the design questions, based on this evidence:

- A stream represents **material flow between unit-operation / process-function
  boundaries**, and it carries (or can carry) thermodynamic state: composition,
  flow, temperature, pressure, phase [S2][S4][S6].
- A stream is *not* bound to a single physical pipe section. One logical stream
  can be realized by several physical pipe sections separated by components
  (e.g. a control valve inside a discharge line does not terminate the stream).
  Conversely, several streams can share one physical line at different times or
  in different operating modes (**unverified as a general rule / hypothesis**:
  in engineering practice, line lists and PFDs are kept consistent by the
  designer, not by an automatic invariant).
- Across a pump, heat exchanger, or vessel the stream is *redefined*: each
  state-changing boundary has an inlet stream and an outlet stream with
  different properties. Simulators enforce this by construction — a material
  stream connects to exactly one inlet port and one outlet port of unit
  operations [S6].
- Valves inside a line normally do **not** create new PFD stream identities,
  because they do not change process state at PFD abstraction. In simulation, a
  valve is itself a unit operation and therefore *does* sit between two streams
  [S6]. This difference (PFD view vs simulation view) is a view/abstraction
  difference over the same physical reality; the canonical model must not be
  forced to choose a single topology because of it.

### Pipe / Piping Line / Piping Network / Segment

Physical piping terminology in P&ID / piping engineering distinguishes several
levels. DEXPI P&ID 1.4 encodes exactly this layered reality, which makes it the
best public evidence for the distinctions engineers actually need [S3]:

| Engineering idea | DEXPI P&ID 1.4 class | Verified definition / attributes |
|---|---|---|
| Line-number object | `PipingNetworkSystem` | "A fluid system of interconnected piping network branches limited by Unit Operation Inlet/Outlet and Piping Network Terminators"; carries `LineNumber`, `FluidCode`, `PipingClassCode`, nominal diameter, insulation, heat tracing [S3] |
| Segment | `PipingNetworkSegment` | piping limited by Nodes/Breaks/Connectors; where bounded by nodes/connectors "the Segment will coincide with a Piping Branch"; composes `Connections` and `Items`; carries segment number, slope, flow classification [S3] |
| Elementary pipe | `Pipe` (subtype of `PipingConnection`) | "An elementary piece of piping, i.e. not interrupted by any item" [S3][S5] |
| Direct adjacency | `DirectPipingConnection` | "A direct connection between two piping items, i.e. a connection that is not realized by a pipe"; implicit in serialization [S3][S5] |
| Inline device | `PipingComponent` (+ `PipeFitting`, valves…) | a `PipingNetworkSegmentItem` with nodes and source/target roles; e.g. `PipeReducer` "has different nominal pipe size at the two ends"; `PipeTee` "has three piping ends in T-shape, including a branch at 90 degrees" [S3][S5] |
| Property change | `PropertyBreak` | "A symbol indicating a change in the piping properties"; can be a nominal-diameter break, piping-class break, insulation break, or composition break [S3][S5] |
| Off-page continuation | `PipeOffPageConnector` | indicates a piping segment continues elsewhere, on the same or another P&ID [S3][S5] |

Crucially, DEXPI **keeps pipe pieces as connections (edges)** inside a segment
and **keeps components/nozzles/breaks as items with connection points
(`PipingNode`s)** — a `PipingNode` is "a possible connection point for a
PipingConnection" carrying nominal diameter [S3]. A physical pipe is therefore
not treated as a component node; it is the edge-like run between items. This is
a genuine engineering distinction, not a serialization artifact: components
(valves, reducers, tees) interrupt the pipe and are the objects that own
connection points. In the Proteus implementation, two pipe centerlines inside
one segment must be separated by a `PipingNetworkSegmentItem` (e.g. a
`PipingComponent`), otherwise they would represent a single `Pipe` with a
graphical gap [S3].

Terminology conclusion for DeepPlant: the canonical physical object at the level
engineers tag is a **piping line** (one line number), composed of **segments**.
The DEXPI word `PipingNetworkSystem` is close in scope but chosen for an
ISO-15926 reference-data world; DeepPlant should prefer the established
engineering word **line** for its canonical entity and map to DEXPI terms inside
the future adapter. `Pipe`, `Pipeline`, `PipingNetwork`, and `Line` are compared
in [Candidate Models](#candidate-models); the naming recommendation is
[here](#recommended-model).

### Nozzle

A nozzle is a **physical connection point on equipment**: a projecting short
piece of pipe attached to an equipment body, through which process material
enters or leaves. Engineers name nozzles (`N1`, `N2`, …) and size them. DEXPI
P&ID 1.4 models `Nozzle` as "a projecting short piece of pipe that is attached
to another (hollow) body" — a class that owns `PipingNode`s, can act as
`PipingSourceItem`/`PipingTargetItem` (an end point of connections and
segments), and carries a `SubTagName` plus nominal pressure. `Equipment` owns
nozzles via `NozzleOwner`, and `ProcessNozzle` is the subtype "intended to
enable transfer of process material" [S3][S5]. The nozzle is the boundary
between equipment and the piping network; a `PipingNetworkSystem` is "limited by
Unit Operation Inlet/Outlet" boundaries [S3].

For DeepPlant the design question is the relationship between `Port` and
`Nozzle`:

- Today `Port` is a *semantic* connection point on equipment: exactly the
  abstraction the topology layer needs, and it remains canonical.
- A **nozzle is physical hardware detail** (subtag, size/rating) that, in the
  target model, should be expressible as optional metadata attached to an
  equipment port — or, if detailed P&ID nozzle data is ever required, as a
  separately referenced physical object with its own identity.
- Not every port must be a nozzle (e.g. logical ports used by future
  instrument/signal functions). No inheritance hierarchy or forced
  one-to-one `Port == Nozzle` is justified yet.
- No new class is needed to represent the current fragment at the topology or
  process level. Nozzles become necessary when P&ID-level piping connects to
  *named physical* equipment outlets; record this as a deferred refinement
  (see [Recommended Model](#recommended-model)).

### Inline Components

Valves, reducers, orifices, filters, check valves, and control valves sit
*inside* piping. Their conceptual position is well established by DEXPI and by
simulation practice:

- They are **components with connection points** — nodes in the physical
  topology graph, not edges. A reducer joins two pipe sizes; a tee has three
  ends; each has `PipingNode`s [S3][S5].
- In DEXPI they are `PipingComponent`s (and fittings such as `PipeReducer`,
  `PipeTee`, flanges) that are items of a `PipingNetworkSegment` and can be
  sources/targets of `Pipe`/`DirectPipingConnection` edges [S3][S5].
- Their **identity differs from an edge's**: a bare pipe piece is rarely tagged,
  but a valve is tagged; a control valve additionally has an
  instrument-function identity (e.g. `FV-1234`) distinct from its physical
  body. DEXPI models the control *function* as a `ProcessInstrumentationFunction`
  [S3]. This dual identity is a future modeling question.
- In simulators a valve is a unit operation with ports and a pressure-drop
  model; it is not a material stream [S6].

For the realistic fragment, inline components are the reason a single process
stream (equipment to equipment) must not be conflated with a single physical
pipe run: the discharge route T-101 → E-101 contains a control valve and
reducers, yet the PFD stream is one object and the pipe run is one or more
physical segments.

## PFD vs P&ID

PFD and P&ID are different engineering views over the same plant and use
different but related concepts [S1][S4]:

| Concept | PFD | P&ID |
|---|---|---|
| Major equipment | yes | yes |
| Process stream (logical, numbered) | yes — the main connecting concept | no (streams are not drawn; flow arrows/labels only) |
| Physical piping line | no (piping omitted or stylized) | yes — line number is central |
| Line number | no | yes |
| Nozzle | no (equipment boundary only) | yes (connection to piping) |
| Inline valve | usually no (control valves may be noted for major control) | yes |
| Thermodynamic stream state | yes — stream table | no (design conditions live in the line list/datasheets, not the drawing) |
| Branch topology | yes — drawn as splitting lines | yes — via tees/components and line branches |
| Recycle loops | yes | yes (as physical lines) |

Which concepts belong where:

- **Shared semantic model**: equipment, ports/connection points, and a
  connectivity substrate both views can use.
- **PFD-level abstraction**: the numbered `ProcessStream` with state and
  composition; it intentionally ignores inline devices that do not change
  process state.
- **P&ID-level detail**: physical piping (`PipingLine` + segments), inline
  components, spec breaks, and nozzle-level connection.

The DEXPI 2.0 direction confirms this is how the domain itself is organized: one
specification now combines a *process model* (BFD/PFD, streams, stream tables,
simulation results) with a *plant model* (P&ID, piping, equipment) [S4]. The two
models are distinct but combinable — the separation argued here.

## DEXPI Findings

### Scope and versions (verified from the official site [S1])

- DEXPI (Data Exchange in the Process Industry) is an industry association whose
  current focus is exchange of intelligent P&IDs; its mission statement covers
  the whole process-plant lifecycle.
- Public specification family: **DEXPI P&ID Specification 1.4** (plant/P&ID
  model), **DEXPI Process Specification 1.0** (process model), and
  **DEXPI Specification 2.0**, which combines the P&ID plant model with an
  improved process model and targets BFDs, PFDs, and P&IDs. Since 2.0 the format
  is DEXPI XML (Proteus XML no longer required). Specifications are CC-licensed;
  the source of truth is the public GitLab repository `dexpi/Specification`
  [S1][S8].

### Plant model (P&ID) — concept map

The exact DEXPI P&ID 1.4 terms and verified definitions [S3][S5]:

| DeepPlant concern | DEXPI P&ID 1.4 term | Role |
|---|---|---|
| Equipment | `Equipment` (+ `TaggedPlantItem`/`TechnicalItem` supertypes) | Tagged apparatus/machine; owns chambers and nozzles |
| Nozzle / connection point | `Nozzle`, `NozzleOwner`, `ProcessNozzle`, `AccessNozzle`, `InstrumentNozzle`, `SprayNozzle`, `PipingNode` | Physical equipment connection; owns `PipingNode`s ("possible connection point for a PipingConnection") |
| Piping network / line | `PipingNetworkSystem` | line-number-level object; composes segments; carries line number, spec class, fluid code, DN, insulation, tracing |
| Piping segment | `PipingNetworkSegment` | piping between Nodes/Breaks/Connectors; may coincide with a piping branch; composes connections and items |
| Physical pipe run | `Pipe` (a `PipingConnection`) | elementary piping not interrupted by any item |
| Direct adjacency | `DirectPipingConnection` | connection not realized by a pipe; implicit (no serialization element) |
| Inline components | `PipingComponent`, `PipeFitting`, valve/fitting subtypes | segment items with nodes, source/target roles |
| Spec / line break | `PropertyBreak` | change in piping properties (diameter, class, insulation, composition) |
| Branch point | tee items + segment boundaries | branch is a segment/component concept; the segment definition references "Piping Branch" |
| Process flow / stream | — | **not part of the P&ID plant model**; lives in the process model |

Two structural facts matter most for DeepPlant:

1. DEXPI separates **items that own connection points** (`PipingNodeOwner`:
   nozzle, component, off-page connector, property break) from **connections
   between them** (`PipingConnection`: `Pipe` or `DirectPipingConnection`), and
   groups them into **segments** within a **system** that carries the line
   number [S3].
2. Connectivity is *not* a single generic graph in the P&ID model. It is
   expressed by segment membership + connection endpoints. pyDEXPI later
   *derives* a NetworkX graph for navigation (nodes = all DEXPI instances;
   edges = composition/reference attributes) [S5]. That derivation is an
   implementation convenience, not part of DEXPI's semantic core.

### Process model — concept map

The DEXPI process model (Process 1.0; re-published and extended in 2.0)
contains its own vocabulary [S2][S4]:

- `ProcessStep` (with details and ports) is the process-model analogue of a
  unit operation / function.
- `Port` (with `MaterialPort`, `EnergyPort`, `InformationPort` subtypes in 2.0)
  is the connection point of a `ProcessStep`.
- `ProcessConnection` connects ports; `Stream` is the process connection that
  carries material state: `MassFlow`, `Pressure`, `Temperature`, `VolumeFlow`
  plus `MaterialStateReference`/`MaterialTemplateReference`.
- `MaterialState` "contains the properties for a Stream… one for the total
  properties and then one for each of the phases present".
- `MaterialTemplate` defines the material/thermo-model structure and "determines
  the legend for a stream table when the model is used to represent a Process
  Flow Diagram".

So DEXPI has already found it necessary to distinguish **process streams with
thermodynamic state between unit-operation ports** from **physical piping with
line numbers, segments, and components**. The two models are published
separately (1.4 vs 1.0) and then *combined* in 2.0 — exactly the separation and
recombination a layered DeepPlant model needs.

### What DEXPI does *not* give DeepPlant

- DEXPI is an exchange format for diagrams with reference data (RDL), built on
  ISO 15926 concepts and (pre-2.0) a Proteus serialization. Its class
  granularity, naming (e.g. `PipingNetworkSystem`), and identity rules are
  shaped by exchange and reference-data requirements.
- DeepPlant's invariant remains: **DEXPI is an adapter/external representation,
  not the canonical model.** DeepPlant should adopt only the *engineering
  distinctions* DEXPI proves necessary, then choose its own smaller,
  Git-native representation.

## pyDEXPI Findings

pyDEXPI is the open-source reference-quality Python implementation of the DEXPI
data model (AGPL-3.0; supports DEXPI 1.3) [S5]. Findings from its README and
source:

- It ships the DEXPI data model as **Pydantic classes** in
  `pydexpi/dexpi_classes/` (piping, equipment, plant structure, instrumentation,
  graphics, etc.), loads Proteus-XML exports, and parses a model into a
  **NetworkX MultiDiGraph** whose nodes are DEXPI instances and whose edges are
  labelled composition or reference [S5].
- Physical piping appears exactly as in the specification: `PipingNetworkSystem`
  → `PipingNetworkSegment` → `Pipe`/`DirectPipingConnection` +
  `PipingComponent`/`PropertyBreak`/`PipeOffPageConnector` items, with
  `PipingNode`s owned by items. The `piping_toolkit` even contains functions
  like `connect_piping_network_segment`, `insert_item_to_segment`, and
  `piping_network_segment_validity_check`, confirming that *segments and items*
  are the working units of P&ID manipulation [S5].
- The **graph abstraction layer** (`GraphAbstractor`) provides
  `build_process_graph` (collapses piping internals into equipment/segment
  nodes) and `build_conceptual_graph` (abstracts instrumentation and piping
  into a compact process topology) [S5]. This is direct evidence that a
  PFD-like process topology is a *derived, collapsed view* of the detailed
  P&ID graph — an observation that strongly supports "views over a layered
  model" rather than "one edge type for everything".

Distinction: **DEXPI semantic necessity vs serialization/implementation
structure.** The necessary semantic distinctions (line/segment/component/pipe,
process stream vs physical line) come from the specification's information
model. The Proteus/DEXPI-XML element structure (`<CenterLine>` for pipes,
implicit direct connections, `<Node Type="process">`) is serialization detail.
pyDEXPI's NetworkX layer is implementation structure. DeepPlant should copy the
first category and ignore the other two.

## Simulator Findings

### DWSIM

- DWSIM is a steady-state/dynamic sequential-modular process simulator (GPLv3)
  and is CAPE-OPEN compliant [S7].
- Its `MaterialStream` class is a flowsheet object categorized as a **Stream**
  that implements CAPE-OPEN material interfaces (`ICapeThermoMaterial` etc.) and
  exposes composition, phases, temperature, pressure, flows, enthalpy, and the
  property package [S6]. Streams are the *state-carrying connections* between
  unit operations.
- Its `Pipe` class is a **unit operation** (`Inherits UnitOpBaseClass`,
  categorized as a pressure changer) with length/roughness and hydraulic and
  heat-transfer calculations [S6]; the DWSIM feature list confirms "pipes with
  detailed hydraulic and heat-transfer calculations" among the unit operations
  and even lists a "Pipe Network" operation in the extended edition [S7].

Conclusion: in a simulator, **the material stream is the process/simulation
flow, and a physical pipe — when simulated at all — is a unit operation with
ports that the stream passes through.** Pressure drop, length, and fittings
therefore belong to the pipe/unit-operation object, not to the thermodynamic
stream object. This is the same separation DEXPI makes between process streams
and piping.

### CAPE-OPEN

- CO-LaN manages the CAPE-OPEN standard: interfaces that let CAPE components
  interoperate, including unit operations, thermodynamic property packages, and
  material objects [S9].
- DWSIM's material stream implementing `ICapeThermoMaterial` shows the CO
  material-object concept aligning with a state-carrying stream, distinct from
  the unit operation that owns ports [S6]. Detailed CO interface semantics
  beyond this were not needed for the decision; deeper interface-by-interface
  analysis is deferred to the simulation-adapter stage.

## Professional-System Findings

Public technical material for AVEVA and Siemens COMOS is mostly marketing-level;
no reliable public documentation of their *internal* object models was found.

- AVEVA publicly positions "AVEVA Unified Engineering" as a data-centric
  engineering environment in which teams "collaborate on the same data set"
  across disciplines and project phases, with 1D/2D/3D design [S10]. AVEVA's
  DEXPI mission statement endorses data-centric, standards-based
  interoperability built on ISO 15926 [S1].
- Siemens is a DEXPI member; its public mission statement on the DEXPI site is
  "Interoperability is one of our professions" [S1]. The Siemens COMOS product
  page was not retrievable during this spike; no internal COMOS modeling claims
  are made here.
- **No claim about the internal data model of AVEVA or Siemens is made.** Any
  statement such as "COMOS stores equipment/nozzle/line as separate classes" is
  **unverified / hypothesis**. These systems matter to DeepPlant only as
  exchange peers through standards/adapters, not as canonical-model templates.

## Standards and Terminology Notes

- DEXPI 2.0 states that its data model is based on ISO 15926 [S4]; DeepPlant
  makes no ISO-15926 compliance claim and should not adopt reference-data
  machinery it does not need.
- The terminology used above (line number, piping line, spec break, nozzle,
  process stream, unit operation) follows established P&ID/piping and process
  engineering usage and is cross-checked against the DEXPI definitions in the
  tables above. No copyrighted standard text is reproduced and no standards
  compliance is claimed.

## Candidate Models

This section evaluates the canonical-model alternatives against the fragment
and the evidence. Option letters match the research task.

### Option A — `Connection` becomes the physical/process object

```text
Equipment.Port ← Connection → Equipment.Port

Connection:
  medium
  size
  pressure
  ...
```

Why it is attractive: it is the smallest change to the shipped model — one
class starts carrying engineering properties, and the YAML stays flat.

Where it breaks:

- A process stream is **not** one physical connection. In the fragment the
  stream T-101 → E-101 passes through a pump, control valve, reducers, and
  several pipe sections; a binary `Connection` with properties cannot own one
  stream state and multiple physical sections at once.
- Physical properties (size/spec/insulation) are properties of a **line and its
  segments**, not of an adjacency, and they change at spec breaks inside one
  route. Pushing them onto `Connection` forces artificial connection splits with
  no engineering meaning (or duplicated stream identity per section).
- A branch or recycle requires multiple outgoing connections from one point.
  Making `Connection` the process/pipe object conflates "which adjacency" with
  "which flow/pipe", and both DEXPI (connections vs items vs segments) and
  simulators (streams vs unit operations) separate them [S3][S6].
- It destroys the current clean invariant (`Connection != stream != pipe`) that
  ADRs and roadmap already rely on.

Verdict: rejected as the target; the attractive part (small change) is better
served by adding a *separate* small entity (Option B).

### Option B — `Connection` remains topology; `ProcessStream` is separate

```text
Equipment.Port ← Connection → Equipment.Port

ProcessStream:
  source: PortRef
  target: PortRef
  (later: phase/design state)
```

Evaluation:

- Matches DEXPI Process model (`Stream` between `ProcessStep` ports) and
  simulator material streams (state-carrying objects between unit operations)
  [S2][S4][S6].
- Gives process identity and later thermodynamic/design state a home without
  polluting adjacency.
- Branching: a binary stream cannot branch; each branch of the fragment is its
  own stream object (matching PFD numbering where branch lines carry separate
  stream numbers) — verified pattern in simulator/DEXPI process models where a
  split is a unit operation/step with separate outlet streams.
- Recycle: recycle is its own stream; loops appear as graph cycles of streams —
  allowed.
- Limitation: it does not yet answer the P&ID physical side (line number,
  inline components, spec breaks); that is Option C. If only Option B ships,
  the P&ID view of the fragment cannot be expressed.

Verdict: necessary and recommended as the process layer; not sufficient alone
for P&ID.

### Option C — `Connection` remains topology; physical `Pipe`/`Line` is separate

```text
Port ← Connection → Port

PipingLine / PipingNetwork:
    owns or references topology
    carries line number, size, spec, insulation...
```

Evaluation:

- Mirrors DEXPI's P&ID plant model (`PipingNetworkSystem` carries line number +
  physical attributes; `PipingNetworkSegment` groups connections/items; `Pipe`
  is an elementary physical connection) [S3].
- Supports P&ID line lists, spec breaks (as segment boundaries/`PropertyBreak`),
  and inline components inside segments.
- Branching and merges are handled by segment/component structure (tees) rather
  than by edge splitting.
- Limitation: process/simulation meaning (stream identity and state) has no
  home; PFD rendering and stream tables would still lack a semantic object. If
  only Option C ships, PFD semantics are lost or forced onto piping.

Verdict: necessary for P&ID; not sufficient alone for process/PFD.

### Option D — Layered model

```text
Topology layer:     Component / Port / Connection
Process layer:      ProcessStream
Physical layer:     PipingLine / PipingSegment / PipingComponent
```

Evaluation:

- This is the only option that expresses all fragment facts: adjacency
  (topology), process flow with state (process), and line/spec/component detail
  (physical). It matches the DEXPI 1.4/1.0 split and DEXPI 2.0 combination, and
  it matches simulator practice [S3][S2][S4][S6].
- The risk is over-modelling. The defence is that each layer is *one* small
  entity class at its introduction and that the layers can be added
  incrementally (B first, then C), each unlocking a distinct view.

Verdict: recommended as the *target architecture*; implement incrementally,
starting with the smallest entity that unlocks a real fragment.

### Option E — Everything is a component with ports

```text
Component -- Connection -- Component

Pump
Valve
PipeSegment
Reducer
...
```

Evaluation:

- Advantage: uniformity; a valve, tee, reducer, and pump are all nodes with
  ports; the graph is simple to navigate and to render.
- Problems: physical pipe is not naturally a node/component. DEXPI and
  engineering practice treat an elementary pipe as an *edge-like run between
  items*, and a line as a *container with segments and branches*; treating every
  pipe segment as a component node buries the line identity and inflates graphs
  [S3]. pyDEXPI must *collapse* such internals to obtain a process graph [S5],
  which shows the collapsed form is the useful abstraction and the flat
  everything-is-a-component graph is the low-level one.
- Additionally "component" would have to cover very different identity rules
  (equipment with tags, inline devices with or without tags, un-tagged pipe
  pieces), erasing the very distinctions this research found necessary.

Verdict: rejected as the single model; components-with-ports remain the right
shape for *equipment and inline devices* (nodes), while pipes/lines are
different (edges/containers).

## Comparison

All options are scored against the evaluation criteria (1 = weak, 3 = strong).
The scores are reasoned judgments from this document's evidence, not measured
values.

| # | Criterion | A (Connection = object) | B (+ProcessStream) | C (+physical line) | D (layered) | E (everything component) |
|---|---|---|---|---|---|---|
| 1 | Engineering semantic fidelity | 1 — conflates stream/pipe/adjacency | 2 — process layer only | 2 — physical layer only | 3 | 1 — pipe-as-node is wrong [S3] |
| 2 | Simplicity | 3 | 3 | 3 | 2 (more concepts, added in steps) | 2 (uniform but hides identity) |
| 3 | Represent PFD | 1 | 3 | 1 | 3 | 2 |
| 4 | Represent P&ID | 1 | 1 | 3 | 3 | 2 |
| 5 | DEXPI interoperability | 1 | 2 (process model) | 2 (plant model) | 3 | 1 |
| 6 | Simulation interoperability | 1 | 3 | 1 | 3 | 2 |
| 7 | Branching / merging | 1 | 2 (per-branch streams; junctions open) | 3 (tees/segments) | 3 | 2 |
| 8 | Recycle loops | 2 | 3 | 3 | 3 | 2 |
| 9 | Inline components | 1 | 2 (transparent by design) | 3 | 3 | 2 |
| 10 | Stable identity | 1 | 3 (stream numbers) | 3 (line numbers) | 3 | 1 |
| 11 | Git diff quality | 2 (property noise on edges) | 3 | 3 | 3 | 2 |
| 12 | Human-readable YAML feasibility | 3 (small) | 3 | 2 (segment nesting risk) | 2 (must be authored in layers) | 2 |
| 13 | Validation potential | 2 | 3 | 3 | 3 | 2 |
| 14 | Future multi-discipline extension | 1 | 2 | 1 | 3 (topology shared by signals later) | 2 |
| 15 | Avoiding unnecessary abstraction | 3 | 3 | 3 | 2 | 2 |

Reading: no single-layer option (A, B, C, E) covers both PFD and P&ID without
forcing one view's semantics onto the other. Option D scores highest on the
engineering-heavy criteria precisely because it preserves the distinctions that
DEXPI and simulators already make; its only weakness is the number of concepts,
which is mitigated by adding the layers one at a time. **Recommended reading:
adopt D's structure, but ship B's entity first, then C's entity** — that keeps
each actual model change small (criteria 2 and 15) while pointing at the correct
architecture (criteria 1, 3–9).

## Identity Analysis

Which objects need stable identity, and what kind?

| Object | Engineer refers to it as | Tagged? | Survives layout changes? | Referenced externally? | Git must recognize |
|---|---|---|---|---|---|
| Equipment | tag (`T-101`) | yes | yes | yes (datasheets, simulators) | same equipment after edits |
| Port / nozzle | nozzle subtag (`N1`) or function (`outlet`) | nozzles yes; function ports often not | yes | sometimes (nozzle schedules) | same port after renames of neighbors |
| Connection (adjacency) | rarely directly | no | yes (pure topology) | no | optional; endpoint pairs already stable |
| ProcessStream | stream number/name (`S-3`) | yes (stream tables) | yes | yes (simulators, heat/mass balances) | same stream after piping edits |
| PipingLine | line number (`10"-PL-101-1234-A1`) | yes | yes | yes (line lists, P&ID) | same line after routing changes |
| PipingSegment | not usually by tag | no | yes | rarely | continuity of a line after spec-break edits |

Key conclusions:

- Engineers and external tools reference **tags** (equipment tag, line number,
  stream number, nozzle subtag). Those are engineering identifiers, and their
  syntax is governed by standards/company rules — a later DeepPlant concern.
- Stable **semantic identity** is what Git and tooling need: an id that stays
  constant when a human label or tag changes, and that is not re-created by
  layout/routing edits. This is the "Engineering as Code" argument.
- This research exposes a future modeling question: DeepPlant will eventually
  need to separate **`id`** (stable model key), **`tag`** (engineering
  designation, possibly derived/validated), and **`name`** (human label). This
  spike does not change current models; the current single `id` per object is
  adequate until tags become first-class.
- `Connection` today needs no identity of its own: its meaning is fully
  determined by its two endpoint refs, and neither DEXPI (implicit direct
  connections) nor engineering practice tags adjacencies [S3]. An optional
  `id` should be added only when a higher layer must *reference* a specific
  adjacency (route membership of a stream/line) and endpoint pairs prove
  insufficient.

## Branching and Spec-Break Analysis

### Branching

```text
          ┌→ B
A → split ┤
          └→ C
```

The fragment splits at a tee in the exchanger outlet line. Consequences for each
candidate concept:

- **`Connection` (topology)**: does not branch. A branch is two connections
  sharing a junction. If the junction is an inline tee component, the two
  connections are `tee.run → pipe → B` and `tee.branch → pipe → C`. If the
  junction is an equipment port (e.g. two outlet streams from a vessel), both
  connections simply share the source port.
- **`ProcessStream`**: does not branch. Each branch becomes its own stream with
  its own identity/state (branch streams inherit the upstream state at the split
  point in PFD terms). This matches simulator practice, where a split requires a
  splitter unit operation with separate outlet streams, and PFD practice, where
  branches carry distinct stream numbers.
- **Physical piping**: a branch is a **tee component** (three ends) or a header
  take-off — a node, not an edge. DEXPI models tees as `PipeFitting`
  (`PipeTee`: "three piping ends in T-shape, including a branch at 90°") and the
  resulting branch lines as segments/`PipingNetworkSystem`s; a segment may
  coincide with a "Piping Branch" [S3][S5].

### Merging

```text
A ─┐
   ├→ merge → C
B ─┘
```

The recycle line merges into the feed line at a tee ahead of the pump.

- Topology: two connections arrive at the merge point; one leaves.
- Process layer: the merged stream downstream of the tee has a *different
  composition/state* than either inlet. In a PFD this merge is often drawn at
  an equipment inlet (e.g. pump suction) or at a drawn junction. In simulation a
  mixer unit operation exists precisely because the merged state must be
  computed.
- Physical layer: the merge point is again a tee/component, or a nozzle where
  the recycle line re-enters equipment.

Implication for the canonical model: **branch and merge are not edge
properties; they are structural facts created by components/ports and by
separate stream identities.** No splitter/tee class is implemented in this
spike; the analysis only decides that the topology layer must allow a port to
participate in several connections and the process layer must allow several
streams to touch one port (in or out).

### Recycle loops

```text
A → B → C
↑       │
└───────┘
```

- A recycle is a graph cycle. The topology layer already supports cycles with no
  special case (directed edges, arbitrary ports).
- Process layer: the recycle is a stream; a loop is valid and is how recycle
  ratios are described. Nothing in the model needs to forbid cycles.
- Physical layer: the recycle is a physical line (or part of one) with its own
  line number; the loop is expressed by line/segment topology.
- Validation implications (later): reachability and "no dangling stream" checks
  become meaningful once streams and lines exist; cycle *detection* is not a
  validity error for process plants.

### Spec / line breaks

```text
DN100 / spec A
      ↓
 reducer / boundary
      ↓
DN50 / spec B
```

Questions and answers:

- **Does a spec break create a new `Pipe` (elementary run)?** Yes, in the DEXPI
  sense the break separates pipe pieces; a `PropertyBreak` (or a reducer, which
  is an item with two different end sizes) sits between them [S3][S5].
- **Does it create a new `PipingSegment`?** Yes, segments are bounded by breaks
  by definition ("piping limited by a Node and a Break, … two Breaks, …") [S3].
- **Does it create a new `PipingLine` / line number?** Not necessarily. A spec
  break usually stays *within* one line number (the line list notes the break
  or lists multiple spec classes). When the break coincides with a new
  line-number assignment (branch-off, different service), the line identity
  changes. This is an engineering decision, not an automatic model rule
  (**partially hypothesis**: DEXPI provides the object types, but line-number
  assignment policy is project/company practice).
- **Does it create a new `ProcessStream`?** No. A spec break does not change
  process state; the PFD stream is unaffected. Only a state-changing boundary
  (pump, exchanger, vessel, valve in simulation) redefines the stream.

This is the cleanest demonstration that **logical process flow and physical
piping realization must be separable**: the same stream crosses the DN100→DN50
break, while the physical model records the change as a new segment bounded by
the break.

## Semantic Mapping Matrix

| Engineering concept | DeepPlant today | Recommended DeepPlant | DEXPI P&ID (plant) | DEXPI Process | PFD | P&ID | Simulator |
|---|---|---|---|---|---|---|---|
| Equipment | `Equipment` | `Equipment` (later generalized Component) | `Equipment` | `ProcessStep` | major equipment | equipment | unit operation |
| Connection point | `Port` | `Port` (semantic); optional nozzle metadata later | `Nozzle` + `PipingNode` | `Port` | stream end | nozzle/pipe end | unit-op port |
| Logical material flow | none | `ProcessStream` | not represented | `Stream` (ProcessConnection) | the connecting concept | not shown as object | material stream |
| Process stream state | none | future (state on `ProcessStream`) | n/a | `MaterialState`/`MaterialTemplate`, T/P/flow | stream table | n/a | thermo state on material stream |
| Physical piping line | none | `PipingLine` (next increment) | `PipingNetworkSystem` (line number) | n/a | not shown | line number | pipe = unit op (if modeled) |
| Piping segment | none | `PipingSegment` (later) | `PipingNetworkSegment` | n/a | n/a | drawn line pieces | n/a |
| Inline valve / component | `Equipment`? none formally | inline component with ports (later) | `PipingComponent` (+ fittings) | n/a | usually omitted | valve symbol | valve unit op |
| Spec break | none | segment boundary on a line (later) | `PropertyBreak` | n/a | n/a | break symbol | not a concept |
| Pipe run | none | part of segment model (later) | `Pipe` (a `PipingConnection`) | n/a | n/a | centerline | not a concept |
| Branch/merge point | port shared by several connections | tee component or shared port | tee item / segment branch | split/mix process steps | drawn junction | tee | mixer/splitter unit op |
| Recycle loop | graph cycle of connections | cycle of streams/lines | segment/system topology | stream loop | recycle line | physical line | recycle stream |

The matrix makes the semantic differences visible: each engineering concept has
one clear home per view, and none of the views requires `Connection` to become
anything other than topology.

## Recommended Model

### Recommendation in one paragraph

Keep `Connection` as the pure, directed, property-free **topology primitive**.
Model **process connectivity** with a separate **`ProcessStream`** entity
(process/PFD/simulation layer, later carrying design/thermo state), and model
**physical realization** with a separate **`PipingLine`** entity (P&ID/piping
layer, later owning segments and inline components). This is Option D's
structure, reached by shipping Option B's entity first and Option C's entity
second — never by promoting `Connection` into a pipe or a stream. Equipment
ports remain semantic connection points; nozzle hardware detail attaches to
ports later; inline components become components-with-ports when the physical
layer ships.

### Target shape (for context; not implemented)

```text
PlantModel
├── Plant
├── Equipment[]            today; later generalized to components
│   └── Port[]
├── Connection[]           unchanged: directed adjacency, no properties
├── ProcessStream[]        NEW (first increment): directed process flow
│                            between PortRef endpoints; later + state
└── PipingLine[]           NEW (second increment): line number + physical
     └── PipingSegment[]   properties; inline components gain ports
```

### Answers to the ten decision questions

1. **Should current `Connection` remain?** Yes. It is the topology substrate
   shared by all future layers; ADRs and roadmap already rely on it.
2. **Should `Connection` remain directed?** Yes — but its direction is only an
   orientation record (source→target), not flow semantics. DEXPI connections
   likewise distinguish source/target items and nodes [S3].
3. **Should `Connection` gain an ID?** Not in the next increment. Its meaning is
   its endpoint pair; engineers do not tag adjacencies and DEXPI leaves direct
   connections implicit [S3]. Add an optional id only if a later route/membership
   reference needs it.
4. **Should `Connection` ever carry engineering properties?** No. Properties
   belong to the layer that has the meaning: state on `ProcessStream`, physical
   attributes on `PipingLine`/segments. This is the single most important
   negative decision of this spike.
5. **Should `ProcessStream` be a separate entity?** Yes. Process flow has its
   own identity (stream number), its own state, and its own abstraction
   (inline devices transparent). DEXPI's process model (`Stream`,
   `MaterialState`, `MaterialTemplate`, stream tables) and simulators
   (material stream objects) make the separation an engineering fact, not a
   preference [S2][S4][S6].
6. **Should physical piping be a separate entity?** Yes. Line identity, spec
   class, size, insulation, tracing, and spec breaks cannot live on a
   topology edge or on a process stream without destroying both. DEXPI's plant
   model is the evidence [S3].
7. **What should the physical entity be called?** `PipingLine` — the
   line-number-level object, matching the engineer's "line" and line-list
   terminology. DEXPI's `PipingNetworkSystem` is the interoperable analogue but
   is exchange/ISO-15926 flavoured; map it in the adapter. (Considered names and
   why: `Pipe` is the elementary run, not the line [S3]; `Pipeline` implies a
   long-distance transport artifact; `PipingNetwork` implies a multi-line
   system; `Segment` is below line level.)
8. **Port vs Nozzle?** `Port` remains the canonical semantic connection point.
   A nozzle is physical hardware detail (subtag, size/rating) that attaches to
   an equipment port; no class or inheritance is introduced now. In DEXPI the
   Nozzle sits between equipment and piping and owns the connection nodes —
   DeepPlant can express the same boundary by giving a piping line segment an
   endpoint at an equipment port that later carries nozzle metadata [S3].
9. **Inline valves/components?** They are components-with-ports (nodes) inside
   the physical layer — never edges and never streams. DEXPI (`PipingComponent`,
   fittings) and simulators (valve unit ops) agree [S3][S5][S6]. They enter the
   model when the physical layer ships; until then `Equipment` must not be
   abused as the home for valves.
10. **Smallest next model change justified by the evidence?** Add one top-level
    entity, `ProcessStream` (`source`/`target` `PortRef`, same reference rules
    as `Connection`, own identity and optional `name`/`phase` descriptor), while
    leaving `Connection` untouched. This unlocks process/PFD semantics for a
    realistic fragment (numbered streams, branches as separate streams, recycle
    loops, stream-table-ready objects) without inventing physical-piping
    machinery that belongs to a later increment.

### Why process first, then physical?

- The PFD/process view is the earlier, higher-abstraction deliverable in
  DeepPlant's roadmap, and the open question is explicitly about
  "pipes/streams".
- Process semantics are **required by both** simulators (stream state) and PFD
  (stream tables); physical piping is required by P&ID and DEXPI, which arrive
  later in the roadmap (renderer → DEXPI spike).
- `ProcessStream` is a smaller, flatter entity than a piping layer (line +
  segments + components + breaks) and can be validated with the existing
  reference machinery unchanged.
- Adding `ProcessStream` first does **not** paint DeepPlant into a corner: the
  physical layer later references the same ports and connections, so the two
  layers compose rather than conflict.

### Proposed incremental sequence (after human approval of this proposal)

1. **Increment 1 (process/PFD):** add `ProcessStream` as a top-level entity;
   validate references exactly like `Connection`; extend the CLI counts and the
   example only as far as a real fragment requires. Do not touch `Connection`.
2. **Increment 2 (physical/P&ID):** add `PipingLine` with line-number-level
   attributes; decide then — with a real P&ID fragment and a DEXPI sample in
   hand — whether `PipingSegment` and inline components are needed immediately
   or can follow.
3. **Increment 3 (later):** inline components as components-with-ports; optional
   nozzle metadata on equipment ports; instrument-function references for
   control valves. Each of these is a separate decision with its own ADR.

## Illustrative YAML

> The snippets below are **proposed / illustrative — not canonical and not
> implemented**. They exist only to show what the recommended semantics would
> look like in DeepPlant YAML. `examples/minimal-process/plant.yaml` is not
> modified by this spike.

### Current shape (unchanged today)

```yaml
plant:
  id: demo
  name: Minimal Process

equipment:
  - id: T-101
    type: tank
    ports: [{ id: outlet }]
  - id: P-101
    type: pump
    ports: [{ id: suction }, { id: discharge }]

connections:
  - source: { component: T-101, port: outlet }
    target: { component: P-101, port: suction }
```

### Proposed Increment 1 shape (illustrative): process layer over the fragment

```yaml
# illustrative only — NOT implemented schema
plant:
  id: frag
  name: Feed / Reactor Fragment

equipment:
  - id: T-101
    type: tank
    ports: [{ id: outlet }]
  - id: P-101
    type: pump
    ports: [{ id: suction }, { id: discharge }]
  - id: E-101
    type: heat-exchanger
    ports: [{ id: tube_in }, { id: tube_out }]
  - id: V-101
    type: vessel
    ports: [{ id: inlet }, { id: outlet }]

# adjacency: unchanged concept — pure topology between ports
connections:
  - source: { component: T-101, port: outlet }
    target: { component: P-101, port: suction }
  - source: { component: P-101, port: discharge }
    target: { component: E-101, port: tube_in }
  - source: { component: E-101, port: tube_out }
    target: { component: V-101, port: inlet }

# proposed: process layer — each numbered process stream is one object;
# branches and recycle are separate streams, not edges with properties.
process_streams:
  - id: S-1
    name: Feed to pump
    source: { component: T-101, port: outlet }
    target: { component: P-101, port: suction }
  - id: S-2
    name: Pump discharge to exchanger
    source: { component: P-101, port: discharge }
    target: { component: E-101, port: tube_in }
  - id: S-2A
    name: Branch to other destination
    source: { component: E-101, port: tube_out }
    target: { component: D-201, port: inlet }        # separate branch identity
  - id: S-3
    name: Main feed to vessel
    source: { component: E-101, port: tube_out }
    target: { component: V-101, port: inlet }
  - id: S-4
    name: Recycle to pump suction
    source: { component: V-101, port: outlet }
    target: { component: P-101, port: suction }       # merge at suction port
```

Notes: the control valve, reducers, tees, nozzles and spec break are **absent
at this layer on purpose**; they belong to the physical layer. The recycle
stream and the feed stream both target `P-101.suction` — a merge by shared port,
mirroring how a PFD draws two arrows into one inlet.

### Proposed Increment 2 shape (illustrative): physical layer sketch

```yaml
# illustrative only — NOT implemented schema (future physical layer)
piping_lines:
  - id: PL-1
    line_number: '3"-PL-101-1234-A1'
    size: DN80
    piping_class: A
    fluid: feed
    # ordered realization between equipment ports; inline components and
    # spec breaks become segment boundaries here, not new process streams.
    segments:
      - from: { component: T-101, port: outlet }      # future nozzle N1 metadata
        to:   { component: P-101, port: suction }
      - from: { component: P-101, port: discharge }
        to:   { component: E-101, port: tube_in }
        via:  [ { component: FV-101, type: control-valve } ]  # inline device
        spec_break_at: [ { size: DN50, piping_class: B } ]
```

This sketch is intentionally rough; the exact shape (segments vs a flat
component list, how `spec_break_at` and `via` are expressed) is exactly what
Increment 2 must decide with a real fragment and DEXPI sample. It is shown only
to prove that the physical layer stays separate from `connections` and
`process_streams`.

## Rejected / Deferred Alternatives

Why each major option was considered and why it is not recommended now — so the
question does not get reopened without context:

- **Option A — `Connection` becomes the physical/process object.** Considered
  because it is the smallest diff to the shipped model. Rejected because one
  engineering adjacency cannot simultaneously be a state-carrying process stream
  and a physical line with spec/insulation; DEXPI and simulators both separate
  these [S3][S6]. Reconsider only if a future vertical slice proves that the
  topology, process, and physical layers never diverge for any real fragment —
  unlikely given the evidence.
- **Option E — everything is a component with ports.** Considered for
  uniformity and simple rendering. Rejected as *the* model because physical pipe
  is edge-like in DEXPI and engineering practice, because line identity gets
  buried, and because pyDEXPI must collapse such internals to reach a process
  topology [S3][S5]. Reconsider as an *internal graph convenience* (a derived
  NetworkX-like view) if renderers need uniform traversal — as a derivation, not
  as the canonical shape.
- **Ship only Option B (`ProcessStream`) forever / defer physical piping
  indefinitely.** Not chosen as an end-state: the realistic fragment contains
  line identity, inline components, and spec breaks that only a physical layer
  can express. B is chosen as the *first increment*, not the final model.
- **Adopt DEXPI terminology directly (`PipingNetworkSystem`,
  `PipingNetworkSegment`, `PipingComponent`, …).** Considered because DEXPI is
  authoritative and its distinctions are correct. Rejected for the canonical
  model because DEXPI's vocabulary and granularity are shaped by ISO-15926-style
  reference-data exchange; DeepPlant's canonical model should use smaller,
  engineer-first names (`PipingLine`, later `PipingSegment`) and map to DEXPI in
  the adapter. Reconsider only if an actual DEXPI adapter proves the mapping cost
  is worse than adopting the vocabulary outright.
- **Introduce `Nozzle`/`PipingNode`/`ProcessStep`/`Port` subtyping now.**
  Deferred: today's `Port` plus endpoint refs covers the topology and process
  layers; nozzle and process-step semantics are only needed at the P&ID/physical
  and simulation boundaries respectively.
- **Give `Connection` an id now.** Deferred until a higher layer needs to
  reference specific adjacencies (route membership). Endpoint pairs are the
  identity today.
- **Model stream thermo state now (T/P/flow/composition).** Deferred: it
  requires a deliberate quantity/unit/property-source decision (a future
  property model) and is not needed to decide topology. The DEXPI and DWSIM
  stream-state evidence is recorded above so that decision can be made
  deliberately later [S2][S4][S6].

## Open Questions

Unresolved questions that this spike intentionally does not decide:

1. **Property/quantity model.** How to represent quantities (temperature,
   pressure, flow, composition) with units, data source, and design/operating
   status on `ProcessStream` and later on piping design conditions. DEXPI uses
   `QualifiedValue`/`PhysicalQuantity`; DWSIM has its own unit system. DeepPlant
   needs its own deliberate decision (units-as-strings vs typed quantities;
   SI-only vs multi-unit).
2. **`id` vs `tag` vs `name`.** When engineering tags become first-class, how do
   stable semantic ids, derived/validated tags (equipment tag, line number,
   stream number, nozzle subtag), and human names relate? This spike records the
   distinction but changes nothing.
3. **Stream identity across a pump/valve/exchanger.** PFD convention says a
   state-changing boundary redefines the stream; simulators enforce it. Should
   DeepPlant validation ever *require* a stream boundary at each equipment item,
   or only warn? (Unanswered here; needs a PFD-authoring workflow.)
4. **Merge/branch junctions without equipment.** The recycle merges at a tee in
   the suction line, not at an equipment port. Increment 1 models this as two
   streams sharing one pump-suction port. Is a future process-level "junction"
   needed for PFDs that draw mid-line merges, or is shared-port merging always
   sufficient? Deferred until a real PFD fragment proves otherwise.
5. **Control-valve dual identity.** A control valve is one physical item plus
   one instrument function (`FV-1234`). How to represent that in Increment 3.
6. **PipingLine scope.** Does one line number ever contain parallel/disconnected
   branches that force DeepPlant to split `PipingLine` into multiple objects?
   DEXPI's `PipingNetworkSystem` wording ("interconnected piping network
   branches") hints at the question; answer with real line-list data in
   Increment 2.
7. **Process stream ↔ piping line traceability.** Should a `ProcessStream`
   later reference its realizing `PipingLine`/segments explicitly (traceability
   for PFD↔P&ID consistency checks), or is shared-port topology enough? This is
   the natural follow-up decision once both layers exist.

## Sources

Primary sources used in this research (accessed 2026-09-08). Claims are
paraphrased; no long copyrighted passages are reproduced.

- **[S1] DEXPI e.V. — official website and Specifications page.**
  Organization: DEXPI e.V. URLs: https://dexpi.org/ and
  https://dexpi.org/specifications/. Supports: DEXPI scope and focus on
  intelligent P&ID exchange; public specification family (P&ID 1.4, Process 1.0,
  combined 2.0 covering BFD/PFD/P&ID); DEXPI XML from 2.0; CC licensing; source
  of truth on GitLab; member/vendor mission statements (AVEVA, Siemens).
- **[S2] DEXPI Process Specification 1.0 — Information Model (PDF).**
  URL: https://dexpi.org/wp-content/uploads/2020/09/DEXPI-Process-1.0-Information-Model.pdf.
  Supports: process-model classes (`ProcessStep`, `Port`, `ProcessConnection`,
  `Stream`) and `Stream` composition: `MassFlow`, `Pressure`, `Temperature`,
  `VolumeFlow`, with `MaterialState`/`MaterialTemplate` references.
- **[S3] DEXPI P&ID Specification 1.4 (PDF).** URL:
  https://dexpi.org/wp-content/uploads/2024/12/DEXPI_PID_Specification_1.4.pdf.
  Supports: plant-model class definitions and attributes — `Equipment`,
  `Nozzle`/`NozzleOwner`/`ProcessNozzle`, `PipingNetworkSystem` (line number,
  spec class, fluid code, insulation, tracing; "fluid system of interconnected
  piping network branches limited by Unit Operation Inlet/Outlet and Piping
  Network Terminators"), `PipingNetworkSegment` (segment/branch definition,
  composes connections and items), `PipingConnection` (abstract) with `Pipe` and
  `DirectPipingConnection` subtypes, `PipingNode`, `PipingComponent`/
  `PipeFitting`/`PipeReducer`/`PipeTee`, `PropertyBreak`,
  `PipeOffPageConnector`, `ProcessInstrumentationFunction`.
- **[S4] DEXPI Specification 2.0 (PDF).** URL:
  https://dexpi.org/wp-content/uploads/2025/10/DEXPI_Specification_2.0.pdf.
  Supports: ISO 15926 basis; combined process model (BFD/PFD) and plant model
  (P&ID) in one specification; exchange of simulation results including stream
  tables; DEXPI XML; process classes `ProcessStep`, `ProcessConnection`,
  `Port`/`MaterialPort`; `MaterialState` ("contains the properties for a
  Stream… one for the total properties and then one for each of the phases"),
  `MaterialTemplate` (thermo-model structure; stream-table legend for a PFD),
  and `Stream` composition/state attributes.
- **[S5] pyDEXPI repository (Process Intelligence Research).** URL:
  https://github.com/process-intelligence-research/pyDEXPI (files:
  `README.md`, `pydexpi/dexpi_classes/pydantic_classes.py`,
  `pydexpi/loaders/graph_loader.py`, `pydexpi/toolkits/piping_toolkit.py`).
  Supports: Pydantic implementation of the DEXPI data model (DEXPI 1.3), Proteus
  XML import, NetworkX graph conversion, `GraphAbstractor`
  (`build_process_graph`, `build_conceptual_graph` collapsing piping into
  process topology), and the code-level shapes of all classes cited. License:
  AGPL-3.0.
- **[S6] DWSIM source repository.** URL:
  https://github.com/DanWBR/dwsim (branch `windows`; files
  `DWSIM.Interfaces/IMaterialStream.vb`,
  `DWSIM.Thermodynamics/MaterialStream/MaterialStream.vb`,
  `DWSIM.UnitOperations/UnitOperations/Pipe.vb`). Supports: `MaterialStream`
  categorized as a Stream implementing CAPE-OPEN material interfaces
  (`ICapeThermoMaterial…`) with phases/composition/T/P/flows/enthalpy and
  property package; `Pipe` as a unit operation (pressure changer) with
  length/hydraulic/heat-transfer calculation. License: GPLv3.
- **[S7] DWSIM official website.** URL: https://dwsim.org/. Supports: DWSIM
  positioning (steady-state and dynamic flowsheet simulation; CAPE-OPEN
  compliance; unit operations including pipes with hydraulic/heat-transfer
  calculations; extended "Pipe Network" operation).
- **[S8] DEXPI GitLab — `dexpi/Specification`.** URL:
  https://gitlab.com/dexpi/Specification. Supports: public source of truth for
  DEXPI specification development and legacy versions.
- **[S9] CO-LaN — the CAPE-OPEN Laboratories Network.** URL:
  https://www.colan.org/. Supports: management and stewardship of the CAPE-OPEN
  standard (interfaces allowing CAPE applications/components to interoperate);
  used only for background terminology, not for interface-level claims.
- **[S10] AVEVA — AVEVA Unified Engineering product page.** URL:
  https://www.aveva.com/en/products/aveva-engineering/. Supports: public
  positioning of AVEVA Unified Engineering as a data-centric environment where
  teams collaborate on the same data set across disciplines and phases (1D/2D/3D).
  No internal data-model claims are made from this source.

Items marked **unverified / hypothesis** in the body above are explicitly not
backed by the cited sources and are flagged as such in context.

---

> **Decision status: proposed — requires human review before implementation.**
> No semantic-model implementation is included in this change.

