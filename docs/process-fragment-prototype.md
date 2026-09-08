---
type: research
status: proposed
source_of_truth_for:
  - process-fragment-prototype
read_when:
  - process-model-implementation
  - pfd-modeling
update_when:
  - process-model-decision
---

# Process Fragment Prototype

> Decision status: **proposed — requires human architectural review before
> implementation.**

Documentation-only modeling prototype. No production semantic-model class, no
Pydantic change, no YAML schema, no ADR, no dependency, and no
`src/` / `tests/` / `examples/` modification is included in this change.

## Purpose

Stress-test the proposed process-layer architecture in
[process-topology.md](process-topology.md) on **one concrete, realistic PFD
fragment**:

```text
Process graph
ProcessStep
└── ProcessPort

ProcessStream
    source ProcessPort
    target ProcessPort

Plant / physical topology
Equipment
└── current Port / future Nozzle

Connection

Mappings
ProcessStep   ↔ Equipment / physical realization
ProcessPort   ↔ physical connection points where meaningful
ProcessStream ↔ physical realization only when needed
```

This prototype is **not meant to prove** that the architecture is correct. It
is meant to **try to break it** with a real engineering example, so a human
reviewer can decide whether the proposed process model is mature enough for its
first production implementation slice.

All identifiers below (`PS-*`, `S-0xx`) are **prototype-only labels** for this
exercise. They do not decide the final DeepPlant stream-numbering, tagging, or
naming standard.

## Selected PFD Abstraction

One deliberate PFD view of the physical arrangement is modeled. The abstraction
is stated explicitly so that nothing is silently omitted.

Represented as ProcessSteps at this abstraction:

- feed storage (`T-101`; acts as a source boundary in this fragment)
- mixing of fresh feed with recycle
- pumping
- heat exchange — one selected process side only
- splitting into a vessel feed and a branch
- vessel / process function (`V-101`)
- downstream-consumer black box (fragment boundary)

Not represented as ProcessSteps at this abstraction — and why:

| Omitted physical object | Reason (abstraction rule) |
|---|---|
| `FV-101` control valve | inline regulation hardware; transparent at this PFD abstraction (rule A2) |
| reducers, elbows, fittings, flanges, supports | pipe detail, not a PFD process function (rule A2) |
| physical tees at the mixing point and at the split | hardware realization of the Mixing / Splitting *function*, which is itself represented as a step (rules A1, A2) |
| equipment nozzle hardware | physical connection detail (rule A2) |
| `E-101` second (utility / other-process) side | not a material stream of this fragment (rule A3) |
| instruments, control loops, utilities, energy streams | not material streams (rule A3) |
| internals of the downstream consumer | lie beyond the fragment boundary (rule A4) |

Stated abstraction rules:

- **A1** — Process functions that store, move, transform, mix, or split
  material and appear as intentional PFD blocks are ProcessSteps.
- **A2** — Inline regulation hardware (`FV-101`), reducers, fittings, physical
  tees, and nozzle hardware are physical-realization detail, not ProcessSteps
  at this abstraction.
- **A3** — Only material streams are modeled. Energy, utility, and control
  flows are out of scope.
- **A4** — The downstream consumer is a black-box ProcessStep; its internals
  lie beyond the fragment.
- **A5** — `V-101` has exactly one modeled material outlet in the given
  scenario: the recycle stream. No additional vessel outlet is invented.
- **A6** — Piping runs between items are not enumerated as streams or steps;
  one ProcessStream may span several physical piping segments.
- **A7** — `E-101` is represented by its modeled process side only; that side
  has one inlet and one outlet ProcessPort.

## Physical Scenario

The physical/process scenario, as given:

```text
A feed liquid is stored in T-101 Feed Tank.
It mixes with a recycle stream.
The mixed stream enters P-101 Feed Pump.
The pump sends the liquid through FV-101 Control Valve, then through one
process side of E-101 Heat Exchanger.
The heated/cooled stream is then split:
    main stream → V-101 Process Vessel
    branch      → another downstream consumer
A stream from V-101 is recycled back to the pump-suction mixing point.
```

**Scenario note (recorded, not resolved):** the fragment as stated gives
`V-101` only one modeled outlet — the recycle stream. Whether `V-101` also has
a net product, vent, or drain outlet in the real unit is unstated. This
prototype reproduces the fragment as given (rule A5) and does not invent
additional vessel outlets. That under-specification belongs to the source
scenario, not to the process model under test.

```text
                                      ┌──→ downstream consumer
                                      │
T-101 ──→ MIX ──→ P-101 ──→ E-101 ──→ SPLIT ──→ V-101
          ↑                                      │
          └──────────── recycle ─────────────────┘
```

## Process Graph

The process graph is the set of ProcessStep nodes, ProcessPort boundaries, and
directed ProcessStream edges below. It is a **process / PFD abstraction** of
the physical arrangement, not a copy of the equipment graph.

```text
PS-feed ──S-001──> PS-mix ──S-003──> PS-pump ──S-004──> PS-hx ──S-005──> PS-split
                   ▲                                            │
                   │                                            ├──S-006──> PS-vessel
              S-002│                                            │           │
                   │                                            └──S-007──> PS-consumer
                   │                                            ▲           │
                   └───── S-002 recycle (PS-vessel.out_recycle) ┘           │
                                                                             │
                          (graph edge list in Process Streams)               │
```

Readable edge list (one semantic fact per stream; this is the granularity that
appears in a Git diff):

```text
S-001  fresh feed     PS-feed.out_feed           → PS-mix.in_fresh
S-002  recycle        PS-vessel.out_recycle      → PS-mix.in_recycle
S-003  mixed feed     PS-mix.out_mixed           → PS-pump.suction
S-004  discharge      PS-pump.discharge          → PS-hx.in_side_A
S-005  to split       PS-hx.out_side_A           → PS-split.in
S-006  vessel feed    PS-split.out_vessel        → PS-vessel.in
S-007  branch         PS-split.out_branch        → PS-consumer.in
```

The only directed cycle is the recycle loop
`PS-mix → PS-pump → PS-hx → PS-split → PS-vessel → PS-mix` formed by `S-002`.

## Process Steps

Concrete prototype instances:

