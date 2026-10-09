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
  - docs/dev/workflow/conventions.md
  - docs/contracts/index.md
decision: []
evidence: []
superseded_by: null
---

# Research and Evidence

This index lists every investigation document, its authority status, the
current contract or decision that operationalizes its outcome, and where it
remains the canonical evidence.

**Evidence documents do not own current rules.** They record what was
investigated, with dates, sources, and outcomes. Current obligations live in
[contracts/](../../contracts/index.md); decisions in
[decisions/](../decisions/index.md).

## DEXPI interoperability evidence

DEXPI evidence lives in the `dexpi/` cluster. The former monolithic Plant/P&ID
spike is split by evidence responsibility: physical topology and piping
boundaries, instrumentation/signals, and presentation/graphics.

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [dexpi/process-adapter-spike.md](dexpi/process-adapter-spike.md) | Can a DEXPI 2.x Process subset map into the canonical `ProcessModel` without hidden invention, and can it be exported back? | Narrow material subset supported; function/role conflation found and fixed; unsupported content fails by name | [dev/reference/dexpi-process-adapter.md](../reference/dexpi-process-adapter.md), ADR-0009 |
| [dexpi/exchanging-thermal-energy.md](dexpi/exchanging-thermal-energy.md) | Can DEXPI `ExchangingThermalEnergy` map honestly to `ProcessStep(function="heat_exchange")`? | No mapping claimed: mandatory `Method`, coupled multi-stream semantics, and missing qualified quantities; class stays explicitly unsupported | [dev/reference/dexpi-process-adapter.md](../reference/dexpi-process-adapter.md) |
| [dexpi/plant-pid-semantic-boundary.md](dexpi/plant-pid-semantic-boundary.md) | How do DEXPI Plant/P&ID physical concepts map to the current DeepPlant physical topology and piping boundaries? | `Port` stays sufficient for the claimed abstraction; piping realization is a separate layer; Plant import stays unimplemented | [contracts/plant-model.md](../../contracts/plant-model.md), [contracts/physical-piping.md](../../contracts/physical-piping.md), ADR-0010, ADR-0011 |
| [dexpi/plant-pid-instrumentation.md](dexpi/plant-pid-instrumentation.md) | What does inspected DEXPI Plant/P&ID evidence show about instrumentation, signals, and their relationship to DeepPlant's semantic layers? | Instrumentation is a separate function layer; signal edges must not become `Connection`; nothing implemented or claimed | ADR-0010 |
| [dexpi/plant-pid-presentation.md](dexpi/plant-pid-presentation.md) | Where do DEXPI Plant/P&ID diagram/graphics constructs belong relative to DeepPlant semantics? | Diagram/graphics constructs are presentation-only and never become canonical engineering semantics | ADR-0003 |

## Canonical-model evidence

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [process-step-classification.md](process-step-classification.md) | Does canonical `ProcessStep` need a second classification concept beside `function`? | No: DEXPI's nine `Method` properties across seven enums are heterogeneous and partly physical-realization semantics | [contracts/process-model.md](../../contracts/process-model.md), ADR-0012 |
| [qualified-engineering-quantities.md](qualified-engineering-quantities.md) | What semantic boundary should DeepPlant use for numerical engineering values with units? | A reusable canonical quantity value (stored scalar magnitude + represented unit semantics) owned by explicit domain properties is justified; units are semantic, not presentation; generic property bags and per-property quantity classes rejected; not implemented | ADR-0013 (no contract yet — no quantity implemented) |
| [physical-piping-model.md](physical-piping-model.md) | What is the physical piping graph, and which minimal canonical shape represents it? | Candidate B selected (line → segment → realization over identified connections); the contract now owns the rules it defines | [contracts/physical-piping.md](../../contracts/physical-piping.md), ADR-0011 |
| [process-topology.md](process-topology.md) | How should process topology relate to physical topology without duplicating connectivity? | Duplicate-endpoint `ProcessStream` rejected; separate process graph required | [contracts/process-model.md](../../contracts/process-model.md), ADR-0005 |
| [process-physical-realization-boundary.md](process-physical-realization-boundary.md) | Where should future process ↔ physical realization relationships be owned, and what target/cardinality boundary must they permit? | Separate cross-layer realization layer decided; independently valid endpoint models; no mapping schema, identity, or metadata introduced | ADR-0016 (unimplemented) |

## Prototypes and historical modelling work

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [process-fragment-prototype.md](process-fragment-prototype.md) | Can one realistic PFD fragment be modelled with explicit steps, ports, streams, junctions, and a recycle? | Concepts validated; 1:1 equipment-as-step assumption disproved; container ownership decided | [contracts/process-model.md](../../contracts/process-model.md), ADR-0005/ADR-0006, `examples/realistic-process-fragment/` |

## Planning selection evidence

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [next-slice-re-evaluation.md](next-slice-re-evaluation.md) | What is the best evidence-backed next executable slice after Issue #32? | One Ready slice: the process ↔ physical realization boundary (Issue #39), since delivered; quantity implementation, port kinds, DEXPI 2.0.1 review, view layer, and rules deferred | [roadmap.md](../planning/roadmap.md) (Issue #39 delivered; the milestone structure now owns selection) |

