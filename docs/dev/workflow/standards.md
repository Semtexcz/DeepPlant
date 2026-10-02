---
type: governance
status: active
canonical_for:
  - standards-usage-policy
  - symbol-asset-provenance-policy
read_when:
  - symbol-asset-work
  - standards-alignment-claim
  - agent-ingestion-of-external-material
update_when:
  - standards-usage-policy-change
  - provenance-policy-change
depends_on:
  - docs/dev/reference/standards-registry.md
decision:
  - docs/dev/decisions/ADR-0007-standards-and-symbol-provenance.md
evidence:
  - docs/dev/research/standards-licensing-evidence.md
superseded_by: null
---

# Standards Usage and Symbol Provenance Policy

> **Question this document answers:** what rules must DeepPlant contributors and
> agents follow when using standards material, claiming standards alignment, or
> distributing symbol assets, and what provenance must a distributed asset
> carry?

This is the **active governance policy** behind
[ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md). Policy,
registry, and evidence are deliberately separate authorities:

```text
policy    this document                          what rules apply now
registry  ../reference/standards-registry.md     which standards are in scope,
                                                 and each one's role
evidence  ../research/standards-licensing-evidence.md
                                                 what was inspected, when, and
                                                 what was found
```

The current reference set is recorded in the
[standards registry](../reference/standards-registry.md); the investigation that
produced these rules is recorded in the
[standards licensing evidence](../research/standards-licensing-evidence.md). This
document states only what must be done now, and it is the single canonical home
for those rules.

## Current boundary

Four concerns must never be collapsed:

```text
normative engineering standards          ISO 10628-1/-2, ISO 14617-1/-2,
                                         ANSI/ISA-5.1, IEC 62424 (restricted)
open interoperability specifications     DEXPI 2.0 (CC BY 4.0)
DeepPlant implementation                 the semantic engineering model + tooling
redistributable graphical assets         DeepPlant SVG symbol assets (basic
                                         process pack, packaged under
                                         deepplant/assets/symbols/process/basic)
```

```text
ISO / ISA / IEC    → restricted normative references
DEXPI              → open semantic/interchange specification
DeepPlant assets   → independent implementation assets with provenance
```

- **restricted normative reference** — the normative content is copyright
  restricted; it is never redistributed and never fed to AI systems without an
  explicit licence permitting that use. DeepPlant references it by identifier and
  verifies it by hand when alignment matters.
- **open semantic/interchange specification** — openly licensed material that may
  be used subject to its licence terms and required attribution; it is not the
  DeepPlant drawing standard.
- **independent implementation asset with provenance** — an asset owned by
  DeepPlant or licensed for redistribution, carrying its own recorded origin,
  licence, and verification state.

## Policy summary

| Question | Current rule |
|---|---|
| Which standards guide DeepPlant? | The current reference set and each standard's role are recorded in the [standards registry](../reference/standards-registry.md); this policy governs how that material may be used. |
| Which standard content may be stored in the repository? | Official metadata, identifiers, and DeepPlant-authored summaries only. No normative tables, figures, symbol artwork, or substantial text from ISO/ISA/IEC publications. DEXPI 2.0 content may be stored where its CC BY 4.0 licence covers it, with attribution. |
| Which material may AI agents inspect? | Openly licensed specifications (DEXPI under CC BY 4.0), DeepPlant-authored summaries, and public material whose licence/terms explicitly permit AI use. For ISO, only ISO Open Data or other explicitly permitted material. Public availability alone is not permission for AI ingestion. |
| Where may graphical assets come from? | DeepPlant-original geometry and clearly permissively licensed sources with explicit provenance. Not from tracing or extracting restricted standard artwork. See [Symbol Provenance Policy](#symbol-provenance-policy). |
| When may DeepPlant claim standards alignment or compliance? | Only after human verification against an authorized copy. Until then the vocabulary is `reference` / `candidate-alignment`. Visual similarity is not compliance. See [Verification vocabulary](#verification-vocabulary). |
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
  attribution and a link to the licence.
- Anything a rights holder has explicitly released under a compatible open
  licence, verified in writing.

## DEXPI policy boundary

DEXPI material covered by CC BY 4.0 may be used with the required attribution,
including commercially, where the specific material is actually covered by that
licence. Two rules constrain that use.

> DEXPI is not the drawing standard.

DEXPI's graphics model must not automatically become the visual symbol style of
DeepPlant. DEXPI describes how plant and diagram *information* is modelled and
exchanged; it does not authoritatively define a drawing style or a normatively
correct symbol appearance. Visual style stays a DeepPlant presentation-layer
decision with its own provenance
([ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
[ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md)).

Reused DEXPI material must be checked to actually fall under the applicable open
licence; any embedded or third-party content carries its own terms. The current
DEXPI reference and its official sources are recorded in the
[standards registry](../reference/standards-registry.md); the licence conclusion
and its sources are recorded in the
[standards licensing evidence](../research/standards-licensing-evidence.md).

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

Why a given source was accepted or rejected is evidence, recorded in the
[standards licensing evidence](../research/standards-licensing-evidence.md); this
policy states only the acceptance test.

## Symbol Provenance Policy

This is a documented requirement for future symbol assets, not yet a
machine-readable schema. A machine-readable provenance manifest is an accepted
future direction (see example below) but is **not implemented**, and no
asset-management framework is created.

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

DeepPlant-original geometry is the default for distributed symbols. The shipped
`basic` process pack is non-normative DeepPlant-original fallback geometry under
AGPL-3.0-only, packaged inside the Python package under
`deepplant/assets/symbols/process/basic/` (contract:
[dev/reference/svg-symbols.md](../reference/svg-symbols.md); consumed by
[contracts/rendering.md](../../contracts/rendering.md)). A future
standards-aligned, company, or custom pack keeps independent provenance and may
carry its own licence, subject to this policy.

## Related

- [ADR-0007 — restrict standards content and require symbol provenance](../decisions/ADR-0007-standards-and-symbol-provenance.md)
  — the durable decision this policy operationalizes.
- [standards-registry.md](../reference/standards-registry.md) — the current
  standard/specification reference set and each standard's role.
- [standards-licensing-evidence.md](../research/standards-licensing-evidence.md)
  — the source, licence, and provenance investigation behind these rules.
- [svg-symbols.md](../reference/svg-symbols.md) and
  [contracts/rendering.md](../../contracts/rendering.md) — the asset/anchor
  contract and the renderer that consume the `basic` pack under this policy.
- [AGENTS.md](../../../AGENTS.md) — the Licensed Standards instruction for
  agents.
