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

> Decision status: **proposed — requires human architectural review before implementation.**

This is a documentation-only research spike. It proposes no schema, production
code, example-file change, dependency, or ADR. DEXPI remains an adapter/external
representation, not the DeepPlant domain model.

## Preserved findings

The following findings remain accepted:

```text
Connection
= directed, property-free topology primitive

Process semantics != physical piping semantics

ProcessStream != PipingLine
Connection != ProcessStream != PipingLine
```

There is no physical-piping implementation, stream thermodynamic-property model,
`Component` hierarchy, Pydantic change, or DEXPI implementation in scope.

## Current DeepPlant model and design problem

The shipped model is deliberately small:

```text
PlantModel
├── Plant
├── Equipment[]
│   └── Port[]
└── Connection[]
    ├── source: PortRef(component, port)
    └── target: PortRef(component, port)
```

`Equipment` is a physical/equipment inventory object. `Port` is only a named
connection point owned by one `Equipment`; it declares neither process purpose
nor nozzle identity. `Connection` has no id or properties and validates only
that its equipment-owned endpoint ports exist. It records directed adjacency,
not flow, a stream, a pipe, a line, or a simulation object.

The earlier illustrative proposal authored this same endpoint relationship twice:

```text
Connection:    T-101.outlet → P-101.suction
ProcessStream: T-101.outlet → P-101.suction
```

That produces two independent connectivity representations. The governing
Engineering-as-Code invariant is:

> The canonical model should not require two independently authored facts to
> remain synchronized when one can be derived or explicitly related to the
> other.

Therefore `ProcessStream(source: PortRef, target: PortRef)` beside the current
`Connection(source: PortRef, target: PortRef)` is rejected. Equality of their
current endpoints does not make their identities or abstraction boundaries the
same; it makes the duplicate fact a synchronization liability.

## Evidence and confidence labels

- **Verified from source** means explicitly supported by a cited source.
- **Engineering inference** is a conclusion from the verified model distinctions
  and normal process-engineering meaning; it is not a claim of DEXPI compliance.
- **DeepPlant recommendation** is the proposed canonical-model decision.

### Verified source findings

DEXPI 2.0 has a distinct Process model and Plant model. Its Process model
contains `ProcessStep`, `ProcessConnection`, `Port`, concrete `MaterialPort`,
and `Stream`; its ProcessModel owns collections of ProcessSteps and
ProcessConnections. `ProcessConnection` has source and target Ports. The
specification also defines `EnergyPort` as a Port modelling transfer of energy
into or out of a ProcessStep, and defines `Mixing` and `Splitting` process
concepts. This is evidence that the standard distinguishes process functions,
process ports, and process connections from plant/P&ID constructs—not evidence
that DeepPlant should reproduce its class hierarchy. [S1]

DEXPI 2.0 describes the plant/P&ID side separately: physical equipment has
nozzles and piping nodes; piping networks, segments, pipes, fittings and tees
model physical realization. A nozzle is physical equipment hardware, whereas a
process port is a process-model boundary. [S1] pyDEXPI is useful corroboration
for the older P&ID model and graph processing only; it is not the DEXPI 2.0
Process-model authority. [S2]

DWSIM separately represents material streams and unit-operation objects. Its
material-stream interface carries phases, composition, temperature, pressure,
flow and enthalpy; its flowsheet object taxonomy separately includes Pipe,
Valve, Mixer, Splitter, Pump and HeatExchanger. [S3]

## ProcessStep versus Equipment

`ProcessStep` is a process function/boundary. Current `Equipment` is one
physical equipment item. They can coincide, but are not semantically equivalent.

| Case | Evidence and analysis | Mapping conclusion |
|---|---|---|
| A — one pump, one function | A simple PFD pump function can be realized by pump `P-101`. | A 1:1 mapping is often reasonable. |
| B — one item, several functions | A column may expose separation, condenser and reboiler functions; an exchanger has distinct process sides; a reactor may have reaction and heat-transfer functions; packaged equipment can encapsulate more than one function. DEXPI’s separate ProcessStep model makes such separation representable. | One `Equipment` may realize multiple ProcessSteps. |
| C — one function, several items | A separation, filtration, reaction, packaged, or duty/standby train can be one process function while realized through several physical items. Whether a particular PFD collapses these is an intentional abstraction decision. | One ProcessStep may map to several Equipment items. |

**Engineering inference:** physical containment/tagging and functional process
boundaries have different identity and cardinality rules. A process graph must
therefore be able to map many-to-many with physical equipment, even though many
initial examples are 1:1.

