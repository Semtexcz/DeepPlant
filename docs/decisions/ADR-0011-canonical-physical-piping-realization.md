# ADR-0011: Represent Physical Piping as Line → Segment → Realization over Identified `Connection` Topology

> Status: Accepted
> Date: 2026-09-21

## Context

The DEXPI Plant/P&ID semantic-mapping spike
([docs/dexpi-plant-pid-spike.md](../dexpi-plant-pid-spike.md)) and
[ADR-0010](ADR-0010-dexpi-plant-pid-semantic-boundary.md) established that
DeepPlant's current physical primitives (`Equipment` with owned `Port`s and a
directed, property-free `Connection`) are sufficient for the *topology*
DeepPlant claims today, that DEXPI's `Nozzle`/`PipingNode` refinement is
conditional on capabilities DeepPlant lacks, and that piping realization is a
separate future layer which must never be folded into `Port`, `Connection`, or
`Equipment.type`. ADR-0010 explicitly deferred the design of that layer and
named it the next evidence-producing task, which became Issue #24.

The official DEXPI `V2.0.0` model and Reference P&ID instance show that the
missing facts are real engineering semantics: line identity
(`PipingNetworkSystem.LineNumber`), property boundaries
(`PipingNetworkSegment` with fluid code, piping class, nominal diameter,
insulation, tracing, test circuit), elementary pipe pieces (`Pipe`, "not
interrupted by any item"), and a real pipe-realized vs direct distinction
(`Pipe` vs `DirectPipingConnection`, 29 vs 2 in the instance). An inline valve
terminates one `Pipe` and starts the next, which is exactly the granularity
DeepPlant's existing `Connection` already has for `FV-101`.

The question this ADR answers is bounded to the physical side:

```text
What is the physical piping graph?
```

It does **not** answer how `ProcessStep` maps to `Equipment` or how
`ProcessStream` maps to physical piping.

## Options

- **A — line metadata over topology:** `PipingLine` with one property set and a
  list of connection references; no segment level, no realization object.
- **B — line + segment + elementary realization referencing connections:**
  `PipingLine` groups `PipingSegment`s; a segment is the property boundary and
  owns `PipingRealization` entries that reference existing `Connection`s and
  state `kind: pipe | direct`.
- **C — independent piping graph:** the piping layer owns its own nodes and
  edges, with equipment attachments as node references.
- **D — widen `Connection`** with line, DN, class, and fluid properties.

Candidate analysis, worked examples, Git-diff behaviour, rule, adapter, and
rendering implications are in
[docs/physical-piping-model.md](../physical-piping-model.md).

## Decision

**B is accepted**, on the following explicit terms:

1. **The canonical piping layer consists of `PipingLine` → `PipingSegment` →
   `PipingRealization`, plus `PipingModel` as its optional container
   (`PlantModel.piping`), mirroring the accepted `PlantModel.process`
   submodel-container precedent (ADR-0005, ADR-0006).**
2. **`Connection` remains pure directed physical adjacency.** It is not a pipe,
   segment, line, realization, process stream, or signal, and it acquires no
   engineering property of any kind.
3. **The piping layer references identified connections instead of restating
   topology.** `Connection` therefore gains a canonical identity (`Connection.id`),
   plant-unique. Identity is not an engineering property; the meaning of
   `Connection` is unchanged. This is a documented pre-1.0 breaking change to
   authored YAML.
4. **Piping is a dependent layer, not an independent graph.** Unlike
   `ProcessModel`, a `PipingModel` cannot be structurally valid on its own
   because it references physical-layer `Connection`s; its validation is
   cross-layer. This asymmetry is intentional.
5. **`PipingLine` carries `id` (canonical), `line_number` (optional human
   designation), and `name`; `line_number` is never the canonical identity and
   a DEXPI `PipingNetworkSystem` XML object id never becomes a DeepPlant id.**
6. **`PipingSegment` is the first-slice property boundary**
   (`segment_number` as an optional human/external engineering designation,
   plus `nominal_diameter`, `piping_class`, and `fluid_code` as optional open
   strings). `PipingSegment.id` remains owner-local canonical identity;
   `PipingNetworkSegment.SegmentNumber` maps only to `segment_number`, and
   neither it nor DEXPI XML `Object@id` becomes canonical identity
   automatically. First-slice segment boundaries must coincide with
   `Connection` boundaries; DEXPI `PropertyBreak` / mid-connection property
   changes are a known fidelity limitation, explicitly deferred.
7. **`PipingRealization` states how one adjacency is realized**; `kind` is the
   closed first-slice vocabulary `pipe | direct`. It defaults to `pipe`,
   `direct` is the evidenced exception, and an unknown value is a validation
   error. No realization is distinct from `kind: pipe`.
8. **No canonical `Pipe` class and no `DirectPipingConnection` class.** An
   elementary pipe piece already has the extent of a `Connection` because
   inline items terminate adjacencies; the realization *kind* is recorded
   without introducing piece identity. `Pipe` is deferred, not rejected
   forever.
9. **Inline components remain `Equipment` (option A of the spike's §8 I3
   question), for now.** A `PipingComponent` kind, a valve/fitting/reducer
   taxonomy, and a generic physical-item hierarchy are deferred with stated
   triggers.
10. **`Port` remains the endpoint concept and no `Nozzle`/`PipingNode` is
    introduced.** Node refinement is required only if two connections must
    attach to one connection point; branch points are physical items with
    several named ports.
11. **A branch is ordinary topology plus ordinary grouping:** a tee is an item
    with three ports and three `Connection`s, and the run's segment is not
    split by the tee — only a property change splits a segment.
12. **C1 and structural rules P1–P5 belong to this layer.** C1 requires a
    non-empty, plant-unique `Connection.id`; P1–P5 cover unique line ids,
    unique segment ids per line, resolvable connection references, at most one
    realization per connection, and non-empty segments. P4 is intentionally a
    conservative first-slice 1:1 invariant, not a universal law of physical
    engineering; it may be relaxed only through a later evidence-backed ADR
    change. All other checks listed in the specification are engineering rules
    for a future rule engine.
13. **No presentation, process, or instrumentation concern enters the layer:**
    no coordinates, routing, symbol ids, sheet metadata, no `process_ref` /
    `stream_ref` / `realized_by` field, no signal semantics.

## Rejected alternatives

| Alternative | Why rejected |
|---|---|
| **A — line metadata over topology** | One property set per line cannot express a DN or piping-class change inside one line, and it has no way to distinguish direct from pipe-realized adjacency. A property change would have to be faked as a new "line", asserting a line identity the engineering data does not support. It survives as the single-segment special case of the accepted shape. |
| **C — independent piping graph** | It authors physical connectivity a second time (endpoints restated as nodes), the exact duplication class [process-topology.md](../process-topology.md) rejected for `ProcessStream`. It also imports node identity and a node-kind taxonomy that the evidence does not justify and `Port` already covers. |
| **D — widen `Connection` with piping properties** | Makes the topology primitive a physical engineering object, forces one property set per adjacency instead of per property boundary, copies line-level data onto every connection, and still does not provide line or segment identity. Forbidden by the anti-roadmap in [roadmap.md](../roadmap.md). |
| **Canonical `Pipe` class now** | Would duplicate the extent of `Connection` without adding engineering meaning (DEXPI's `Pipe` has no own data). Deferred, not rejected in principle. |
| **`Nozzle` + `PipingNode` now** | Conditional on node-level connectivity DeepPlant does not have; ADR-0010 already recorded the collapse and the unresolved `Port.id` derivation. |
| **Separate `PipingComponent` kind now** | Duplicates `Equipment` identity, ownership, and port mechanics without a distinguishing requirement. |
| **Copying DEXPI names** (`PipingNetworkSystem`, `PipingNetworkSegment`, `PipingConnection`) | The canonical model must not be shaped by an external exchange hierarchy (ADR-0002/ADR-0003); DeepPlant names record engineering meaning (`line`, `segment`, `realization`). |

## Consequences

### Positive

- The physical piping graph becomes representable without a second connectivity
  graph: one authored topology fact (`Connection`) plus grouping and realization
  statements that reference it.
- The "absence of a modelled pipe" ambiguity that today's fixture documents
  becomes expressible: an unreferenced `Connection`, a pipe-realized
  realization, and a direct realization are three distinguishable states.
- Engineering checks that were previously impossible (DN continuity,
  piping-class continuity, reducer-at-transition, direct vs pipe routing) gain a
  data boundary without adding taxonomy.
- Inline components work unchanged: `FV-101` already terminates and starts
  `Connection`s, which is DEXPI's structural role for a piping component, so the
  layer needs no component classification.
- Branches need no new concept: a tee with three ports is enough, so no
  node/junction abstraction is introduced.
- The decision is reversible in shape: the levels are additive and the only
  change to an existing primitive is identity.

### Negative

- `Connection` gains a required id: a documented pre-1.0 breaking change to
  authored YAML, fixtures, and tests.
- The model gains two identity levels and one reference object; a reader must
  understand four physical concepts instead of two.
- `PipingModel` is the first semantic submodel that cannot validate on its own,
  so cross-layer validation ownership must be designed deliberately.
- Known fidelity gaps stay explicit rather than closed: item/node endpoint
  refinement, mid-connection property breaks, insulation/tracing/slope/test-
  circuit data, system-level template inheritance, off-page connectors, and
  pipe-piece identity.
- Inline components are still `Equipment`, so a valve and a pressure vessel
  share one kind until a distinguished requirement appears.

## Deferred

- DEXPI Plant/P&ID import/export of this layer, and the ignored-content report
  the adapter must gain when Plant content starts to matter.
- `Nozzle`, `PipingNode`, item + node endpoints, and the DEXPI → `Port.id`
  derivation (carried forward from ADR-0010).
- A canonical `Pipe`/pipe-piece identity, `PipingComponent` kind, valve/fitting
  taxonomy, and a tee class.
- Line-level property inheritance/defaults (DEXPI system-level templates).
- Quantity/unit typing for DN, pressure, temperature, and thickness.
- Insulation, heat tracing, slope, pressure-test circuit, flow direction,
  jacketing, and system grouping.
- Mid-connection property breaks (`PropertyBreak` semantics), until a concrete
  requirement justifies a canonical topology/break representation.
- Multiple/as-built/alternative realizations per adjacency (`1:N` cardinality)
  and revision status.
- Off-page/continuation connectors and cross-sheet semantics.
- Instrumentation and signal layers (separate layer per ADR-0010).
- Rule-engine implementation, P&ID rendering, and any presentation data.

## Process ↔ physical realization is not decided

Explicitly outside this ADR:

```text
ProcessStep   ↔ Equipment                                          unresolved
ProcessStream ↔ PipingLine / PipingSegment / PipingRealization      unresolved
ProcessPort   ↔ Port                                               unresolved
```

No mapping field is introduced, and the accepted piping layer is required to be
useful without any process-layer reference. `ProcessModel` remains an
independently valid submodel; `PipingModel` remains a physical-layer submodel;
neither depends on the other, and no cross-layer cardinality is claimed.

## Revisit When

- A concrete requirement needs a DN, piping-class, insulation, or similar
  property change that does not coincide with an existing topology item or
  `Connection` boundary (then design the break semantics deliberately).
- A concrete requirement needs parallel, as-built, or alternative realizations
  for one adjacency (then resolve `1:N` cardinality deliberately).
- A concrete requirement needs two connections on one physical connection point
  (then `Nozzle`/`PipingNode` refinement must be reconsidered).
- A concrete requirement shows `Equipment` is insufficient for inline
  components (then design a physical-item kind instead of adding fields).
- Pipe-piece identity is needed for spooling, materials, stress, or fabrication
  workflows (then design `Pipe` from that evidence).
- DEXPI 2.0.1 or a later stable release changes the piping semantics this
  decision relies on, or a Plant/P&ID adapter shows the collapsed mapping loses
  something DeepPlant must own.
- Evidence requires widening the closed `kind: pipe | direct` vocabulary with
  a new realization meaning.

## Related

- [docs/physical-piping-model.md](../physical-piping-model.md) — the
  specification this ADR decides (requirements, candidates, worked fragment,
  diffs, rule/adapter/rendering implications).
- [docs/dexpi-plant-pid-spike.md](../dexpi-plant-pid-spike.md) — the DEXPI
  `V2.0.0` evidence base.
- [ADR-0010](ADR-0010-dexpi-plant-pid-semantic-boundary.md) — the `Port` /
  `Connection` boundary and the deferral this ADR now resolves for the physical
  side.
- [ADR-0002](ADR-0002-semantic-model-is-the-core.md),
  [ADR-0003](ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0005](ADR-0005-process-model-container.md),
  [ADR-0006](ADR-0006-process-model-root-integration.md),
  [ADR-0009](ADR-0009-separate-process-function-from-symbol-role.md).
- [docs/process-topology.md](../process-topology.md),
  [docs/architecture.md](../architecture.md), [docs/roadmap.md](../roadmap.md).