| ProcessStep | Type / role | Inputs | Outputs | Physical realization |
|---|---|---|---|---|
| `PS-feed` | feed storage (source boundary in this fragment) | — | `out_feed` | `T-101` |
| `PS-mix` | mixing | `in_fresh`, `in_recycle` | `out_mixed` | no standalone Equipment; physical suction tee / piping arrangement |
| `PS-pump` | pumping | `suction` | `discharge` | `P-101` |
| `PS-hx` | heat exchange — modeled process side only | `in_side_A` | `out_side_A` | `E-101` (one selected side; side B not modeled) |
| `PS-split` | splitting | `in` | `out_vessel`, `out_branch` | no standalone Equipment; physical tee / piping arrangement |
| `PS-vessel` | vessel / process function | `in` | `out_recycle` | `V-101` |
| `PS-consumer` | downstream-consumer black box (sink boundary) | `in` | — | none — beyond fragment |

Notes:

- `PS-feed` is a **source boundary** only because the supply upstream of
  `T-101` is outside the fragment. Being a boundary is a property of the
  fragment scope, not an intrinsic property of the storage function.
- `PS-consumer` is a **sink boundary**; its single input absorbs `S-007`.
- The valve `FV-101`, all piping, and all nozzle hardware are intentionally
  absent as steps (rules A2, A6).

## Process Ports

Every ProcessPort is owned by exactly one ProcessStep. Port ids are local to
the owning step (prototype convention). The derived role column follows only
from the incident ProcessStreams; no direction field is authored.

| ProcessPort (prototype) | Owning step | Derived role | Incident ProcessStreams |
|---|---|---|---|
| `PS-feed.out_feed` | `PS-feed` | output | `S-001` |
| `PS-mix.in_fresh` | `PS-mix` | input | `S-001` |
| `PS-mix.in_recycle` | `PS-mix` | input | `S-002` |
| `PS-mix.out_mixed` | `PS-mix` | output | `S-003` |
| `PS-pump.suction` | `PS-pump` | input | `S-003` |
| `PS-pump.discharge` | `PS-pump` | output | `S-004` |
| `PS-hx.in_side_A` | `PS-hx` | input | `S-004` |
| `PS-hx.out_side_A` | `PS-hx` | output | `S-005` |
| `PS-split.in` | `PS-split` | input | `S-005` |
| `PS-split.out_vessel` | `PS-split` | output | `S-006` |
| `PS-split.out_branch` | `PS-split` | output | `S-007` |
| `PS-vessel.in` | `PS-vessel` | input | `S-006` |
| `PS-vessel.out_recycle` | `PS-vessel` | output | `S-002` |
| `PS-consumer.in` | `PS-consumer` | input | `S-007` |

All 14 ports are used exactly once, so role derivation is unambiguous here.
Boundary roles (source vs sink) are a fragment-scope property of whole steps,
not of a per-port direction flag.

## Process Streams

Prototype stream inventory. No thermodynamic values are attached; `id`,
`name`, source, and target are the only recorded facts.

| Prototype id | Source ProcessPort | Target ProcessPort | Human meaning | Role in fragment | Physical route (conceptual) |
|---|---|---|---|---|---|
| `S-001` | `PS-feed.out_feed` | `PS-mix.in_fresh` | fresh feed to mixing point | fresh feed | `T-101` outlet nozzle → suction-mix tee (one route, several segments) |
| `S-002` | `PS-vessel.out_recycle` | `PS-mix.in_recycle` | recycle to pump-suction mixing point | recycle | `V-101` recycle nozzle → suction-mix tee |
| `S-003` | `PS-mix.out_mixed` | `PS-pump.suction` | mixed feed to pump suction | mixed feed / suction | suction-mix tee → `P-101` suction nozzle |
| `S-004` | `PS-pump.discharge` | `PS-hx.in_side_A` | pump discharge to exchanger | discharge | `P-101` discharge nozzle → piping → `FV-101` (transparent) → piping → `E-101` side-A inlet nozzle (one stream spans several segments and one transparent inline item) |
| `S-005` | `PS-hx.out_side_A` | `PS-split.in` | exchanger outlet to split | hx outlet / split feed | `E-101` side-A outlet nozzle → split tee |
| `S-006` | `PS-split.out_vessel` | `PS-vessel.in` | vessel feed | vessel feed (split main) | split tee → `V-101` inlet nozzle |
| `S-007` | `PS-split.out_branch` | `PS-consumer.in` | branch to downstream consumer | branch (split side draw) | split tee → fragment boundary (beyond boundary: unresolved) |

Every stream has exactly one semantic source and one semantic target. Stream
endpoints are ProcessPorts of ProcessSteps — never equipment ports and never
current `Connection` objects.

## Mixing / Splitting

### Mixing

```text
fresh feed ─┐
            ├→ Mixing (PS-mix) → mixed feed
recycle ────┘
```

- **Does Mixing need its own ProcessStep?** Yes, at this abstraction. The
  merge is real in the PFD (fresh feed and recycle converge before the pump),
  it changes material identity (`S-003` mixed feed is neither `S-001` fresh
  feed nor `S-002` recycle), and a future mass balance needs a conservation
  node. The only way to express the merge without a step would be to let
  several ProcessStreams share one target port or to author multi-source
  streams — both are the shared-port / hidden-merge shortcuts that
  [process-topology.md](process-topology.md) already rejected. ProcessStream is
  binary (one source, one target), so a merge needs an explicit node.
- **How many ProcessPorts does it own?** Three: `in_fresh`, `in_recycle`,
  `out_mixed`.
- **Which ProcessStreams enter and leave?** Enter: `S-001` (fresh),
  `S-002` (recycle). Leave: `S-003` (mixed).
- **Where would a future mass balance live?** On `PS-mix`
  (`ṁ_fresh + ṁ_recycle = ṁ_mixed`), with material state carried by the three
  streams. The mixing rule (composition/enthalpy) is step-level engineering
  semantics, not stream topology.

### Splitting

```text
               ┌→ branch stream (S-007 → downstream consumer)
main flow → Split (PS-split)
               └→ vessel stream (S-006 → V-101)
```

