---
type: adr-index
status: active
source_of_truth_for:
  - architectural-decisions-index
read_when:
  - architecture-change
  - create-adr
update_when:
  - adr-added
  - adr-status-change
---

# Architectural Decisions

| ADR | Status | Decision |
|---|---|---|
| ADR-0001 | Accepted | Use the generated golden-path baseline and grow infrastructure only when requirements justify it. |
| ADR-0002 | Accepted | The semantic engineering model is the product core; all consumers depend on it. |
| ADR-0003 | Accepted | Keep semantic engineering data and presentation/rendering data strictly separate. |
| ADR-0004 | Accepted | YAML is a serialization format validated into the domain model, not the domain model itself. |
| ADR-0005 | Accepted | Use `ProcessModel` as the process-graph container and S1–S4 validation boundary while `PlantModel` remains the overall aggregate. |
| ADR-0006 | Accepted | Accept `PlantModel.process: ProcessModel \| None` as the first root shape and the YAML `process` section as the first serialization boundary. |
| ADR-0007 | Accepted | Do not redistribute restricted standards content; reference normative standards by identifier with human verification; allow AI agents only openly licensed standards material, DeepPlant-authored summaries, and public material whose applicable terms explicitly permit AI use; require explicit redistributable provenance for all distributed symbol assets; treat standards correspondence and asset copyright as separate concerns; use DEXPI under CC BY 4.0 with attribution without making it the drawing standard. |
| ADR-0008 | Accepted, partially superseded by ADR-0009 (only the `ProcessStep.type` → symbol-role coupling) | Use SVG as the initial presentation asset format for the process/PFD layer: a symbol role (in the original text read from `ProcessStep.type`) is not globally canonical SVG geometry; a future presentation layer selects a graphical symbol pack; the initial DeepPlant-original `basic` pack is non-normative fallback/reference geometry under `assets/symbols/process/basic/` with uniform `viewBox="0 0 100 100"` and machine-readable ordered `anchor-in-N` / `anchor-out-N` slots distinct from semantic `ProcessPort` ids; input/output roles derived from `ProcessStream` incidence; anchors are hidden via `fill`/`stroke="none"` without an exact radius, unrelated internal SVG ids allowed; pack selection, renderer, layout, routing, labels, rotation, and custom-pack machinery deferred. The role → pack → SVG + anchor contract remains in force. |
| ADR-0009 | Accepted | Separate `ProcessStep.function` (open, DeepPlant-native engineering semantics) from the presentation symbol role (resolved by renderer presentation policy or explicit per-step overrides at the rendering boundary; never stored in the semantic model); remove `ProcessStep.type` as an intentional pre-1.0 break; `unspecified` remains a legal function; unresolved-role rendering is a presentation error; DEXPI maps step classes onto DeepPlant functions (including reverse material-only `pumping`); persistent view configuration deferred. |
| ADR-0010 | Accepted | Keep the DEXPI Plant/P&ID semantic boundary at the current primitives: `Port` remains the canonical physical connection point (a documented collapse of DEXPI `Nozzle` + `PipingNode`; no `Nozzle` concept), `Connection` remains directed semantic topology only (never a pipe, pipe segment, piping line, process stream, signal, or cable), piping realization (`Pipe`, `PipingNetworkSegment`, `PipingNetworkSystem.LineNumber`, piping class, fluid code, nominal diameter) and the instrumentation/signal function layer are recognized as separate future layers that depend on their own evidence and Issue, Plant/P&ID import stays unimplemented and fail-closed, and DEXPI `Core.Diagram`/`Plant.Diagram` constructs stay presentation-only. The physical-piping-layer design this ADR deferred is now specified and decided by [ADR-0011](ADR-0011-canonical-physical-piping-realization.md). |
| ADR-0011 | Accepted | Represent physical piping as `PipingLine` → `PipingSegment` → `PipingRealization` inside an optional `PipingModel` container (`PlantModel.piping`), referencing identified `Connection`s: `Connection` stays pure directed physical adjacency and gains only canonical identity (`Connection.id`, plant-unique, a documented pre-1.0 breaking change to authored YAML); the piping layer never restates topology, so piping is a dependent cross-layer-validated submodel rather than an independent graph; `PipingLine` carries canonical `id` plus optional human `line_number`/`name` (a DEXPI `PipingNetworkSystem` id never becomes canonical); `PipingSegment` is the engineering property boundary (`nominal_diameter`, `piping_class`, `fluid_code` as optional open strings, no DEXPI `SegmentNumber`, no line-level inheritance); `PipingRealization.kind` defaults to `pipe` with `direct` as the evidenced exception and an open vocabulary; no canonical `Pipe` or `DirectPipingConnection` class (elementary piece identity deferred, kind recorded instead), inline components remain `Equipment` for now (no `PipingComponent` kind, no valve/fitting taxonomy, no tee class), `Port` remains the endpoint with no `Nozzle`/`PipingNode` refinement, and a branch is a physical item with several named ports plus ordinary `Connection`s (a tee does not split a segment); structural rules P1–P5 belong to the layer, engineering rules (DN/class continuity, reducer at transition, line-number consistency) stay future rule-engine work; no presentation, process, or instrumentation data enters the layer, and Process ↔ physical realization remains explicitly undecided. Specification: [docs/physical-piping-model.md](../physical-piping-model.md) |

Create an ADR for architecture style changes, databases, external services, authentication, cache, queues, events, deployment, vendor lock-in, and data ownership changes.