## Engineering editor UX evidence

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [engineering-editor-ux.md](engineering-editor-ux.md) | How should an engineer interact with the DeepPlant Engineering Editor MVP v0.1, so the first GUI slice does not invent fundamental UX behaviour while the semantic model stays authoritative? | Interaction architecture: canvas-dominant minimum permanent chrome; one command direction; four separated state kinds; engineering-concept explorer; PFD/P&ID as editor views; cardinality-neutral related-object navigation; shared command surface for direct manipulation/palette/Copilot; Copilot placeholder deferred; MVP/later/not-now UX matrix; #70 keeps library selection | [engineering-editor-reuse-architecture.md](engineering-editor-reuse-architecture.md) (Issue #70 technology/boundary layer); [roadmap.md](../planning/roadmap.md) |

## Engineering editor reuse architecture evidence

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [engineering-editor-reuse-architecture.md](engineering-editor-reuse-architecture.md) | Which reusable GUI technologies should underpin the DeepPlant Engineering Editor, and where are their boundaries? | Selects a small reuse-first stack — Vue 3 + TypeScript + Vite (foundation), Vue Flow (canvas, behind a DeepPlant projection/adapter), Reka UI (primitives) — and defers/rejects Dockview, Monaco, ELK/elkjs, Pinia, VueUse, shadcn-vue, X6, and Cytoscape.js, each with an adoption trigger; keeps semantic/presentation/framework state separated, undo/redo at the application-command boundary, and the existing renderer/symbol contract reused; no new ADR and no dependency added | the read-only Process/PFD editor slice (Issue #75) is its first implementation consumer; informs [roadmap.md](../planning/roadmap.md) |

## Reuse, standards, and asset evidence

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [reference-products.md](reference-products.md) | Which existing projects are credible reuse, integration, or reference candidates for future views/editing? | Study list with licence findings and unresolved items; no selection or dependency | [direction.md](../planning/direction.md) stages 3–4 (not authorized) |
| [standards-licensing-evidence.md](standards-licensing-evidence.md) | What public/open sources, licences, provenance claims, and candidate graphical assets were inspected to justify DeepPlant's standards and symbol-provenance policy? | Source/licence/provenance findings with their inspection dates: ISPF not approved, draw.io `pid2` a candidate pending per-file confirmation, IPD Studio current rejected, DEXPI CC BY 4.0 confirmed; no asset imported | ADR-0007 + [workflow/standards.md](../workflow/standards.md) (policy); [reference/standards-registry.md](../reference/standards-registry.md) (registry) |
| [notation-profile-classification.md](notation-profile-classification.md) | Which notation profiles, if any, should the three current `generic-iso` representations (`valve.gate`, `pump.centrifugal`, `instrument.local`) migrate to, based on the available evidence? | Public-source classification: `valve.gate` and `instrument.local` suit `deepplant-default`; `pump.centrifugal` should be redesigned first; exact standards geometry is unresolved for all three and `iso-10628` is too coarse because instrumentation belongs to ISO 15519-2 / ISA-5.1; `candidate-alignment` retained; no migration performed | Issue #124 (notation-profile architecture) and Issue #127 (this research); feeds [profiles.py](../../../src/deepplant/symbols/profiles.py) policy and [reference/symbol-library.md](../reference/symbol-library.md) |

## Editor distribution evidence

| Document | Question investigated | Outcome | Operationalized by |
|---|---|---|---|
| [standalone-editor-distribution.md](standalone-editor-distribution.md) | How can the read-only Engineering Editor become an installable Windows and Linux application without losing the local browser SPA, the FastAPI/Uvicorn boundary, or Core independence? | Measured four candidate stacks against the real application; selects PyInstaller onedir + Inno Setup (Windows) + AppImage (Linux) for the distribution-foundation slice; rejects Briefcase (documented AppImage/binary-wheel unreliability plus required project restructuring) and, for this slice, webview/Electron/Tauri (the goal was self-contained packaging without changing the product UI host); defers Nuitka (free integrated NSIS/AppImage, but 768-module C builds and unverified runtime here); makes the SPA an application-owned package resource. The native desktop host it deferred was then decided by [#93](https://github.com/Semtexcz/DeepPlant/issues/93) in [editor-desktop-host.md](editor-desktop-host.md) | [workflow/packaging.md](../workflow/packaging.md) (practice); [user/how-to/install-the-editor.md](../../user/how-to/install-the-editor.md) (user path); [contracts/cli.md](../../contracts/cli.md) (shared launch contract) |
| [editor-desktop-host.md](editor-desktop-host.md) | Which native desktop host technology should turn the packaged Editor into a real graphical application while keeping the same Vue SPA, the same application/API boundary, and an independent Core? | Prototyped the strongest candidates against the real application and selected **PySide6 + Qt WebEngine**: it is the only candidate that embeds its own webview engine, so the Windows/Linux artifacts need no user-installed WebView2 or WebKitGTK; rejects pywebview (platform webview required) and Tauri + Python sidecar (Rust + sidecar + platform webview); records frozen/AppImage sizes, the Qt-consistency build fix, the bundled WebEngine resources, and the measured desktop self-check evidence | [workflow/packaging.md](../workflow/packaging.md), [architecture/index.md](../architecture/index.md), [user/how-to/install-the-editor.md](../../user/how-to/install-the-editor.md) |

Implementation history is maintained separately in
[docs/dev/history/implementation-slices.md](../history/implementation-slices.md).

## Outcome-card convention

Every document listed above is being brought to the conventions in
[../workflow/conventions.md](../workflow/conventions.md): front matter, an outcome card at the top,
and an explicit statement of the current contract that operationalizes its
outcome. Where an older document still mixes a proposed or historical shape with
current rules, the current rule lives in the linked contract.
