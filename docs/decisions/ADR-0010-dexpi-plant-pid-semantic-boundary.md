# ADR-0010: Keep the DEXPI Plant/P&ID Semantic Boundary at `Port`, `Connection`, and Separate Piping/Instrumentation Layers

> Status: Accepted
> Date: 2026-09-21

## Context

The DEXPI Plant/P&ID semantic-mapping spike
([docs/dexpi-plant-pid-spike.md](../dexpi-plant-pid-spike.md)) investigated the
official DEXPI `V2.0.0` model definitions and the official DEXPI Reference P&ID
instance (`src/documentation/_static/reference_pid.xml`) to answer where the
boundary runs between DEXPI Plant/P&ID semantics and the canonical DeepPlant
physical model.

The evidence established:

- `Plant.PlantModel` is a separate conceptual model from `Process.ProcessModel`,
  and it has **no generic connection collection**: physical connectivity lives in
  the `Piping` package, instrumentation connectivity in the `Instrumentation`
  package.
- Physical items are `TaggedPlantItem`/`ProcessEquipment` with `TagName` identity
  and owned `Nozzles` and `Chambers`.
- Connection points are split in DEXPI: `Nozzle` (equipment-side, owning
  `PipingNode`s, carrying nominal-pressure data and purpose subclasses) and
  `PipingNode` (the attach point, also owned by piping components).
- Piping connectivity is directed (`SourceItem`/`TargetItem`,
  `SourceNode`/`TargetNode`), endpoints are item **and** node, a `Pipe` is an
  elementary uninterrupted piece, an inline valve splits a run into separate
  `Pipe` objects, and piping-line identity (`LineNumber`) belongs to
  `PipingNetworkSystem`, not to any connection.
- Instrumentation is a function layer with its own directed signal edges
  (`SignalConveyingFunction.Source`/`Target`) whose sensing/actuating locations
  are physical-realization objects (nozzle, piping component, piping segment).
- DEXPI's own model separates `Core.ConceptualModel` from `Core.Diagram`, keeps
  engineering objects free of coordinates and labels, and puts drawing metadata in
  `Plant/Diagram.PlantMetaData`.

DeepPlant today has `Equipment` with owned `Port`s and a directed,
property-free `Connection`, deliberately not a pipe, process stream, signal, or
piping line.

## Options

- **A — Adopt DEXPI's Plant shape:** introduce `Nozzle`, `PipingNode`, `Pipe`,
  `PipingNetworkSystem`, and instrumentation classes into the canonical model
  now, mirroring DEXPI's hierarchy.
- **B — Keep the current invariants and record the boundary:** `Port` stays the
  canonical physical connection point; `Connection` stays directed topology
  only; piping realization and instrumentation are recognized as separate future
  layers that must never be folded into `Port`, `Connection`, or
  `Equipment.type`; Plant/P&ID import stays unimplemented and fail-closed.
- **C — Ignore Plant/P&ID entirely:** conclude that DEXPI's Plant layer is out of
  scope indefinitely.

## Decision

**B is accepted**, with the following explicit statements:

1. **`Port` remains the canonical physical connection point and no `Nozzle`
   concept is introduced.** The evidence shows DEXPI's `Nozzle` and `PipingNode`
   differ from `Port` only in ways conditional on capabilities DeepPlant does not
   have: nozzle engineering data, purpose classification, item/node refinement,
   and instrumentation-location roles. `Port` is therefore a documented
   **collapse** of `Nozzle` + `PipingNode`, acceptable only while DeepPlant has
   no piping components and no node-level connectivity. The identity statement
   `DeepPlant Port != DEXPI Nozzle != DEXPI PipingNode` stays in force. `Nozzle`
   may be revisited only when a real requirement needs nozzle data or a separate
   attach point.
2. **`Connection` remains directed semantic topology only, and its scope is now
   stated explicitly.** DEXPI never represents physical adjacency as a
   property-free directed edge between two items; it represents piping
   realization. The existing invariant therefore survives real P&ID semantics:

   ```text
   Connection = directed semantic topology between two connection points
   Connection != pipe
   Connection != pipe segment
   Connection != piping line / line number
   Connection != process stream
   Connection != signal
   Connection != cable
   ```