- **Does Splitting need its own ProcessStep?** Yes, for the mirror-image
  reasons. The split is real in the PFD, `S-006` and `S-007` are distinct
  streams with distinct meanings, and a future balance needs a node. Without a
  step the two outlets would have to be expressed as multi-target streams or a
  shared source port — both rejected shortcuts.
- **How many ProcessPorts does it own?** Three: `in`, `out_vessel`,
  `out_branch`.
- **Which ProcessStreams enter and leave?** Enter: `S-005`. Leave: `S-006`
  (vessel feed), `S-007` (branch).
- **Where would a future mass balance live?** On `PS-split`
  (`ṁ_in = ṁ_vessel + ṁ_branch`); the branch ratio is step-level engineering
  data.

### Junction findings

- A process branch or merge is **not** hidden inside shared physical/equipment
  ports: `PS-mix` and `PS-split` own their junction ports, and each branch or
  inlet is a distinct port with a distinct stream.
- Junction steps are process functions with **no standalone Equipment**. The
  model only survives this if a ProcessStep may exist with zero physical
  equipment realization (see Process ↔ Physical Mapping).
- Step `type` values `mixing` and `splitting` are sufficient to express the
  junction semantics in this fragment; no junction subclass is needed (see
  Recommended First Code Slice).

## Recycle

The recycle is a genuine directed graph cycle:

```text
PS-mix → PS-pump → PS-hx → PS-split → PS-vessel
   ▲                                        │
   └──────────── S-002 recycle ─────────────┘
```

Checks against the proposed model:

- **ProcessStream identity remains clear.** `S-002` is an ordinary stream with
  its own prototype id, source `PS-vessel.out_recycle`, and target
  `PS-mix.in_recycle`. Nothing about its identity or class differs from the
  once-through streams.
- **Every stream has exactly one semantic source and target.** Yes: all seven
  streams, including `S-002`, are single-source / single-target edges.
- **No special-case recycle concept is required.** No shared port, no extra
  edge type, no cycle flag. The recycle is visible because `S-002` is a row in
  the stream inventory and an edge in the graph.
- **Git-diff readability.** In the authoring shape above, every stream is one
  edge/row, so a topology change is a small diff. For example, deleting the
  recycle is one removed line:

```diff
  S-001  fresh feed     PS-feed.out_feed           → PS-mix.in_fresh
- S-002  recycle        PS-vessel.out_recycle      → PS-mix.in_recycle
  S-003  mixed feed     PS-mix.out_mixed           → PS-pump.suction
```

  Deterministic diff readability also requires a stable authoring order (see
  Model Failures / Ambiguities), which is a serialization concern, not a
  semantic one.

No simulation-convergence concept (tearing, iteration, stream ordering for
solvers) is introduced anywhere in this prototype.

## Process ↔ Physical Mapping

### ProcessStep → Equipment

| Mapping case | Prototype instances | Result |
|---|---|---|
| **A — 1 ProcessStep ↔ 1 Equipment** | `PS-feed ↔ T-101`; `PS-pump ↔ P-101`; `PS-vessel ↔ V-101`; `PS-hx ↔ E-101` (for the selected process side only) | 1:1, high confidence |
| **B — ProcessStep with no standalone Equipment** | `PS-mix ↔ physical suction tee / piping arrangement`; `PS-split ↔ physical tee / piping arrangement` | no Equipment tag; realized by piping. The model handles this only because ProcessStep may exist with zero Equipment. |
| **C — physical Equipment not represented as a ProcessStep** | `FV-101` exists physically (between `P-101` and `E-101` in the P&ID) but is **transparent at this PFD abstraction** | Equipment → 0 ProcessSteps |

Case C is shown explicitly:

```text
FV-101 exists physically (inline control valve in the P&ID)
but is transparent at this PFD abstraction:

PROCESS:  PS-pump ──S-004──> PS-hx        (one ProcessStream)
PHYSICAL: P-101.discharge → piping → FV-101 → piping → E-101 side-A inlet
```

This tests `process graph != physical graph`: the process graph has one edge
where the physical graph has one inline item plus piping, and neither graph is
a subset of the other at the same granularity.

**Consequence for the earlier MVP assumption:** the temporary assumption
recorded in [process-topology.md](process-topology.md) — *for every process
step exactly one Equipment realizes it, and every represented Equipment
realizes exactly one process step* — **does not hold for this fragment**.
`PS-mix` and `PS-split` are real process functions realized by no standalone
Equipment, and `FV-101` is real Equipment realizing no ProcessStep. A first
production slice therefore cannot treat Equipment as a temporary stand-in for
ProcessStep, even in an MVP fragment that contains junctions and a transparent
inline valve.

### ProcessStream is not a Connection

The process relation and the physical relation are shown separately on purpose:

```text
PROCESS

PS-pump.discharge
        │
        S-004
        ▼
PS-hx.in_side_A

PHYSICAL (conceptual, not implemented)

P-101.discharge  → piping → FV-101 → piping → E-101 side-A inlet
```

- `S-004` is authored once, as a ProcessStream between two **ProcessPorts**. It
  is **not** a reference to any current `Connection`, and no identical
  source/target `PortRef` pair is duplicated.
- The physical route traverses several physical segments and `FV-101`; current
  `Connection` objects (equipment port → equipment port) could at best describe
  the physical adjacency, and only if valve/piping equipment and ports were
  authored — which today's model cannot do because no valve or piping classes
  exist.
- The two graphs have different abstraction boundaries and different node
  identities; neither is derivable from the other.

### ProcessPort → physical / current Port mapping

Allowed cardinality tokens used here: `1:1`, `1:N`, `N:1`, `none`, `unresolved`
(as specified by the prototype brief).

