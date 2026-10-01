---
type: navigation
status: active
canonical_for:
  - evidence-and-research-index
read_when:
  - interoperability-work
  - model-growth
  - evidence-review
update_when:
  - research-document-added
  - evidence-status-change
depends_on:
  - docs/conventions.md
  - docs/contracts/index.md
decision: []
evidence: []
superseded_by: null
---

# Research, Evidence, and History

This index lists every investigation document, its authority status, the
current contract or decision that operationalizes its outcome, and where it
remains the canonical evidence.

**Evidence documents do not own current rules.** They record what was
investigated, with dates, sources, and outcomes. Current obligations live in
[contracts/](../contracts/index.md); decisions in
[decisions/](../decisions/index.md).

## DEXPI interoperability evidence

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [dexpi-process-spike.md](../dexpi-process-spike.md) | Can a DEXPI 2.x Process subset map into the canonical `ProcessModel` without hidden invention, and can it be exported back? | Narrow material subset supported; function/role conflation found and fixed; unsupported content fails by name | [contracts/dexpi-process-adapter.md](../contracts/dexpi-process-adapter.md), ADR-0009 |
| [dexpi-exchanging-thermal-energy-evidence.md](../dexpi-exchanging-thermal-energy-evidence.md) | Can DEXPI `ExchangingThermalEnergy` map honestly to `ProcessStep(function="heat_exchange")`? | No mapping claimed: mandatory `Method`, coupled multi-stream semantics, and missing qualified quantities; class stays explicitly unsupported | [contracts/dexpi-process-adapter.md](../contracts/dexpi-process-adapter.md) |
| [dexpi-plant-pid-spike.md](../dexpi-plant-pid-spike.md) | Where is the semantic boundary between DEXPI Plant/P&ID and the canonical physical model? | `Port` stays sufficient for the claimed abstraction; piping and instrumentation are separate layers; Plant import stays unimplemented | [contracts/plant-model.md](../contracts/plant-model.md), [contracts/physical-piping.md](../contracts/physical-piping.md), ADR-0010 |

## Canonical-model evidence

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [process-step-classification.md](../process-step-classification.md) | Does canonical `ProcessStep` need a second classification concept beside `function`? | No: DEXPI's nine `Method` properties across seven enums are heterogeneous and partly physical-realization semantics | [contracts/process-model.md](../contracts/process-model.md), ADR-0012 |
| [qualified-engineering-quantities.md](qualified-engineering-quantities.md) | What semantic boundary should DeepPlant use for numerical engineering values with units? | A reusable canonical quantity value (stored scalar magnitude + represented unit semantics) owned by explicit domain properties is justified; units are semantic, not presentation; generic property bags and per-property quantity classes rejected; not implemented | ADR-0013 (no contract yet — no quantity implemented) |
| [physical-piping-model.md](../physical-piping-model.md) | What is the physical piping graph, and which minimal canonical shape represents it? | Candidate B selected (line → segment → realization over identified connections); the contract now owns the rules it defines | [contracts/physical-piping.md](../contracts/physical-piping.md), ADR-0011 |
| [process-topology.md](../process-topology.md) | How should process topology relate to physical topology without duplicating connectivity? | Duplicate-endpoint `ProcessStream` rejected; separate process graph required | [contracts/process-model.md](../contracts/process-model.md), ADR-0005 |

## Prototypes and historical modelling work

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [process-fragment-prototype.md](../process-fragment-prototype.md) | Can one realistic PFD fragment be modelled with explicit steps, ports, streams, junctions, and a recycle? | Concepts validated; 1:1 equipment-as-step assumption disproved; container ownership decided | [contracts/process-model.md](../contracts/process-model.md), ADR-0005/ADR-0006, `examples/realistic-process-fragment/` |

## Reuse, standards, and asset evidence

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [reference-products.md](../reference-products.md) | Which existing projects are credible reuse, integration, or reference candidates for future views/editing? | Study list with licence findings and unresolved items; no selection or dependency | [direction.md](../direction.md) stages 3–4 (not authorized) |
| [standards.md](../standards.md) | Which standards may be referenced, what may be stored, and what provenance do distributed symbols need? | Policy plus registry plus source assessment (shared document; policy is the active part) | ADR-0007 |

## History

| Document | Contents |
|---|---|
| [history/implementation-slices.md](../history/implementation-slices.md) | The roadmap state narrative and the completed-slice record, moved verbatim out of the roadmap |

## Outcome-card convention

Every document listed above is being brought to the conventions in
[../conventions.md](../conventions.md): front matter, an outcome card at the top,
and an explicit statement of the current contract that operationalizes its
outcome. Where an older document still mixes a proposed or historical shape with
current rules, the current rule lives in the linked contract.