**DeepPlant recommendation:** `ProcessStep` is a separate canonical *concept*.
Do not make current `Equipment` its canonical node type. It may only serve as a
temporary realization for an approved MVP fragment under this explicit
assumption:

```text
For every process step in the approved fragment,
exactly one Equipment realizes it, and each represented Equipment realizes
exactly one process step at that selected PFD abstraction.
```

That is Outcome 3: ProcessStep is conceptually needed but its schema is deferred
until a fragment demonstrates and records the mapping. The assumption excludes,
rather than silently mishandles, multi-side exchangers, grouped systems,
internal functions and redundant trains.

## Process ports versus current Port

A process port is a logical boundary of a ProcessStep for material transfer (and
later energy or information transfer). A nozzle/PipingNode is a physical
connection point in the plant/piping realization. Neither identity implies the
other.

- A logical process boundary need not correspond to visible hardware: it may
  collapse internal equipment or a packaged system at PFD level.
- One process port can be realized through multiple nozzles/physical paths (for
  example a manifold or grouped train); one physical nozzle can participate in
  differently abstracted process boundaries. Those mappings must not be assumed
  1:1.
- Energy ports—and eventually information/control ports—make a generic
  equipment-owned material-looking `Port` particularly unsuitable as the sole
  process-port identity. DEXPI 2.0’s EnergyPort demonstrates this category is
  distinct. [S1]

### Candidate port models

| Model | Assessment |
|---|---|
| P1 — shared canonical `Port` with process meaning and later nozzle realization | Rejected. Today’s Port has equipment ownership and no process/nozzle semantics. Reusing its identity couples logical function to physical realization and makes shared-port merge shortcuts look valid. |
| P2 — `ProcessStep → ProcessPort`; `Equipment → physical Port/Nozzle`; explicit mapping | Semantically correct target. It permits zero/one/many mappings and keeps process and physical identity separate. |
| P3 — current Port as low-level anchor referenced by ProcessPort and Nozzle | Not justified now. It still presumes one universal anchor before evidence establishes what its identity means. It may be reconsidered only if a concrete mapping proves it reduces—not hides—identity relationships. |

**DeepPlant recommendation:** do not reuse current `Port` as a process port.
Keep it unchanged as today’s low-level, equipment-owned topology anchor. When a
process layer is approved, introduce a distinct `ProcessPort` owned by a
`ProcessStep`; define explicit mapping relations to current equipment/ports or
future nozzles only where the fragment requires them. Do not implement either
class in this PR.

## ProcessStream versus Connection

### Candidate topology relationships

| Alternative | Evaluation | Result |
|---|---|---|
| T1 — independent duplicated endpoints | Two endpoint facts must be edited together. The earlier proposal did not define an invariant or derivation to keep them synchronized. | Rejected. |
| T2 — ProcessStream references one Connection | Current Connection has no id. Adding identity solely to support this creates coupling too early; moreover one process stream can cross several low-level adjacencies/inline items. | Rejected for MVP. |
| T3 — ProcessStream owns/references an ordered Connection path | Requires connection IDs, ordering, branch rules, route maintenance and path edits. It leaks physical/low-level routing into the process abstraction and creates noisy Git diffs. | Deferred; only a future physical-realization use case can justify it. |
| T4 — derive process adjacency from ProcessStream | Appropriate *within a process graph*: a ProcessStream is the one authored process relation and adjacency is derived. It cannot derive physical plant topology. | Correct process-graph principle. |
| T5 — separate process graph and plant graph with explicit mapping | Preserves differing abstraction and identity rules. It is the correct target, but the mapping vocabulary must be proven on a real fragment before schema work. | Target architecture; no implementation yet. |

A ProcessStream is a process-graph edge with its own stream identity and, later,
a home for material state. It connects **ProcessPorts**, not current `PortRef`s.
It may directly store its own `source_process_port` and `target_process_port`
because that is the single canonical process connectivity fact; this does not
duplicate a Connection endpoint fact. Process adjacency is derived from the
stream. Physical realization is related by explicit mapping, not inferred from
equal endpoints.

## Split, merge, and recycle test

A binary stream is not a branch or a merge. Process-level junction semantics
must be explicit whenever material identity/state changes or the process graph
needs a balance boundary. DEXPI 2.0 explicitly contains Mixing and Splitting
concepts; DWSIM separately lists Mixer and Splitter operations. [S1][S3]