| ProcessPort | Current / physical mapping | Cardinality | Confidence |
|---|---|---|---|
| `PS-feed.out_feed` | `T-101.outlet` current Port | 1:1 | high |
| `PS-mix.in_fresh` | none — piping branch between `T-101` outlet nozzle and suction tee | none | low |
| `PS-mix.in_recycle` | none — recycle piping meets the suction tee | none | low |
| `PS-mix.out_mixed` | unresolved — suction-piping segment before `P-101`; nearest current Port (`P-101.suction`) is already the mapping of `PS-pump.suction` | unresolved | low |
| `PS-pump.suction` | `P-101.suction` current Port | 1:1 | high |
| `PS-pump.discharge` | `P-101.discharge` current Port | 1:1 | high |
| `PS-hx.in_side_A` | `E-101` side-A inlet port / future Nozzle (not yet authored in any example) | 1:1 | medium |
| `PS-hx.out_side_A` | `E-101` side-A outlet port / future Nozzle | 1:1 | medium |
| `PS-split.in` | unresolved — piping between `E-101` side-A outlet and the split tee; nearest anchor collides with `PS-hx.out_side_A` | unresolved | low |
| `PS-split.out_vessel` | unresolved — piping to `V-101` inlet; nearest anchor collides with `PS-vessel.in` | unresolved | low |
| `PS-split.out_branch` | none / unresolved — piping toward the fragment boundary | unresolved | low |
| `PS-vessel.in` | `V-101.inlet` current Port / future Nozzle | 1:1 | high |
| `PS-vessel.out_recycle` | `V-101.recycle` outlet current Port / future Nozzle | 1:1 | high |
| `PS-consumer.in` | none — beyond the fragment boundary | none | n/a |

**Mapping finding:** equipment-adjacent process ports map cleanly 1:1 to
current equipment Ports (or future nozzles) when those physical ports exist.
Junction ports — the ports of `PS-mix` and `PS-split` — map to unmodeled
piping points, so their mapping is either `none` or `unresolved`; forcing them
onto the nearest equipment port would collide with the mapping of the adjacent
equipment-bounding port. A meaningful physical mapping for junction ports must
wait for a physical piping/nozzle layer, or be deliberately left as
documentation-only relations. This does not break the process graph itself —
it only limits what a *mapping table* can assert today.

## Heat Exchanger Stress Test

`E-101` is modeled deliberately and carefully: not as a generic two-port
object, but as **one selected process side** of a physical exchanger that has
(by construction of the fragment) a second, unmodeled side.

```text
ProcessStep PS-hx (process side A only)
    in_side_A
    out_side_A
        ↕
physical Equipment E-101
    (side A  — modeled)
    (side B  — not modeled: utility or another process stream)
```

The exchanger does **not** break the one-step / one-inlet / one-outlet shape of
this prototype, because the selected PFD abstraction deliberately includes only
one side (rule A7). That choice is recorded, not silently hidden.

**Unresolved broader question (important stress test of
`ProcessStep != Equipment`):**

> If both exchanger sides are included in one process model, should one
> Equipment map to **multiple ProcessSteps** (one per side), or should one
> ProcessStep own **multiple independent material port pairs** (side-A
> inlet/outlet and side-B inlet/outlet)?

The fragment provides evidence for the *question*, not for the *answer*:

- A single generic two-port ProcessStep cannot represent both sides without
  losing which port pair belongs to which side, so “collapse `E-101` into one
  step with two ports” is already wrong here.
- The current model’s `Equipment → Port[]` shape *can* carry four nozzles
  (`E-101.side_A_in`, `E-101.side_A_out`, `E-101.side_B_in`,
  `E-101.side_B_out`), but that is physical realization, not a process model.
- DEXPI-derived reasoning in [process-topology.md](process-topology.md)
  (one Equipment may realize several ProcessSteps) suggests one option; the
  process-topology research explicitly excludes multi-side exchangers from the
  temporary 1:1 MVP assumption rather than resolving them.

The decision is deferred to a future fragment that models both sides. For this
fragment the recorded result is:

> One heat-exchanger Equipment can support the chosen one-side process
> abstraction cleanly, provided the abstraction is stated (rule A7). The
> multi-side modeling rule remains an open decision that no current fragment
> resolves.

Note also that this step performs “heat exchange” with no energy port modeled
(rule A3): its only authored boundaries are material. A future energy-port
category would be added when a requirement demonstrates it — not in the first
material-only slice.

## Identity Findings

The fragment was used to test whether semantic identity, engineering-facing
identification, and human-readable naming are already distinct needs. Three
concrete rows:

| Object | Semantic `id` | Process / physical designation | Human `name` |
|---|---|---|---|
| `PS-hx` step | `PS-hx` (process-graph node identity) | no inherent process-step designation; equipment tag `E-101` belongs to the *Equipment*, and only via the 1:1 mapping | “Heat exchanger, process side A” |
| `S-004` stream | `S-004` (graph-edge identity; referenced by nothing else yet but stable) | not decided: a PFD may use a process stream number/designation, distinct from a physical piping line number; this prototype does not establish whether `S-004` is either one or only a label | “Pump discharge to exchanger” |
| `PS-mix` step | `PS-mix` | none — no equipment tag exists at all (untagged junction) | “Fresh feed / recycle mixing point” |

Findings:

- **`id` and `name` are clearly distinct needs.** A semantic `id` is stable,
  machine identity used by references inside the model. `name` is a
  human-readable description for review and rendering. Every prototype step and
  stream naturally wants both.
- **A process stream number / designation is a separate future identity
  question.** It is an engineering-facing identifier used on a PFD or stream
  table. It is not the same thing as a physical piping line number, which
  identifies a physical line in a P&ID / line-list context. PFDs can number or
  otherwise designate process streams; this fragment does not establish whether
  its `S-0xx` labels are stable semantic ids, stream designations, or merely
  prototype labels.
- **No designation field is justified in the first slice.** Physical equipment
  tags (`T-101`, `E-101`) belong to Equipment, and `PS-mix` / `PS-split` prove
  that a ProcessStep may have no equipment tag. The fragment also does not prove
  that a process-stream designation must be stored independently from `id` now.
  Adding `stream_number`, `designation`, or `tag` would therefore invent a
  standard before it is required.
- **Prototype-only labeling.** The concrete `PS-*` / `S-0xx` strings are
  illustrative. The fragment clearly justifies `id` and optional `name`; it
  does **not** decide whether a separate stream number / designation / tag must
  exist independently from `id`.
- Port ids are local to the owning step (e.g., `suction`, `discharge`), which
  mirrors the current equipment-local `Port` convention.

## Cardinality Findings

Observed-in-fragment values are separated from hypothesized general
capabilities. Only the observed column is evidence.

