---
type: evidence
status: active
canonical_for:
  - standards-and-symbol-licensing-evidence
read_when:
  - symbol-source-investigation
  - licence-and-provenance-review
  - standards-research
update_when:
  - new-source-inspection
  - licence-finding-change
depends_on: []
decision:
  - docs/dev/decisions/ADR-0007-standards-and-symbol-provenance.md
evidence: []
superseded_by: null
---

# Standards and Symbol Licensing Evidence

## Outcome card

- **Question investigated:** What public/open sources, licences, provenance
  claims, and candidate graphical assets were inspected to justify DeepPlant's
  standards and symbol-provenance policy?
- **Status:** open evidence — the main conclusions are already operating as
  current policy and reference, but the candidate-asset findings stay unresolved
  where an upstream licence was ambiguous, internally inconsistent, or
  unreachable.
- **Inspection scope and dates:** public/open sources inspected at repository/
  file level on **2026-09-08** (DEXPI official sources, ISA/ISO/IEC public pages,
  ISPF `ispf-pid-v1`, draw.io P&ID assets, IPD Studio); DEXPI version-freshness
  re-checks on **2026-08-25**, **2026-09-14**, and **2026-09-21**; IPD Studio
  upstream re-check on **2026-09-30**. The original governance/research slice
  was recorded 2026-09-08. No asset was imported, and no restricted standards
  content was ingested.
- **Conclusions:**
  - DEXPI 2.0 is published under CC BY 4.0 (confirmed from two official public
    sources on 2026-09-08) and may be used with attribution, including
    commercially, where a specific item is actually covered by the licence.
  - ISPF `ispf-pid-v1` is **not approved for import**: its pack licence is
    internally inconsistent (Apache-2.0 header vs. field-of-use restrictions)
    inside an AGPL-3.0 repository with an unclear copyright holder.
  - draw.io `pid2` code is a plausible candidate pending per-file licence
    confirmation; the XML `stencils/pid` files lack per-file provenance.
  - IPD Studio current assets (`v0.13.0+`, PolyForm Noncommercial) are rejected;
    historical assets (`<= v0.12.1`, AGPL-3.0-only) are a potential candidate
    only, and a 2026-09-30 re-check could not re-confirm the upstream licence.
  - Independently authored DeepPlant geometry is the preferred default, because
    it has the highest legal clarity and no third-party provenance debt.
- **Resulting ADRs:**
  [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md).
- **Current policy/reference operationalizing the result:**
  policy = [standards.md](../workflow/standards.md); registry =
  [standards-registry.md](../reference/standards-registry.md); decision =
  [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md).
- **Conditions for revisiting:** an upstream source clarifies its licence in
  writing; a new candidate asset source appears; a DEXPI version change is
  proposed; or a symbol-import PR needs per-asset provenance.

**This document does not own current rules.** It records what was investigated
and found. The rules are in [standards.md](../workflow/standards.md); the current
reference set is in
[standards-registry.md](../reference/standards-registry.md).

## Slice provenance

This was the governance/research slice behind
[ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md), recorded
2026-09-08. It began as a documentation slice: no SVG symbol library, renderer,
or runtime provenance framework was introduced by it. The `basic` symbol pack and
the headless process renderer were implemented later under the rules this slice
produced (see [dev/reference/svg-symbols.md](../reference/svg-symbols.md) and
[contracts/rendering.md](../../contracts/rendering.md)).

Under [ADR-0015](../decisions/ADR-0015-documentation-architecture-v2-1.md) this
material was split by authority: the active policy moved to
[standards.md](../workflow/standards.md), the reference set to
[standards-registry.md](../reference/standards-registry.md), and the
investigation remained here as evidence, with its original inspection dates
preserved.

## DEXPI licence and release evidence

The licence conclusion was confirmed from two official public sources on
2026-09-08: the DEXPI e.V. announcement (publication date 2025-10-10; published
under the Creative Commons Attribution 4.0 International (CC BY 4.0) license) and
the official GitLab specification repository, whose specification documentation
carries the CC BY 4.0 notice.

Version-freshness observations:

- DEXPI's 25 August 2026 update (published 2026-08-25) says DEXPI 2.0.1 is being
  prepared (“corrections and clarifications in the Process Model”) and that the
  DEXPI Profile is under development, without a release-date claim.
- The DEXPI September 2026 update (published 2026-09-14) announced no 2.0.1
  release (it refers only to “DEXPI Specification 2.0”); it reports that the
  P&ID 1.4 testing campaign (May–July 2026) found gaps in attribute mapping and
  graphical consistency, and that the Testing Procedure will be adapted for
  DEXPI 2.0.
- As of the 2026-09-21 inspection the stable target remained `V2.0.0`.

This is a freshness record, not a claim that 2.0.1 has been released, and not a
decision to change the referenced version. The recorded reference state lives in
[standards-registry.md](../reference/standards-registry.md).

## Candidate graphical asset sources

Researched on 2026-09-08 at repository/file level. No assets were copied in that
slice, and none has been imported since.

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
| Verdict | Candidate for a later asset PR **only after** per-file licence/provenance confirmation and, where standards alignment is claimed, human verification. Nothing imported. |

### DEXPI reference material

The DEXPI 2.0 specification (official GitLab repository, tag `V2.0.0`) is CC BY
4.0, so semantic/information-model material and specification-derived reference
content can be reused with attribution. DeepPlant does **not** treat DEXPI as a
source of visual symbol style or drawing-standard artwork. Any specific file
planned for reuse must be checked to be covered by CC BY 4.0 (the repository also
contains tooling and build content).

### IPD Studio historical/current symbol assets

| Scope | Finding | Verdict |
|---|---|---|
| Current IPD Studio (`v0.13.0+`) | The public upstream repository states that `v0.13.0` and later use PolyForm Noncommercial 1.0.0. It also identifies the project copyright as © 2026 Praharsh Nagpure. Current symbols/assets are therefore not acceptable for DeepPlant's commercially usable public symbol library. | **REJECTED** for DeepPlant asset reuse: PolyForm Noncommercial is incompatible with the project's commercial-use requirement. |
| Historical IPD Studio (`<= v0.12.1`) | Upstream states that versions through `v0.12.1` were AGPL-3.0-only and that the grant remains perpetual for recipients. This makes historical assets a possible licensing candidate, not an approved source. A 2026-09-30 re-check could not re-confirm this from upstream (see the [reference-products.md](reference-products.md) record). | **POTENTIAL CANDIDATE ONLY.** Before reuse, verify the exact tag/ref, exact asset path, copyright/provenance, that the asset existed under that AGPL release, whether it was independently authored, and whether it was modified later. |

A repository-level or historical licence alone is not sufficient evidence for a
concrete symbol import. No IPD Studio asset is approved or imported.

### Other open-source SVG P&ID libraries