| Fragment | Process graph | Semantics owner / future balance | Junction and stream identity | Duplicate topology? |
|---|---|---|---|---|
| Simple `A → B` | `Step A —S-1→ Step B` | S-1 carries future material state; neither endpoint needs a junction. | No junction; one stream identity. | No: process relation is authored once. |
| Split `A → split → B,C` | `A —S-in→ Split —S-B→ B`; `Split —S-C→ C` | Explicit Split ProcessStep owns split semantics; balances evaluate there. | Explicit junction; each outlet is a distinct stream. | No. |
| Merge `A,B → merge → C` | `A —S-A→ Mix`; `B —S-B→ Mix`; `Mix —S-C→ C` | Explicit Mixing ProcessStep owns mixing and downstream mixed-state calculation. | Explicit junction; S-C is not either inlet stream. | No. |
| Recycle `A → B → C → A` | A cycle of distinct streams and steps. | Each unit/explicit junction owns its balance; solver strategy is later simulation scope. | Cycle is explicit; no special shared port is needed. | No. |

Several streams may legitimately terminate at the same *process port* only when
that port is expressly a multi-inlet boundary whose semantics are defined by the
owning ProcessStep. This is not an appropriate default for a pump suction.

**Recommendation:** a pump suction does not itself semantically assert mixing.
Two streams aimed at `P-101.suction` can be a PFD drawing shorthand or a physical
tee ahead of the pump, but it fails to identify where mixed state exists. Model
an explicit process Mixing step when the merge matters. Do not hide it in a
shared equipment port. The same logic requires an explicit Splitting step for a
material split. Physical tees remain P&ID/plant realization details, not a
substitute for process Mixing/Splitting semantics.

## Process, simulation, and plant topology are related views

For the same physical fragment, graphs legitimately differ:

```text
PFD abstraction
Pump ProcessStep ──S-1──> Exchanger ProcessStep

Simulation abstraction
Pump unit op ──S-1──> Valve unit op ──S-2──> Exchanger unit op

Plant / P&ID topology
Pump nozzle → piping → valve → piping → exchanger nozzle
```

A control valve may be transparent in a selected PFD, explicit in a simulation,
and an inline physical component in P&ID topology. Conversely an exchanger can
be one physical item with two process sides. These are not errors to normalize
away: they are abstraction choices requiring mappings.

**DeepPlant recommendation:** the canonical model must support related process,
simulation, and plant/physical graphs without forcing them to be one graph.
Simulation topology is not being implemented now, but it demonstrates why a
universal `Connection` graph is unsafe.

## Status of current Connection

The earlier claim that `Connection` is “the topology substrate shared by all
future layers” is withdrawn. Evidence supports C2 with a transitional caveat:

```text
Connection is current generic low-level adjacency / bootstrap topology.
A process graph may have its own canonical edges.
Its future plant/physical role remains to be proven by a real P&ID slice.
```

Thus Connection is **not universal**. It is useful and should not be deleted:
it already provides reference validation for today’s equipment-owned ports. Its
long-term refinement is deliberately open (C2/C3), not decided by its existence.

## Mapping example

This conceptual fragment makes the non-duplication boundary visible:

```text
PROCESS LAYER (selected PFD abstraction)

Feed ProcessStep ──S-feed──> Mixing ProcessStep ──S-suction──> Pump ProcessStep
Recycle source ──S-recycle──> Mixing ProcessStep
Pump ProcessStep ──S-discharge──> Exchanger ProcessStep
```

```text
PLANT / PHYSICAL TOPOLOGY (future, illustrative)

T-101.outlet ─ Connection ─ tee / suction piping ─ Connection ─ P-101.suction
V-101.outlet ─ Connection ─ tee / suction piping
P-101.discharge ─ Connection ─ FV-101 ─ Connection ─ E-101.nozzle
```

```text
MAPPINGS (illustrative relations, not a schema)

Feed ProcessStep          ↔ T-101 Equipment
Pump ProcessStep          ↔ P-101 Equipment
Exchanger ProcessStep     ↔ E-101 Equipment (one selected process side)
Mixing ProcessStep        ↔ physical tee/suction-piping realization (unresolved
                             until the P&ID slice; it may have no standalone Equipment)
S-discharge               ↔ realization through P-101 discharge nozzle,
                             FV-101 and piping, to E-101 inlet nozzle
ProcessPort(pump.inlet)   ↔ P-101 suction nozzle/current Port only if the
                             approved fragment explicitly asserts that mapping
```

The process stream is not a duplicate of any one physical Connection; its
realization can traverse multiple physical relations. The physical tee and the
process Mixing step are related but have different identities and purposes.

## Revised recommended model

### Target conceptual shape