| Relation | Observed in fragment | Hypothesized general capability (not proven here) |
|---|---|---|
| ProcessStep → Equipment | 0..1 — `PS-feed/PS-pump/PS-vessel/PS-hx` → 1; `PS-mix`, `PS-split` → 0; `PS-consumer` → 0 (beyond fragment) | 0..N — duty/standby trains, packaged systems, one function over several items |
| Equipment → ProcessStep | 0..1 — `T-101`, `P-101`, `V-101` → 1; `FV-101` → 0; `E-101` → 1 with a second side already in view but unmodeled | 0..N — one item with several functions/sides (full exchanger, column, reactor) |
| ProcessPort → physical Port / Nozzle | 0..1 — equipment-adjacent ports → 1 current Port; junction ports → `none`/`unresolved` | 0..N — manifold / grouped train realization |
| ProcessStream → physical piping route | 1 : a route of 1..N physical segments — `S-004` spans piping + `FV-101` + piping; boundary stream `S-007` → unresolved beyond fragment | 1 : 0..N — depending on the future physical piping layer |

No relation in the fragment requires a 1:N or N:1 authoring today, but the
model must **permit** 0 and 1 on the process-to-equipment relations (junctions
and the transparent valve prove this), and it must not assume 1:1 anywhere.

## Port Semantics

Does a future ProcessPort need an explicit `direction: input | output` or a
`kind: material` field, or can roles be derived purely from ProcessStream
relationships?

What the fragment shows:

- Every port role in the Process Ports table is **derivable**: a port is an
  input if an incident stream targets it, an output if an incident stream
  sources it. All 14 ports have unambiguous roles because each is incident to
  exactly one stream.
- The fragment never needs a port to declare its own direction for the model
  to be coherent. Mixing/splitting cardinality (`≥2 in : 1 out` and
  `1 in : ≥2 out`) is a property of the step `type`, checked against the
  derived port roles — not a property stored on each port.
- A stored per-port direction would be a **second authored fact that must be
  kept synchronized with stream direction**, duplicating information the graph
  already contains. That violates the Engineering-as-Code invariant used by
  [process-topology.md](process-topology.md) (no two independently authored
  facts when one can be derived).

Caveat the fragment exposes: while a step is being authored *before* its
streams exist, roles cannot yet be derived. That is an acceptable intermediate
state (a partial model), not a reason to store direction. Validation may
require role derivability only when a step has incident streams.

Recommendation based on the fragment:

```text
ProcessPort has identity only;
input/output role is derived from ProcessStream relationships.
```

- `kind` (material) is not needed as a field yet: this fragment is entirely
  material, and there is no second kind to discriminate against. It becomes
  relevant only when energy/information ports are introduced by a future
  requirement.
- Port direction/type must not be implemented in the first slice.

## Stream Direction

Unlike today’s `Connection`, a ProcessStream’s `source → target` means actual
**process-flow direction**, not merely edge orientation. The fragment verifies
this on all four required patterns:

- **normal flow** — `S-004` runs `PS-pump.discharge → PS-hx.in_side_A`
  because the pump pushes fluid that way; reversing it would describe a
  different (impossible for this pump) process.
- **split** — `S-006` and `S-007` leave `PS-split`; they cannot be authored
  into it without contradicting the split function.
- **merge** — `S-001` and `S-002` enter `PS-mix`; only `S-003` leaves.
- **recycle** — `S-002` must be oriented `PS-vessel.out_recycle →
  PS-mix.in_recycle`. Reversing it would turn the recycle into a stream from
  the mixing point to the vessel, which is not the process.

```text
ProcessStream.source → target
= actual process-flow direction (design / normal operation),
  not merely edge orientation.
```

This must be explicit before implementation: structural tooling may treat the
graph as directed and may not assume reversibility; downstream process
semantics (balance direction, pump/valve orientation checks) build on it.

## Operating-State Stress Test

The directed ProcessStream graph is tested here as the **design / normal intended
process-flow** topology, not as a record of every transient operating condition.
The existing fragment remains meaningful when `P-101` is stopped during
shutdown, `FV-101` is closed, or the recycle is disabled: those conditions do
not delete `S-003`, `S-004`, or `S-002` if the designed relationships still
exist. Likewise, a hypothetical bypass around `E-101`, temporary reverse or
abnormal flow where physically possible, maintenance isolation, and equipment
out of service do not by default rewrite the canonical graph.

1. **Does absence of flow mean deleting a ProcessStream?** No, not when the
   design relationship remains present.
2. **Does temporarily closed or unavailable equipment change the canonical
   process graph?** No by default; it changes use or availability unless the
   engineering design topology itself changes.
3. **What does `ProcessStream.source → target` mean?** It represents intended /
   design process-flow direction for the selected process model, not a claim
   that reverse or zero flow is impossible in every operating state.
4. **Where do operating scenarios belong?** The working hypothesis is a future
   scenario/operating-state overlay or configuration: it would modify
   availability, activity, flow/state, or route usage rather than duplicate the
   canonical graph. This fragment does not prove the eventual overlay shape.

## Validation Findings

Only rules that the fragment actually justifies are listed. They are separated
into **structural validity** (provable from references and uniqueness alone)
and **engineering validity** (needs process meaning). Neither is implemented
in this change.

### First hard structural rules

These rules require a clearly defined process-model/container boundary: S1 is
scoped to the owning process model's collections, and S3 resolves references
against its owned steps and streams. No reference-validation rule should be
implemented without that boundary.

| # | Rule | Fragment evidence |
|---|---|---|
| S1 | Ids unique within their owning collections: `ProcessStep.id` within `ProcessModel.steps`; `ProcessStream.id` within `ProcessModel.streams`; the two collections are separate namespaces | needed for stream endpoints and graph identity; step and stream ids may coincide |
| S2 | `ProcessPort.id` unique within the owning `ProcessStep` | mirrors current equipment-local `Port` uniqueness; all 14 ports distinct within their steps |
| S3 | `ProcessRef` endpoints resolve within the `ProcessModel` | all seven streams resolve; equivalent in kind to today’s `Connection` reference validation |
| S4 | source endpoint != target endpoint | no self-edge exists or is meaningful in this fragment |