3. **Piping realization is recognized as a distinct future canonical layer, not
   as content of `Connection` or `Equipment`.** Line number, segment number,
   piping class, fluid code, nominal diameter, insulation/tracing,
   pressure-test circuit, pipe-piece identity, realized-by-pipe vs direct
   connection, and item-vs-node endpoints belong to that layer if and when it is
   built. It is **not** implemented by this ADR.
4. **Instrumentation is recognized as a third layer with its own directed signal
   edges**, never mapped onto `Connection`; its attachment points are
   physical-realization objects, so an instrumentation slice depends on the
   piping layer. It is **not** implemented by this ADR.
5. **Plant/P&ID import remains unimplemented and fail-closed.** No generic
   Plant/P&ID adapter is introduced. The existing DEXPI adapter continues to
   handle only the Process material subset, to reject Plant-only input, and to
   ignore Plant objects in mixed documents; making that ignored content explicit
   is recorded as a prerequisite before any future Plant/P&ID import.
6. **Presentation remains outside the semantic model.** DEXPI's `Core.Diagram`
   and `Plant/Diagram` constructs (`ShapeUsage`, `Point`, `Label` subclasses,
   `PipingNodePosition`, `NozzleStandardLabel`, `PlantMetaData`) are classified
   presentation-only and corroborate ADR-0003.

## Consequences

### Positive

- The product core is not shaped by an external exchange model: DEXPI's class
  hierarchy stays an interoperability concern (ADR-0002, ADR-0003).
- Two invariants that were previously asserted are now **evidence-backed** and
  cannot be eroded by analogy: `Port`'s sufficiency and `Connection`'s
  property-free scope.
- The next physical-model decision is bounded and pre-evidenced: a
  piping-realization layer specified against a concrete official fragment, rather
  than guessed from class names.
- Instrumentation and asset-hierarchy work now have obvious prerequisites instead
  of tempting shortcuts.
- No implementation risk: nothing in the model, adapter, fixtures, or tests
  changes.

### Negative

- DeepPlant cannot claim faithful P&ID fidelity for piping or instrumentation
  until those layers exist; the realistic fragment remains deliberately partial.
- Plant/P&ID adapter work is blocked on a layer decision rather than being
  incrementally achievable.
- `Port` remains an overloaded name for two DEXPI concepts; the collapse must be
  re-examined whenever the piping layer is designed, so a known redefinition risk
  stays open.

## Deferred

- The design of a piping-realization layer (line/segment/pipe-piece identity and
  endpoints) and its first canonical field.
- Whether inline components (valves, fittings) become their own component kind or
  remain `Equipment` with a type value.
- Nozzle-level engineering data and any `Nozzle` concept.
- Instrumentation, signals, and off-page/cross-sheet connector semantics.
- `PlantStructure` asset hierarchy, utilities, `Chamber`/`SprayNozzle`.
- DEXPI graphics, shape catalogues, and drawing-metadata handling.
- Any generic Plant/P&ID import, export, or round-trip claim.

## Revisit When

A concrete DeepPlant requirement, example, or executable check needs one of:
pipe/segment/line identity; piping-class or fluid-code data; nozzle or
attach-point data; instrumentation or signal semantics; or a documented need to
import Plant/P&ID content — each of which must arrive with its own evidence and
Issue. This ADR authorizes no implementation by itself, and the anti-roadmap in
[roadmap.md](../roadmap.md) still governs.

## Related

- [docs/dexpi-plant-pid-spike.md](../dexpi-plant-pid-spike.md) — the evidence
  (version pin, model facts, instance facts, findings, gaps, next slice).
- [docs/dexpi-process-spike.md](../dexpi-process-spike.md) and
  [ADR-0009](ADR-0009-separate-process-function-from-symbol-role.md) — the
  process-layer precedent for evidence-before-model.
- [ADR-0002](ADR-0002-semantic-model-is-the-core.md),
  [ADR-0003](ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0007](ADR-0007-standards-and-symbol-provenance.md).
- [docs/process-topology.md](../process-topology.md),
  [docs/architecture.md](../architecture.md), [docs/roadmap.md](../roadmap.md).