```text
Process graph
ProcessStep[]
└── ProcessPort[]
ProcessStream(source ProcessPort, target ProcessPort)

Plant / physical topology (current and future)
Equipment[]
└── current Port[] / future Nozzle[]
Connection[]

Mappings
ProcessStep ↔ Equipment[]
ProcessPort ↔ current Port[] / future Nozzle[]
ProcessStream ↔ physical realization (only when a concrete later use case needs it)
```

This is conceptual pseudo-model, not proposed YAML or an approved schema.

### Direct answers

1. **Is ProcessStep separate?** Yes, conceptually canonical; it is not
   semantically identical to Equipment.
2. **Temporary assumption if not implemented now?** An approved fragment may
   assume one selected ProcessStep per selected Equipment and one Equipment per
   selected ProcessStep; all non-1:1 cases are out of that MVP.
3. **Is current Port reused?** No.
4. **Why not?** Its current identity is equipment-owned generic adjacency, not a
   process boundary or physical nozzle identity.
5. **What process-port concept is required?** A distinct ProcessPort owned by a
   ProcessStep, initially MaterialProcessPort (name to be decided only at schema
   time); energy/information categories remain future extensions.
6. **Does ProcessStream directly store endpoints?** In a future process graph,
   yes: ProcessPort endpoints are its one canonical process relation.
7. **Does it reference/derive topology?** Process adjacency is derived from the
   ProcessStream. It neither references nor duplicates current Connection.
8. **What is Connection?** Current low-level adjacency/bootstrap concept, not
   universal; its later physical role is open.
9. **How are split/merge represented?** Explicit ProcessStep junctions for
   Splitting/Mixing, with distinct inbound/outbound streams; never implicit
   shared equipment ports.
10. **Smallest non-duplicating implementation?** None is approved yet.

### Smallest next increment

The evidence is insufficient to implement `ProcessStream` safely today. First
model one real, reviewable PFD fragment as a documentation/prototyping exercise
with explicit ProcessSteps, ProcessPorts, ProcessStreams, a split or merge, a
recycle where relevant, and stated mappings to the current equipment/port graph.
Human review must decide its abstraction boundary and the mapping cardinalities.
Only then may the roadmap name a concrete vertical code slice. This protects the
semantic model from both duplicate connectivity and premature identity coupling.

## Illustrative pseudo-model (not YAML)

Detailed YAML is intentionally removed. A YAML shape would falsely imply that
field names, IDs, ownership, mapping cardinalities, and validation rules have
been approved. The conceptual pseudo-model above is the appropriate outcome of
this research stage.

## Rejected and deferred conclusions

- Do not add `ProcessStream(source: PortRef, target: PortRef)` beside
  `Connection`; this is T1 duplication.
- Do not say “Nozzle is metadata attached to Port.” A nozzle may eventually map
  to a current Port, but the mapping/identity has not been established.
- Do not represent process branches or merges by shared equipment ports.
- Do not make `Connection` a universal substrate by assumption.
- Do not add process, physical piping, simulation, or generic component classes
  until the approved real fragment demonstrates the smallest necessary slice.

## Roadmap consequence

The next roadmap action is human-decision-gated review and approval of this
revised process-layer model, including ProcessStep/Equipment, ProcessPort/current
Port, ProcessStream/Connection, explicit junctions, and mapping cardinalities.
No implementation increment is named by this research.

## Sources

- **[S1] DEXPI e.V., _DEXPI Specification_, Release 2.0.0 (10 October 2025),
  Chapter 3 “Models”, Process model entries including `ProcessStep`,
  `ProcessConnection`, `MaterialPort`, `EnergyPort`, `Mixing`, `Splitting`, and
  `Stream`; plant/P&ID entries for nozzles, piping nodes, piping networks and
  fittings. https://dexpi.org/wp-content/uploads/2025/10/DEXPI_Specification_2.0.pdf
  (primary source; accessed 2026-09-08).
- **[S2] process-intelligence-research/pyDEXPI**, P&ID 1.3/1.4 Pydantic model
  and graph loader. It represents DEXPI plant-model objects and graph
  abstractions; it is corroborative, not the DEXPI 2.0 Process-model authority.
  https://github.com/process-intelligence-research/pyDEXPI (accessed 2026-09-08).
- **[S3] DWSIM source**, `DWSIM.Interfaces/IMaterialStream.vb` and
  `DWSIM.Interfaces/Enums.vb`, `windows` branch. The former defines material
  stream phases, composition, T/P, flows and enthalpy; the latter separately
  enumerates MaterialStream, Pipe, Valve, Mixer, Splitter and unit operations.
  https://github.com/DanWBR/dwsim (accessed 2026-09-08).

---

> Decision status: **proposed — requires human architectural review before
> implementation.** No semantic-model implementation is included in this change.