### Proposed / deferred consistency rule

This fragment observes every port as exclusively input or output: input/output
role is derived from incident ProcessStreams, with a target making a port an
input and a source making it an output. That observation is not sufficient
evidence for a canonical invariant. A future pass-through or abstraction case
may require a different rule. Do **not** implement or recommend “a ProcessPort
is never both source and target” (former S5) as a production validation rule
yet.

### Engineering validity (not structural; deferred)

| # | Rule | Why it is engineering, not structural |
|---|---|---|
| E1 | A `mixing` step has ≥ 2 inputs and exactly 1 output; a `splitting` step has exactly 1 input and ≥ 2 outputs | relies on step-`type` meaning; the fragment observes exactly 2:1 and 1:2 |
| E2 | Source/sink boundary steps are allowed: a step may legitimately have only inputs (`PS-consumer`) or only outputs (`PS-feed` in this fragment) | depends on fragment scope, not on graph form |
| E3 | Future node-level mass balance (`ṁ_in = ṁ_out` per step; mixing/split rules) | needs material-state/flow data that this prototype deliberately omits |
| E4 | Stream orientation agrees with the physical realization (e.g., pump discharge direction, recycle direction) | needs the Process↔Physical mapping that is deferred |

Nothing broader (e.g., general reachability, acyclicity outside recycle
bounds, port-count limits per type) is justified by this fragment and nothing
broader is proposed.

## Model Failures / Ambiguities

The prototype was run honestly against the fragment; these are the places where
the proposed model buckled or stayed ambiguous.

1. **Heat-exchanger multi-side modeling is unresolved.** `E-101` works only
   because rule A7 deliberately drops side B. The moment both sides enter one
   model, the architecture must choose between one Equipment → multiple
   ProcessSteps and one ProcessStep → multiple material port pairs. The
   fragment cannot decide this; a two-sided fragment can. (Heat Exchanger
   Stress Test.)
2. **Junction ports have no physical mapping target.** `PS-mix` and `PS-split`
   ports map to unmodeled piping points. Forcing a mapping onto the nearest
   equipment port collides with the neighboring equipment-bounding port’s
   mapping (`PS-mix.out_mixed` vs `PS-pump.suction` → `P-101.suction`). Until a
   physical piping/nozzle layer exists, junction-port mappings must stay
   `none`/`unresolved` or live only in documentation.
3. **The earlier 1:1 MVP assumption fails.** Junction steps with zero Equipment
   and `FV-101` with zero ProcessSteps refute the temporary assumption that an
   MVP fragment could treat Equipment as a 1:1 stand-in for ProcessStep. Any
   production slice must let ProcessStep exist without an Equipment reference.
4. **Physical graph cannot yet hold the physical fragment.** Current model has
   no valve, nozzle, or piping classes, so even the *physical* side of the
   fragment (`P-101 → FV-101 → E-101`) cannot be authored today. This is a
   known, separate gap, but it means “process graph != physical graph” is
   currently demonstrated conceptually only.
5. **Scenario under-specification at `V-101`.** The given scenario states only
   a recycle outlet for `V-101`. Whether the vessel has further outlets in the
   real unit is unstated and was not invented (rule A5). A reviewer should not
   read the single-outlet vessel as a modeling conclusion.
6. **Step `type` vocabulary is ad hoc.** `storage`, `mixing`, `pumping`,
   `heat_exchange`, `splitting`, `vessel`, `consumer` are enough for this
   fragment but are not a governed vocabulary. Boundary-ness of `PS-feed` and
   `PS-consumer` is fragment scope, not a type property — the graph degree
   (`0 in` / `0 out`) expresses it.
7. **Diff ordering is a serialization concern the fragment cannot solve.** One
   edge per stream keeps topology diffs small only if authoring order is
   stable (e.g., deterministic stream ordering). That rule belongs to a future
   serialization decision, not to the semantic classes.

None of these breaks the *core* proposal (separate process graph with explicit
junction steps, directed flow-semantic streams, no shared-port shortcuts), but
items 1–3 are real decisions a production slice cannot avoid.

## Recommended First Code Slice

### Step hierarchy: Options A / B / C

| Option | Shape | Assessment against the fragment |
|---|---|---|
| **A** | one `ProcessStep` with a `type` discriminator | Sufficient as a simple semantic discriminator for review and future engineering rules; no per-type fields occur. |
| **B** | typed subclasses (`MixingStep`, `SplittingStep`, …) | Not justified. The fragment adds no subclass-specific data or behavior; subclassing would build a taxonomy the architecture explicitly postpones. |
| **C** | generic step, semantic role vocabulary later | Weaker for human review because the fragment does use role labels, but it reinforces that those labels need not yet be governed. |

**Recommendation: Option A with an open string.** `type` is a non-empty semantic
discriminator in the first slice, following the same deliberate simplicity as
current `Equipment.type`. A controlled vocabulary or typed subclasses are
deferred until engineering rules require governed type semantics. For example,
mixing input/output cardinality validation or splitting cardinality validation
would later justify a governed vocabulary.

### Container / validation boundary: C1 / C2

The fragment proves that the process graph must be distinct from the plant /
physical graph, but does not prove which minimal owner should contain it.

| Option | Shape | Assessment |
|---|---|---|
| **C1** | separate `ProcessModel` owning `ProcessStep[]` and `ProcessStream[]`; ProcessPorts are owned by steps | Strongly expresses the separate process graph and gives one obvious validation boundary. It makes future process↔plant mapping explicitly cross-layer. It adds one nesting level and can make Git/YAML paths longer. |
| **C2** | `PlantModel` directly owns `ProcessStep[]` and `ProcessStream[]` beside `Equipment[]` and `Connection[]` | Fits the current single root and keeps a compact Git/YAML shape. It can still keep validation scoped to the process collections, but places both graphs under one root and risks implying a closer ownership relationship than the fragment establishes. Future mappings remain possible. |

The current DeepPlant architecture confirms a `PlantModel` root for the existing
physical/bootstrap collections, while this fragment confirms separate process
semantics. Neither fact decides whether semantic separation should be expressed
as a dedicated process container (C1) or as separately scoped collections under
the current root (C2). Avoiding premature nesting favors C2; separation and
validation clarity favor C1. Git/YAML readability is a trade-off rather than
decisive evidence.