No other source was cleared. Any future candidate is evaluated under the policy
[source-quality rule](../workflow/standards.md#source-quality-rule) and the
[Symbol Provenance Policy](../workflow/standards.md#symbol-provenance-policy)
before a single file is imported. A permissively licensed repository is not by
itself sufficient; each asset needs provenance.

## Initial seven process symbols assessment

> Terminology update (ADR-0009): the seven items below are **presentation
> symbol roles** used by the `basic` pack and the realistic fragment's diagram
> (`source`, `mixing`, `pump`, `heat_exchanger`, `splitting`, `vessel`,
> `sink`). They are distinct from the canonical engineering functions stored on
> `ProcessStep.function` (`source`, `mixing`, `pumping`, `heat_exchange`,
> `splitting_material`, `unspecified`, `sink`); the table keeps the role names
> because the assessment is about drawing assets.

The seven symbol roles used by the realistic process fragment
(`source`, `mixing`, `pump`, `heat_exchanger`, `splitting`, `vessel`, `sink`)
divide into two groups. `pump`, `heat_exchanger`, and `vessel` are candidates for
standards-aligned *equipment* geometry. `source`, `sink`, `mixing`, and
`splitting` are process-graph presentation concepts (boundaries and functions)
that must **not** be forced into an ISO equipment-symbol category. Nothing was
drawn by this assessment.

| Presentation symbol role | Engineering function (canonical) / meaning | Likely normative reference | Physical equipment symbol or process-function glyph | Open-source asset candidate | Human verification required? |
|---|---|---|---|---|---|
| `source` | `source` — graph boundary that supplies a feed into the process (e.g. `PS-feed`). | None forced. Process-boundary concept, not an equipment item. | Process-function/boundary glyph, not an equipment symbol. | None needed — DeepPlant-original glyph. | Only if an explicit standard correspondence is later asserted. |
| `mixing` | `mixing` — process function merging ≥ 2 streams into 1 (e.g. `PS-mix`); explicit step with no required `Equipment`. | DEXPI 2.0 Process mixing concept (open, informational); no restricted ISO equipment symbol forced. | Process-function glyph (converging junction), not an equipment outline. | None needed — DeepPlant-original glyph. | Only if later mapped to a physical mixer and a correspondence is asserted. |
| `pump` | `pumping` — function that in a 1:1 realization is the pump equipment (`P-101`). | ISO 10628-2 pump symbols (normative reference; unverified here). | Real equipment symbol candidate (centrifugal-pump circle/arrow convention). | draw.io `pid2`/`pid` pump shapes (candidate, pending per-file licence confirmation); DeepPlant-original preferred. | **Required** before any `human-verified` alignment state. |
| `heat_exchanger` | `heat_exchange` — function on a selected process side (`E-101`); process graph currently exposes one side. | ISO 10628-2 heat-exchanger symbols (normative reference; unverified here). | Real equipment symbol candidate. | draw.io `pid` heat-exchanger shapes (candidate, pending confirmation); DeepPlant-original preferred. | **Required** before any `human-verified` alignment state. |
| `splitting` | `splitting_material` — process function splitting 1 stream into ≥ 2 (e.g. `PS-split`); explicit step with no required `Equipment`. | DEXPI 2.0 Process splitting concept (open, informational); no restricted ISO equipment symbol forced. | Process-function glyph (diverging junction), not an equipment outline. | None needed — DeepPlant-original glyph. | Only if later mapped to a physical tee/manifold and a correspondence is asserted. |
| `vessel` | `unspecified` for `PS-vessel` (a vessel drawing is presentation evidence, not a storage-function claim; ADR-0009). | ISO 10628-2 vessel/tank symbols (normative reference; unverified here). | Real equipment symbol candidate. | draw.io `pid` vessel shapes (candidate, pending confirmation); DeepPlant-original preferred. | **Required** before any `human-verified` alignment state. |
| `sink` | `sink` — graph boundary receiving product for a downstream consumer (e.g. `PS-consumer`). | None forced. Process-boundary concept, not an equipment item. | Process-function/boundary glyph, not an equipment symbol. | None needed — DeepPlant-original glyph. | Only if an explicit standard correspondence is later asserted. |

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

The current **rule** this comparison produced — DeepPlant-original geometry is
the default, with third-party imports allowed only under explicit permissive
licences and full provenance — is stated in
[standards.md](../workflow/standards.md#symbol-provenance-policy) and decided in
[ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md). This
document preserves the comparison and reasoning behind that rule; it does not
restate it as a second policy.

## Research sources and access notes

Official/public sources consulted on 2026-09-08:

| Source | Used for | Notes |
|---|---|---|
| [DEXPI announcement (dexpi.org)](https://dexpi.org/dexpi-2-0-specification-published-a-new-standard-for-process-industry-data-exchange/) | DEXPI 2.0 release date and CC BY 4.0 licence. | Machine-readable; quoted above. |
| [gitlab.com/dexpi/Specification](https://gitlab.com/dexpi/Specification) | DEXPI licence text in the specification documentation (default branch `master`, tag `V2.0.0`). | Shallow clone inspected locally; licence notice confirmed in `src/documentation/index.rst`. |
| [ISA-5.1 committee page (isa.org)](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa5-1) | ANSI/ISA-5.1-2024 currency, scope, and ISA's AI-use prohibition notice. | Machine-readable; notice summarised above. |
| ISO catalogue and ISO copyright policy (iso.org) | ISO 10628 / ISO 14617 edition status and ISO's copyright/AI policy. | ISO policy permits AI use only for ISO Open Data under applicable terms; publicly accessible ISO catalogue/web pages are not thereby AI-usable. A human may manually re-open catalogue pages to verify identifier, edition, status, and official source before compliance-sensitive use. |
| IEC Webstore (webstore.iec.ch) | IEC 62424:2016 status. | Automated retrieval blocked/JS-only; treat as restricted; confirm status on the Webstore before compliance-sensitive use. |
| [iot-solutions-ru/ispf](https://github.com/iot-solutions-ru/ispf) | ispf-pid-v1 pack licence and provenance. | Inspected at file level: `docs/en/pid-symbols-legal.md`, pack `LICENSE.md`, repo `NOTICE`/`LICENSE`, generator `tools/symbol-pack-isa/README.md`, pack JSON contents. |
| [jgraph/drawio](https://github.com/jgraph/drawio) | P&ID asset licensing context. | Inspected at file level: repository `LICENSE` (Apache-2.0) and `src/main/webapp/shapes/pid2/mxPidInstruments.js` copyright header. |
| [Coldbari/IPD-Studio](https://github.com/Coldbari/IPD-Studio) | Current and historical IPD Studio licensing assessment. | Upstream README states `v0.13.0+` are PolyForm Noncommercial 1.0.0 and versions through `v0.12.1` were AGPL-3.0-only with a perpetual recipient grant; this is not per-asset provenance approval. |
| [DEXPI August 2026 update](https://dexpi.org/dexpi-august-2026-update/) | DEXPI version freshness. | Published 2026-08-25; reports DEXPI 2.0.1 is being prepared (“corrections and clarifications in the Process Model”) and that the DEXPI Profile is under development, without a release-date claim. |
| [DEXPI September 2026 update](https://dexpi.org/dexpi-september-2026-update/) | DEXPI version freshness re-verified before the Plant/P&ID spike. | Published 2026-09-14; no 2.0.1 release announcement (refers only to “DEXPI Specification 2.0”); reports that the P&ID 1.4 testing campaign (May–July 2026) found gaps in attribute mapping and graphical consistency, and that the Testing Procedure will be adapted for DEXPI 2.0. Confirms that as of the 2026-09-21 inspection the stable target remains `V2.0.0`. |
| [DEXPI Specification `V2.0.0` archive](https://gitlab.com/dexpi/Specification/-/archive/V2.0.0/Specification-V2.0.0.tar.gz) | Primary semantic evidence for the Plant/P&ID spike: `src/model/Plant/**`, `src/model/Core/**` model definitions and `src/documentation/_static/reference_pid.xml` (the official DEXPI Reference P&ID instance). | CC BY 4.0; inspected 2026-09-21 in a temporary directory outside the repository; nothing vendored. Findings in [dexpi/plant-pid-semantic-boundary.md](dexpi/plant-pid-semantic-boundary.md), decision in ADR-0010. |

## Human-verification and open questions

Human verification requirements discovered through this investigation (now
stated as policy in [standards.md](../workflow/standards.md)):

- Any compliance/alignment claim needs a named human check against an authorized
  copy of the standard; the three-state vocabulary
  (`reference` / `candidate-alignment` / `human-verified`) is the recording
  mechanism.
- Official catalogue pages must be re-opened by a human before a
  compliance-sensitive claim; machine-readable retrieval was not available for
  the ISO catalogue or the IEC Webstore.

Deliberately unresolved items:

- Whether ISPF will clarify its pack licence in writing so the pack (or the
  generator's output) may be redistributed standalone under Apache-2.0 without
  field-of-use restrictions.
- Whether draw.io's `stencils/pid` XML files carry a per-file licence scope that
  would permit redistribution.
- The current authoritative upstream location and licence of IPD Studio's
  historical AGPL assets, and whether any specific asset was independently
  authored under that release.

None of these unresolved items is an approved import or dependency.

## Related

- [standards.md](../workflow/standards.md) — the current policy that
  operationalizes these findings.
- [standards-registry.md](../reference/standards-registry.md) — the current
  standard/specification reference set.
- [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md) — the
  durable decision resulting from this investigation.
- [reference-products.md](reference-products.md) — the broader reuse landscape
  and its IPD Studio re-check note.
- [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md)
  — the semantic/presentation boundary that keeps drawing style a DeepPlant
  presentation decision.
