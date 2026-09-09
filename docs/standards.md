---
type: standards-and-provenance
status: active
source_of_truth_for:
  - standards-registry
  - symbol-asset-provenance-policy
read_when:
  - symbol-asset-work
  - standards-alignment-claim
  - agent-ingestion-of-external-material
update_when:
  - standards-edition-change
  - new-symbol-source-decision
  - provenance-policy-change
---

# Standards and Symbol Provenance

Governance/research slice behind
[ADR-0007](decisions/ADR-0007-standards-and-symbol-provenance.md). Recorded
2026-09-08. This page started as a documentation slice (no SVG symbol library,
renderer, or runtime provenance framework was introduced there); the basic
symbol pack and the headless process renderer have since been implemented
under the rules recorded here (see [svg-symbols.md](svg-symbols.md) and
[rendering.md](rendering.md)).

This document defines a durable boundary between four concerns that must never
be collapsed:

```text
normative engineering standards          ISO 10628-1/-2, ISO 14617-1/-2,
                                         ANSI/ISA-5.1, IEC 62424 (restricted)
open interoperability specifications     DEXPI 2.0 (CC BY 4.0)
DeepPlant implementation                 the semantic engineering model + tooling
redistributable graphical assets         DeepPlant SVG symbol assets (basic
                                         process pack, packaged under
                                         deepplant/assets/symbols/process/basic)
```

It answers the six governance questions:

| Question | Answer |
|---|---|
| Which standards guide DeepPlant? | ISO 10628-1/-2, ISO 14617-1/-2, ANSI/ISA-5.1, IEC 62424 as normative engineering references; DEXPI 2.0 as the open semantic/interchange specification. |
| Which standard content may be stored in the repository? | Official metadata, identifiers, and DeepPlant-authored summaries only. No normative tables, figures, symbol artwork, or substantial text from ISO/ISA/IEC publications. DEXPI 2.0 content may be stored where its CC BY 4.0 licence covers it, with attribution. |
| Which material may AI agents inspect? | Openly licensed specifications (DEXPI under CC BY 4.0), DeepPlant-authored summaries, and public material whose licence/terms explicitly permit AI use. For ISO, only ISO Open Data or other explicitly permitted material. Public availability alone is not permission for AI ingestion. |
| Where may graphical assets come from? | DeepPlant-original geometry and clearly permissively licensed sources with explicit provenance. Not from tracing or extracting restricted standard artwork. |
| When may DeepPlant claim standards alignment or compliance? | Only after human verification against an authorized copy. Until then the vocabulary is `reference` / `candidate-alignment`. Visual similarity is not compliance. |
| How must symbol provenance and licensing be recorded? | Every distributed symbol needs a provenance record covering author/origin, licence, modification state, upstream revision, intended standard, and verification state. See [Symbol Provenance Policy](#symbol-provenance-policy). |

## Restricted standards: copyright and AI constraints

ISO, ISA, and IEC publications are restricted copyrighted works. Their
restricted normative content is not free to copy, redistribute, trace, or feed
into AI systems. Copyright and redistribution are separate questions: a
copyrighted work may be openly licensed for reuse, while restricted content is
not open-licensed.

- ISO's public copyright policy states that ISO copyrighted content may not be
  used in AI/machine-learning systems except where ISO explicitly provides it
  as ISO Open Data under its applicable terms. Publicly visible does not mean
  AI-usable: agents must not ingest ISO-hosted catalogue or web content unless
  its applicable terms explicitly permit AI use. Purchased ISO PDFs, licensed
  ISO content, and other restricted ISO material stay restricted.
- ISA's published notice on its official standards pages states that ISA
  prohibits entering ISA intellectual property (standards, publications,
  training, or other materials) into any form of AI tool, and prohibits
  creating derivatives of ISA IP using AI without express written permission
  from ISA's CEO. ISA reserves rights for text/data mining and AI training.
- IEC publications are restricted and covered by IEC copyright and Webstore
  terms. DeepPlant treats IEC 62424 exactly like the other restricted
  standards: no copying of normative content, no AI ingestion without an
  explicit licence permitting it.

### Project rule — never do this

- Commit purchased ISO/ISA/IEC PDFs to the repository.
- Copy tables or figures from them.
- Extract their symbol images.
- Trace their symbol images.
- Embed screenshots from them.
- Reproduce substantial text from them.
- Send purchased/licensed standards to an AI system.
- Ask an AI system to derive SVG assets from those PDFs.
- Claim compliance from visual similarity or secondary sources.

### Human catalogue verification versus AI ingestion

Humans may manually use official catalogue pages to verify a standard's
identifier, edition, status, and official source. That manual verification does
not authorize AI ingestion of the page. For ISO, agents may use only ISO Open
Data or other material whose applicable terms explicitly permit AI use.

### What may be stored in the repository

- Standard identifiers, edition years, official source URLs, and role notes.
- Short, DeepPlant-authored summaries of *why* a standard is relevant.
- DEXPI 2.0 material where its CC BY 4.0 licence covers it, with the required
  attribution and a link to the licence (see [DEXPI](#dexpi)).
- Anything a rights holder has explicitly released under a compatible open
  licence, verified in writing.

## Standards registry

Edition/status data below reflects the identifiers and editions in the DeepPlant
project scope, cross-checked where official pages were machine-readable on
2026-09-08. iso.org and the IEC Webstore block automated retrieval, so the exact
ISO catalogue entries and confirmation dates must be re-verified by a human on
the official catalogue before any compliance-sensitive claim. This is also the
standing rule in the [verification vocabulary](#verification-vocabulary).

### Normative engineering references (restricted)

| Standard | Version | Role in DeepPlant | Current status | Official source | Repository handling | AI handling | Verification requirement |
|---|---|---|---|---|---|---|---|
| ISO 10628-1 | 2014 | Diagram structure and drafting reference for the diagrams DeepPlant derives (PFD/P&ID structure, layout logic). | Current edition in project scope; confirm on the ISO catalogue. | ISO catalogue / ISO Store — search `ISO 10628-1:2014`. | Metadata and DeepPlant-authored role summaries only. | Do not feed restricted content to AI tools. | Human check against an authorized copy before any structural-conformance claim. |
| ISO 10628-2 | 2012 | Normative graphical-symbol reference for the chemical and petrochemical process industry. Reference for future equipment symbols such as pump, heat exchanger, vessel. | Current edition in project scope; confirm on the ISO catalogue. | ISO catalogue / ISO Store — search `ISO 10628-2:2012`. | No symbol artwork, tables, or figures. | Do not feed restricted content to AI tools. Do not ask AI to derive symbol geometry from it. | Human verification per symbol before any `human-verified` alignment state. |
| ISO 14617-1 | 2025 | General rules for graphical symbols for diagrams (preparation and presentation of symbols). Relevant when DeepPlant authors original symbol geometry. | Current edition in project scope; confirm on the ISO catalogue. | ISO catalogue / ISO Store — search `ISO 14617-1:2025`. | Metadata and role summaries only. | Do not feed restricted content to AI tools. | Human review if DeepPlant claims its own symbols follow these rules. |
| ISO 14617-2 | 2025 | General industrial graphical-symbol reference. Broader scope than ISO 10628-2; secondary reference for generic component glyphs. | Current edition in project scope; confirm on the ISO catalogue. | ISO catalogue / ISO Store — search `ISO 14617-2:2025`. | No symbol artwork, tables, or figures. | Do not feed restricted content to AI tools. | Human verification before any symbol-correspondence claim. |
| ANSI/ISA-5.1 | 2024 | Instrumentation and control symbols and identification. Relevant to later P&ID instrumentation work, not the current PFD-level step glyphs. | Current edition (ANSI/ISA-5.1-2024) per ISA's official committee page. | [ISA-5.1 committee page](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa5-1). | Metadata and role summaries only. | ISA prohibits entering ISA IP into AI tools and prohibits AI-created derivatives without express written permission. | Human verification against an authorized copy before any ISA alignment claim. |
| IEC 62424 | 2016 | Later interoperability reference for P&ID ↔ process-control-engineering (PCE-CAE) exchange and representation of process control requests in P&IDs. | Current edition in project scope; confirm on the IEC Webstore. | IEC Webstore — search `IEC 62424:2016`. | Metadata and role summaries only. | Treat as restricted; verify licence before any AI use. | Human verification before any conformance/interoperability claim. |

### Open interoperability specification

| Standard | Version | Role in DeepPlant | Current status | Official source | Repository handling | AI handling | Verification requirement |
|---|---|---|---|---|---|---|---|
| DEXPI | 2.0 | Open semantic/interchange and information-model reference: semantic concepts, information-model mapping, interchange architecture, and graphics-data concepts. Not a drawing or symbol-style standard. | Published 2025-10-10 under CC BY 4.0 (official announcement and official GitLab repository both confirm the licence). | [DEXPI announcement](https://dexpi.org/dexpi-2-0-specification-published-a-new-standard-for-process-industry-data-exchange/); [gitlab.com/dexpi/Specification](https://gitlab.com/dexpi/Specification) (default branch `master`, tag `V2.0.0`). | CC BY 4.0 material may be stored/reproduced with attribution, licence link, and change indication. Embedded or third-party content must be checked to actually fall under the licence. | Agents may use the CC BY 4.0 specification with attribution; the licence permits sharing and adaptation including commercially. | Per-item check that reused material is actually covered by CC BY 4.0; semantic alignment vs DEXPI is a mapping concern, not a compliance claim. |

## DEXPI

DEXPI 2.0 is appropriate as an open source for:

```text
semantic concepts
information-model mapping
interchange architecture
graphics-data concepts
reference/test material where covered by the licence
```

The licence conclusion was confirmed from two official public sources on
2026-09-08: the DEXPI e.V. announcement (publication date 2025-10-10; published
under the Creative Commons Attribution 4.0 International (CC BY 4.0) license)
and the official GitLab specification repository, whose specification
documentation carries the CC BY 4.0 notice. DEXPI's 25 August 2026 update says
DEXPI 2.0.1 is being prepared; re-check the recommended DEXPI version before
implementing an adapter. This is a freshness note, not a claim that 2.0.1 has
been released.

The important distinction:

> DEXPI is not the drawing standard.

DEXPI's graphics model must not automatically become the visual symbol style of
DeepPlant. DEXPI describes how plant and diagram *information* is modelled and
exchanged; it does not authoritatively define a drawing style or a normatively
correct symbol appearance. Visual style stays a DeepPlant presentation-layer
decision with its own provenance (ADR-0003).

## Verification vocabulary

DeepPlant uses three conservative alignment states. The words *compliant* or
*conforming* are avoided until normative requirements have actually been
verified against an authorized source.

| State | Meaning |
|---|---|
| `reference` | DeepPlant consults the standard for direction, terminology, or structure. No correspondence claim is made for any concrete asset or model. |
| `candidate-alignment` | A model element or symbol is *intended* to correspond to a standard, but the correspondence has not been verified against an authorized copy. |
| `human-verified` | A named human checked the correspondence against an authorized copy of the standard and recorded the result (standard id, symbol/rule, date, verifier). |

Rules:

- Do not use “ISO compliant”, “ISA compliant”, or “standards compliant” until
  the relevant normative requirements are human-verified.
- Visual similarity is not compliance. Secondary sources (tutorials, blog
  images, third-party symbol packs that “look like” a standard) are evidence of
  intent, never proof of compliance.
- Symbol assets that merely resemble a standard figure are still independent
  copyright works with their own provenance; resemblance does not transfer the
  standard's copyright or grant any rights.

## Source-quality rule

Never assume any of the following:

```text
public GitHub repository           = reusable asset
visible on a website               = public domain
looks like ISO                     = ISO compliant
SVG file                           = freely redistributable
```

Every future imported graphical asset requires explicit provenance: a
verifiable upstream location, an identifiable copyright holder, an explicit
licence that permits DeepPlant's redistribution (AGPL-3.0 repository, commercial
use allowed), and a statement of whether the geometry was derived from
standards artwork. Sources with unclear provenance or noncommercial/incompatible
licences are rejected, not “kept under consideration”.

## Candidate graphical asset sources

Researched on 2026-09-08 at repository/file level. No assets were copied in this
slice.

### iot-solutions-ru/ispf — `ispf-pid-v1` pack

| Question | Finding |
|---|---|
| What is it? | A P&ID symbol pack shipped as generated JSON geometry packs (`isa.json`, `pumps.json`, `tanks.json`, `valves.json`, …) under `apps/web-console/src/scada/symbols/packs/ispf-pid-v1/`, generated from `tools/symbol-pack-isa/src/symbols.ts`. No standalone SVG files are committed in the pack. |
| Exact asset licence | The pack-level `LICENSE.md` says **“Apache-2.0 — original artwork by ISPF Core Contributors”**, then adds field-of-use restrictions: *“Inside ISPF SCADA mimic diagrams only”* and *“Do not republish this pack as a standalone icon library unrelated to ISPF.”* Those restrictions conflict with the Apache-2.0 grant, so the pack-level licence is internally inconsistent. |
| Repository-level licence | The repository `NOTICE` states the framework is AGPL-3.0 (“unless you have a separate commercial license agreement”), and the top-level `LICENSE` is AGPL-3.0. |
| Copyright holder | Claimed: “ISPF Core Contributors” (no individual/named entity). |
| Attribution / NOTICE requirements | Repo NOTICE exists; the pack's own licence text has no separate NOTICE file. Attribution practice for the pack is not demonstrated independently. |
| Modification permitted? | The generator README says symbols may be extended by editing the generator, but the pack's “mimic diagrams only” / no-standalone-republication clauses make downstream modification-and-redistribution ambiguous. |
| Commercial redistribution permitted? | Apache-2.0 would permit it; the pack-specific restrictions appear to forbid republishing the pack standalone, which conflicts. Ambiguous. |
| Is asset provenance documented? | Partially. `docs/en/pid-symbols-legal.md` asserts the geometry is original (“not traced, converted, or derived from Siemens SymbolFactory, TIA Portal, or other vendor WMF/SVG libraries”) and drawn to ISA-5.1/ISO 14617 *conventions*. That is an upstream claim, not independent verification. |
| Practical in an AGPL repository? | **Not approved for import.** The pack licence is internally inconsistent (Apache-2.0 header vs. field-of-use restrictions) and sits inside an AGPL-3.0 repository with an unclear copyright holder. |
| Action | Revisit only if the upstream rights holder clarifies in writing that the pack (or the generator's output) may be freely redistributed standalone under Apache-2.0 without field-of-use restrictions, with a named copyright holder. |

### jgraph/drawio — P&ID/process stencils and `pid2` shapes

| Question | Finding |
|---|---|
| What is it? | diagrams.net (draw.io) repository P&ID assets: XML stencils under `src/main/webapp/stencils/pid/` (pumps, vessels, heat exchangers, mixers, instruments, piping, …) and code-drawn shapes under `src/main/webapp/shapes/pid2/`. |
| Licence | The repository `LICENSE` is Apache-2.0. The `pid2` shape sources carry an explicit header: *“Copyright (c) 2006-2013, JGraph Holdings Ltd”*. The XML stencil files do **not** carry per-file author/licence headers. |
| Assessment | The `pid2` code (Apache-2.0, explicit JGraph copyright) is a plausible candidate. The `stencils/pid` XML files lack per-file provenance, and draw.io's product may distribute icon/stencil libraries under separate terms, so the licence scope for a specific geometry file must be confirmed before import. Standards correspondence of the shapes is unverified. |
| Verdict | Candidate for a later asset PR **only after** per-file licence/provenance confirmation and, where standards alignment is claimed, human verification. Nothing imported in this slice. |

### DEXPI reference material

The DEXPI 2.0 specification (official GitLab repository, tag `V2.0.0`) is CC BY
4.0, so semantic/information-model material and specification-derived reference
content can be reused with attribution. DeepPlant does **not** treat DEXPI as a
source of visual symbol style or drawing-standard artwork (see
[DEXPI](#dexpi)). Any specific file planned for reuse must be checked to be
covered by CC BY 4.0 (the repository also contains tooling and build content).

### IPD Studio historical/current symbol assets

| Scope | Finding | Verdict |
|---|---|---|
| Current IPD Studio (`v0.13.0+`) | The public upstream repository states that `v0.13.0` and later use PolyForm Noncommercial 1.0.0. It also identifies the project copyright as © 2026 Praharsh Nagpure. Current symbols/assets are therefore not acceptable for DeepPlant's commercially usable public symbol library. | **REJECTED** for DeepPlant asset reuse: PolyForm Noncommercial is incompatible with the project's commercial-use requirement. |
| Historical IPD Studio (`<= v0.12.1`) | Upstream states that versions through `v0.12.1` were AGPL-3.0-only and that the grant remains perpetual for recipients. This makes historical assets a possible licensing candidate, not an approved source. | **POTENTIAL CANDIDATE ONLY.** Before reuse, verify the exact tag/ref, exact asset path, copyright/provenance, that the asset existed under that AGPL release, whether it was independently authored, and whether it was modified later. |

A repository-level or historical licence alone is not sufficient evidence for a
concrete symbol import. No IPD Studio asset is approved or imported in this PR.

### Other open-source SVG P&ID libraries

No other source was cleared in this slice. Any future candidate is evaluated
under the [source-quality rule](#source-quality-rule) and the
[Symbol Provenance Policy](#symbol-provenance-policy) before a single file is
imported. A permissively licensed repository is not by itself sufficient; each
asset needs provenance.

## Symbol Provenance Policy

This is a documented requirement for future symbol assets, not yet a
machine-readable schema. A machine-readable provenance manifest is an accepted
future direction (see example below) but is **not implemented** in this slice,
and no asset-management framework is created.

Every distributed symbol must eventually be able to answer:

```text
Who created this geometry?
Under what licence may DeepPlant redistribute it?
Was it modified? (and how does it differ from upstream?)
Which upstream revision did it come from?
Which standards is it intended to correspond to?
Has that correspondence been human-verified?
```

Repository handling for imported assets, when imports begin:

- Record upstream repository, ref/commit, file path, author/copyright holder,
  licence identifier, and any modification, next to the asset or in a
  `THIRD_PARTY_NOTICES`-style attribution file.
- Keep the upstream licence text and preserve required NOTICE/attribution.
- Confirm the licence permits redistribution inside an AGPL-3.0 repository and
  commercial use; reject noncommercial or ambiguous licences.
- Default the standards-correspondence state to `candidate-alignment` (or
  `reference`) and never to `human-verified` without a recorded human check.

A future machine-readable provenance manifest is an acceptable direction, for
example:

```yaml
id: pump
asset_origin: deepplant-original
asset_license: AGPL-3.0-only
standards:
  - id: ISO 10628-2:2012
    verification: unverified
```

That example is illustrative only; it is not a schema to implement without a
concrete need.

## Initial seven process symbols assessment

The seven current `ProcessStep` types in the realistic process fragment
(`source`, `mixing`, `pump`, `heat_exchanger`, `splitting`, `vessel`, `sink`)
divide into two groups. `pump`, `heat_exchanger`, and `vessel` are candidates for
standards-aligned *equipment* geometry. `source`, `sink`, `mixing`, and
`splitting` are process-graph presentation concepts (boundaries and functions)
that must **not** be forced into an ISO equipment-symbol category. Nothing is
drawn in this slice.

| DeepPlant type | Engineering meaning (current model) | Likely normative reference | Physical equipment symbol or process-function glyph | Open-source asset candidate | Human verification required? |
|---|---|---|---|---|---|
| `source` | Graph boundary that supplies a feed into the process (e.g. `PS-feed`). | None forced. Process-boundary concept, not an equipment item. | Process-function/boundary glyph, not an equipment symbol. | None needed — DeepPlant-original glyph. | Only if an explicit standard correspondence is later asserted. |
| `mixing` | Process function merging ≥ 2 streams into 1 (e.g. `PS-mix`); explicit step with no required `Equipment`. | DEXPI 2.0 Process mixing concept (open, informational); no restricted ISO equipment symbol forced. | Process-function glyph (converging junction), not an equipment outline. | None needed — DeepPlant-original glyph. | Only if later mapped to a physical mixer and a correspondence is asserted. |
| `pump` | Pumping function that in a 1:1 realization is the pump equipment (`P-101`). | ISO 10628-2 pump symbols (normative reference; unverified here). | Real equipment symbol candidate (centrifugal-pump circle/arrow convention). | draw.io `pid2`/`pid` pump shapes (candidate, pending per-file licence confirmation); DeepPlant-original preferred. | **Required** before any `human-verified` alignment state. |
| `heat_exchanger` | Heat-exchange function on a selected process side (`E-101`); process graph currently exposes one side. | ISO 10628-2 heat-exchanger symbols (normative reference; unverified here). | Real equipment symbol candidate. | draw.io `pid` heat-exchanger shapes (candidate, pending confirmation); DeepPlant-original preferred. | **Required** before any `human-verified` alignment state. |
| `splitting` | Process function splitting 1 stream into ≥ 2 (e.g. `PS-split`); explicit step with no required `Equipment`. | DEXPI 2.0 Process splitting concept (open, informational); no restricted ISO equipment symbol forced. | Process-function glyph (diverging junction), not an equipment outline. | None needed — DeepPlant-original glyph. | Only if later mapped to a physical tee/manifold and a correspondence is asserted. |
| `vessel` | Containment function that in a 1:1 realization is the vessel equipment (`V-101`). | ISO 10628-2 vessel/tank symbols (normative reference; unverified here). | Real equipment symbol candidate. | draw.io `pid` vessel shapes (candidate, pending confirmation); DeepPlant-original preferred. | **Required** before any `human-verified` alignment state. |
| `sink` | Graph boundary receiving product for a downstream consumer (e.g. `PS-consumer`). | None forced. Process-boundary concept, not an equipment item. | Process-function/boundary glyph, not an equipment symbol. | None needed — DeepPlant-original glyph. | Only if an explicit standard correspondence is later asserted. |

The `pump` / `heat_exchanger` / `vessel` rows identify where a future symbol PR
may choose standards-informed equipment geometry. The process-function and
boundary rows (mixing, splitting, source, sink) are DeepPlant presentation
concepts for the process graph and should be drawn as independent DeepPlant
glyphs, not squeezed into equipment-symbol categories.

## Recommended future asset strategy

Three approaches were evaluated against legal clarity, commercial usability,
open-source redistribution, standards alignment, maintainability, and
AI-assisted development:

| Approach | Assessment |
|---|---|
| A. Independently authored DeepPlant SVG geometry | Highest legal clarity and maintainability; full AGPL-3.0-only control; no third-party provenance debt. Standards *alignment* then still depends on human verification, but there is no copyright entanglement with restricted standards. Preferred default. |
| B. Reuse/adaptation of clearly permissively licensed SVG assets | Valuable when a source has explicit provenance and a compatible licence. Today no source passed the bar completely: ISPF is ambiguous/restricted, draw.io `pid2` is promising but needs per-file confirmation, DEXPI is not a drawing-standard source. Use only case-by-case with full provenance records. |
| C. Licensed reproduction of normative standard artwork | Legally possible only under a licence from the standards body (paid) and it would complicate open redistribution. Rejected as the default for the public AGPL repository; not excluded forever, but requires a separate rights decision. |

Recommended strategy (mixed):

```text
DeepPlant-original process-function glyphs        source, sink, mixing, splitting, boundaries
+
independently authored or clearly permissively
licensed equipment symbols                       pump, heat_exchanger, vessel, later equipment
+
human standards verification                     per-symbol, recorded, before alignment claims
```

This keeps the public repository free of restricted artwork, gives DeepPlant
full control of the process-graph presentation vocabulary, permits commercial
use, and makes AI-assisted symbol development safe because the geometry is
authored from DeepPlant-controlled sources — never derived from restricted
standards content. Visual conventions may be informed by public knowledge of the
domain; correspondence claims still require the recorded human check.

## DEXPI relationship

Recorded explicitly so the three concerns are never collapsed:

```text
ISO/ISA/IEC               → normative engineering references
DEXPI                     → open semantic/interchange specification
DeepPlant SVG library     → implementation asset layer with independent provenance
```

- ISO 10628 / ISO 14617 / ANSI/ISA-5.1 / IEC 62424 are normative references:
  restricted, referenced by identifier, human-verified when alignment matters.
- DEXPI 2.0 is the open specification DeepPlant may use for semantic concepts,
  information-model mapping, interchange architecture, and graphics-data
  concepts under CC BY 4.0 with attribution. DEXPI is not the drawing standard,
  and its graphics model must not automatically become DeepPlant's visual
  symbol style.
- The DeepPlant SVG symbol assets are an implementation asset layer with
  independent provenance. The first process/PFD pack ships as the non-normative
  `basic` pack, packaged inside the Python package under
  `deepplant/assets/symbols/process/basic/` (contract:
  [svg-symbols.md](svg-symbols.md); consumed by [rendering.md](rendering.md)),
  as DeepPlant-original fallback geometry under AGPL-3.0-only. Future
  standards-aligned, company, and custom packs keep independent provenance and
  may carry their own licences.

## Research sources and access notes

Official/public sources consulted on 2026-09-08:

| Source | Used for | Notes |
|---|---|---|
| [DEXPI announcement (dexpi.org)](https://dexpi.org/dexpi-2-0-specification-published-a-new-standard-for-process-industry-data-exchange/) | DEXPI 2.0 release date and CC BY 4.0 licence. | Machine-readable; quoted above. |
| [gitlab.com/dexpi/Specification](https://gitlab.com/dexpi/Specification) | DEXPI licence text in the specification documentation (default branch `master`, tag `V2.0.0`). | Shallow clone inspected locally; licence notice confirmed in `src/documentation/index.rst`. |
| [ISA-5.1 committee page (isa.org)](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa5-1) | ANSI/ISA-5.1-2024 currency, scope, and ISA's AI-use prohibition notice. | Machine-readable; notice quoted in summary above. |
| ISO catalogue and ISO copyright policy (iso.org) | ISO 10628 / ISO 14617 edition status and ISO's copyright/AI policy. | ISO policy permits AI use only for ISO Open Data under applicable terms; publicly accessible ISO catalogue/web pages are not thereby AI-usable. A human may manually re-open catalogue pages to verify identifier, edition, status, and official source before compliance-sensitive use. |
| IEC Webstore (webstore.iec.ch) | IEC 62424:2016 status. | Automated retrieval blocked/JS-only; treat as restricted; confirm status on the Webstore before compliance-sensitive use. |
| [iot-solutions-ru/ispf](https://github.com/iot-solutions-ru/ispf) | ispf-pid-v1 pack licence and provenance. | Inspected at file level: `docs/en/pid-symbols-legal.md`, pack `LICENSE.md`, repo `NOTICE`/`LICENSE`, generator `tools/symbol-pack-isa/README.md`, pack JSON contents. |
| [jgraph/drawio](https://github.com/jgraph/drawio) | P&ID asset licensing context. | Inspected at file level: repository `LICENSE` (Apache-2.0) and `src/main/webapp/shapes/pid2/mxPidInstruments.js` copyright header. |
| [Coldbari/IPD-Studio](https://github.com/Coldbari/IPD-Studio) | Current and historical IPD Studio licensing assessment. | Upstream README states `v0.13.0+` are PolyForm Noncommercial 1.0.0 and versions through `v0.12.1` were AGPL-3.0-only with a perpetual recipient grant; this is not per-asset provenance approval. |
| [DEXPI August 2026 update](https://dexpi.org/dexpi-august-2026-update/) | DEXPI version freshness. | Published 2026-08-25; reports DEXPI 2.0.1 is being prepared, without a release-date claim. |

Related project documents:

- [ADR-0007 — restrict standards content and require symbol provenance](decisions/ADR-0007-standards-and-symbol-provenance.md)
- [Architecture](architecture.md) and [ADR-0003](decisions/ADR-0003-separate-semantic-and-presentation-models.md) for the semantic/presentation boundary.
- [Roadmap](roadmap.md) for the symbol-slice sequence.