**Conclusion: container ownership remains unresolved.** `ProcessStep`,
`ProcessPort`, `ProcessStream`, and `ProcessRef` are justified concepts, but
production implementation remains blocked until their owning
process-model/container boundary is decided. No reference-validation rules may
be implemented until that boundary defines the process model in which S1–S4
apply.

### Slice outcome

**Outcome B — concepts validated, implementation still blocked.** The concepts
must be introduced together once the owning boundary is approved:

- `ProcessStep { id, type, name?, ports }`
- `ProcessPort { id }` — identity only, no direction/kind
- `ProcessStream { id, name?, source, target }` where source/target use a
  distinct `ProcessRef`, not current `PortRef`

The subsequently approved production slice may apply only hard structural rules
S1–S4, with non-empty semantic ids/types and unknown-field rejection consistent
with the current model. It must not add a tag/designation field, a ProcessPort
direction/kind field, mappings, a governed step-type vocabulary, or the deferred
port-role rule merely to complete this fragment.

**Do not begin production implementation until the owning
process-model/container boundary is approved.**

Deliberately out of scope after that approval:

- process-stream designation / stream-number standard (Identity Findings)
- direction/kind on ProcessPort; energy/information ports
- mappings to Equipment / current Port / future Nozzle (documented only)
- physical piping, valves, nozzles (the physical side of `FV-101` remains
  unmodeled)
- controlled step-type vocabulary, typed subclasses, and type-specific rules
- YAML serialization details and diff-ordering rules
- the heat-exchanger both-sides decision (needs a two-sided fragment)
- operating-state overlay design

## Candidate Schema

> Conceptual shape only — **not a production schema and not approved for
> implementation until the container boundary is decided.**

The fragment justifies the object shapes below, but not their parent container.
Detailed YAML is intentionally **not** provided: field names for an eventual
container, ownership, mapping relations, and the unresolved items above are not
yet approved, and a YAML shape would falsely imply they are.

```python
# Conceptual sketch only — not a production schema.


class ProcessPort:
    id: NonEmptyString  # unique within the owning ProcessStep


class ProcessStep:
    id: NonEmptyString  # unique within the owning process model
    type: NonEmptyString  # open semantic discriminator, not an enum
    name: str | None
    ports: list[ProcessPort]  # ids unique within this step


class ProcessRef:
    step: NonEmptyString  # resolves within the owning process model
    port: NonEmptyString  # resolves to a port owned by that step


class ProcessStream:
    id: NonEmptyString  # unique within the owning process model
    name: str | None
    source: ProcessRef
    target: ProcessRef  # source → target carries intended/design flow direction


# Hard structural checks, after the owner/validation boundary is approved:
# S1 ids unique within owning collections:
#    ProcessStep.id unique within ProcessModel.steps
#    ProcessStream.id unique within ProcessModel.streams (separate namespaces)
# S2 ProcessPort.id unique within the owning ProcessStep
# S3 ProcessRef endpoints resolve within the ProcessModel
# S4 source endpoint != target endpoint
```

## Comparison with the Current Implemented Model

```text
CURRENT IMPLEMENTED MODEL                PROPOSED PROCESS MODEL
                                         (after fragment validation)
PlantModel                               Process graph (conceptual)
├── Plant                                ProcessStep[]
│   └── id, name                             └── ProcessPort[]
├── Equipment[]                          ProcessStream[]
│   ├── id, type, name                       ├── id
│   └── Port[]                               ├── name?
│       └── id (equipment-local)             ├── source ProcessRef(step, port)
└── Connection[]                             └── target ProcessRef(step, port)
    ├── source PortRef(component, port)   ProcessStream.source → target
    └── target PortRef(component, port)      = process-flow direction,
                                             not merely edge orientation
```

| Question | Status after this prototype |
|---|---|
| What stays unchanged | Current `PlantModel` / `Plant` / `Equipment` / `Port` / `Connection`, the existing YAML example, and the CLI remain untouched by this iteration. `Connection` remains the low-level adjacency/bootstrap relation of the physical layer. |
| What new concepts are justified | `ProcessStep` (with an open non-empty `type` discriminator), `ProcessPort`, `ProcessStream`, and `ProcessRef`; they must be introduced together once their owner is approved. Hard structural rules are S1–S4 only. |
| What current concepts are not reused | `Connection` is not reused as the process relation; current `Port` is not reused as a process port; `Equipment` is not reused as a process step (junctions and `FV-101` make 1:1 substitution impossible). ProcessStream endpoint references need a distinct `ProcessRef` type, not current `PortRef`. |
| What remains blocked or deferred | The owning process-model/container boundary; ProcessStep ↔ Equipment; ProcessPort ↔ current Port / future Nozzle; ProcessStream ↔ physical piping route; the heat-exchanger both-sides decision; process-stream designation standards; controlled step-`type` vocabulary; process-layer YAML serialization; operating-state overlay design. |

## Open Questions

1. Heat exchanger with both sides modeled: one Equipment → several ProcessSteps,
   or one ProcessStep → several independent material port pairs?
2. Should junction-port ↔ physical mappings be authored at all before a
   physical piping/nozzle layer exists, or remain documentation-only?
3. Which owning boundary should contain the process collections — a separate
   `ProcessModel` (C1) or direct `PlantModel` ownership (C2)? This is the
   implementation blocker because it defines S1–S4 reference-validation scope.
4. When do engineering rules justify governing the currently open step `type`
   discriminator?
5. Is a pass-through port (one port used as both sink and source) ever
   legitimate? This is not a first-slice validation rule.
6. How are source/sink boundaries represented deliberately — implicit via graph
   degree, or an explicit boundary marker?
7. Which deterministic authoring order makes process-graph diffs stable?
8. Do parallel lines between the same two steps (multiple trains) need
   distinct ports or distinct streams? Not exercised by this fragment.

## Process-Model Container Decision

[ADR-0005](decisions/ADR-0005-process-model-container.md) (Accepted) selects
**C1**: `PlantModel` remains the overall semantic aggregate for one plant and
contains one independently constructible `ProcessModel`; `ProcessModel` owns the
process graph and defines its S1–S4 reference-validation boundary. This resolves
a false dichotomy: a domain submodel may live inside one plant aggregate without
being a separate YAML document or repository-level artifact.

### Decision matrix

| Criterion | C1 `ProcessModel` | C2 direct `PlantModel` ownership |
|---|---|---|
| Semantic cohesion | Keeps steps, ports, and streams as one graph | Keeps graph collections at the aggregate root |
| Validation boundary clarity | S1–S4 reside with the graph they describe | `PlantModel` combines process and physical validators |
| Current implementation simplicity | Adds one semantic container | Fewer immediate fields/classes |
| Independent process testing | Process graph can be constructed alone | Tests must construct an otherwise irrelevant root/plant |
| Adapter boundary | Natural input for PFD, process exchange, and simulation consumers | Consumers must select process collections from the root |
| Process/physical decoupling | Explicit: graph validity has no physical dependency | Possible, but easier to blur at the root |
| Future cross-layer mapping | Leaves mappings above/between two valid graphs | Encourages root-level coupling pressure |
| Risk of premature abstraction | One boundary justified by the real graph | Lowest immediate abstraction cost |
| Root-model complexity | Keeps root aggregate focused | Root accumulates unrelated validation domains |
| Git/YAML impact | Not decisive under ADR-0004 | Not decisive under ADR-0004 |

The fragment supports C1 because `PS-mix`, `PS-split`, and `PS-consumer` are
valid steps despite no corresponding `Equipment`; `S-001`, `S-002`, and an
invalid `S-004` endpoint can be resolved or rejected wholly within the process
graph. Under this boundary, the invalid `ProcessModel` is the invalid
object — not the unrelated physical/bootstrap graph.

The authorized validator shape is:

```text
ProcessStep
    validates unique local ProcessPort ids (S2)

ProcessModel
    validates ids unique within their owning collections (S1):
        ProcessStep.id unique within steps
        ProcessStream.id unique within streams
        (step and stream collections are separate namespaces)
    validates ProcessRef endpoint resolution (S3)
    validates source endpoint != target endpoint (S4)

PlantModel
    retains physical Equipment/Connection validation
```

Under S1, `ProcessStep.id` is unique within `ProcessModel.steps` and
`ProcessStream.id` is unique within `ProcessModel.streams`; the two collections
are separate namespaces, so a step and a stream may use the same string id.
`ProcessPort.id` is unique within its `ProcessStep` (S2), and `ProcessRef.step`
/ `ProcessRef.port` resolves within that model (S3). Those identities are
separate from physical `Equipment` and current `Port` identities, so cross-layer
id collisions remain legal by default. The first production slice assumes at
most one process model per plant aggregate; multiple abstractions, scenario
graphs, and operating state overlays remain deferred. Future mapping relations
are higher-level cross-layer concerns and must not make the process graph
require `Equipment`.

## Decision Status

> **Proposed — requires human architectural review.** This change is
> decision-gated: it introduces no production semantic schema.

The realistic fragment **did not break the core process-layer proposal**, but
it did invalidate the earlier temporary 1:1 “Equipment stands in for
ProcessStep” MVP assumption, and it exposed decisions that any production slice
must face: the exchanger multi-side modeling rule, junction-port physical
mapping, and the process-graph container shape. The first roadmap backlog item
now asks a human reviewer to read this prototype and decide whether the
proposed model is mature enough for its first production implementation slice.

### Reviewer Decision Checklist

Answers and approvals this prototype now makes explicit:

1. **Does `ProcessStep` need to exist separately from `Equipment`?** Yes —
   junction steps (`PS-mix`, `PS-split`) have no Equipment and `FV-101` is
   Equipment with no step.
2. **Does `ProcessPort` need to exist separately from current `Port`?** Yes —
   junction ports have no equipment port; the two identities belong to
   different graphs.
3. **Can `ProcessStream` be the sole authored process-connectivity relation?**
   Yes within the process graph — seven streams fully specify the connectivity;
   no `Connection` is used or duplicated.
4. **Do Mixing and Splitting work without hiding semantics in shared ports?**
   Yes — explicit junction steps with three ports each; mass balances have a
   node to live on.
5. **Does recycle work naturally as a graph cycle?** Yes — `S-002` closes the
   only directed cycle; no special recycle concept, no shared port.
6. **Can a physical valve exist without appearing as a PFD ProcessStep?**
   Yes — `FV-101` is transparent at this abstraction
   (process graph != physical graph).
7. **Can one heat-exchanger Equipment support the chosen abstraction?** Yes for
   the selected one-side abstraction (rule A7); the both-sides modeling rule is
   unresolved.
8. **Is process-container ownership resolved?** No. C1 (separate
   `ProcessModel`) and C2 (collections directly on `PlantModel`) have been
   evaluated, but this fragment does not decide between them. Approval is
   required before implementation because it defines the validation boundary.
9. **What structural validation is justified?** S1–S4 only: ids unique within
   their owning collections (`ProcessStep.id` within `ProcessModel.steps`;
   `ProcessStream.id` within `ProcessModel.streams`; separate namespaces);
   `ProcessPort.id` per owning step; `ProcessRef` endpoints resolving within
   the `ProcessModel`; and distinct source/target endpoints. Former S5 is
   deferred, not a production invariant.
10. **What is the `type` decision?** A non-empty open string discriminator,
    consistent with current `Equipment.type`; no enum, controlled vocabulary,
    or subclasses yet.
11. **What is the stream identity/designation decision?** `id` is stable machine
    identity and `name` is human-readable. A separate process-stream number /
    designation remains a future question and is distinct from a piping line
    number.
12. **Has the operating-state assumption been tested?** Yes. ProcessStream
    direction represents intended/design process flow; shutdown, isolation,
    disabled recycle, bypass use, and abnormal/reverse flow are future operating
    state/scenario concerns by default, not reasons to duplicate or delete the
    canonical graph.
13. **What is the production-slice recommendation?** Outcome B: the concepts
    `ProcessStep`, `ProcessPort`, `ProcessStream`, and `ProcessRef` are
    validated, but do not begin production implementation until the owning
    process-model/container boundary is approved.
