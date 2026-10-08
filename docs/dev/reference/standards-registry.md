---
type: reference
status: active
canonical_for:
  - standards-registry
read_when:
  - standards-lookup
  - standards-alignment-claim
  - dexpi-version-pinning
update_when:
  - standards-edition-change
  - project-reference-set-change
depends_on: []
decision:
  - docs/dev/decisions/ADR-0007-standards-and-symbol-provenance.md
evidence:
  - docs/dev/research/standards-licensing-evidence.md
superseded_by: null
---

# Standards Registry

> **Question this document answers:** which standards and specifications are
> currently relevant to DeepPlant, what role does each play, and what
> project-level handling applies?

This is the current developer **reference** catalogue. It is not the policy and
not the research record: the rules that govern use of this material are in
[standards.md](../workflow/standards.md), and the source/licence investigation
is in
[standards-licensing-evidence.md](../research/standards-licensing-evidence.md).

Edition/status data below reflects the identifiers and editions in the DeepPlant
project scope, cross-checked where official pages were machine-readable on
2026-09-08. iso.org and the IEC Webstore block automated retrieval, so the exact
ISO catalogue entries and confirmation dates must be re-verified by a human on
the official catalogue before any compliance-sensitive claim (the standing rule
in [standards.md](../workflow/standards.md#verification-vocabulary)).

The **handling** column is a classification, not a restatement of the rule:
`metadata only` means identifiers, editions, sources, and DeepPlant-authored
role summaries may be stored; `restricted` means the material is a restricted
normative reference for both storage and AI use. The full rule is in
[standards.md](../workflow/standards.md).

## Normative engineering references (restricted)

| Standard | Version | Role in DeepPlant | Current status | Official source | Repository handling | AI handling | Verification requirement |
|---|---|---|---|---|---|---|---|
| ISO 10628-1 | 2014 | Diagram structure and drafting reference for the diagrams DeepPlant derives (PFD/P&ID structure, layout logic). | Current edition in project scope; confirm on the ISO catalogue. | ISO catalogue / ISO Store — search `ISO 10628-1:2014`. | Metadata and DeepPlant-authored role summaries only. | Restricted — see [policy](../workflow/standards.md). | Human check against an authorized copy before any structural-conformance claim. |
| ISO 10628-2 | 2012 | Normative graphical-symbol reference for the chemical and petrochemical process industry. Reference for future equipment symbols such as pump, heat exchanger, vessel. | Current edition in project scope; confirm on the ISO catalogue. | ISO catalogue / ISO Store — search `ISO 10628-2:2012`. | No symbol artwork, tables, or figures. | Restricted — see [policy](../workflow/standards.md). | Human verification per symbol before any `human-verified` alignment state. |
| ISO 14617-1 | 2025 | General rules for graphical symbols for diagrams (preparation and presentation of symbols). Relevant when DeepPlant authors original symbol geometry. | Current edition in project scope; confirm on the ISO catalogue. | ISO catalogue / ISO Store — search `ISO 14617-1:2025`. | Metadata and role summaries only. | Restricted — see [policy](../workflow/standards.md). | Human review if DeepPlant claims its own symbols follow these rules. |
| ISO 14617-2 | 2025 | General industrial graphical-symbol reference. Broader scope than ISO 10628-2; secondary reference for generic component glyphs. | Current edition in project scope; confirm on the ISO catalogue. | ISO catalogue / ISO Store — search `ISO 14617-2:2025`. | No symbol artwork, tables, or figures. | Restricted — see [policy](../workflow/standards.md). | Human verification before any symbol-correspondence claim. |
| ISO 15519-2 | 2015 | Diagrams for the process industry; representation of measurement, control, and instrumentation, relevant to P&ID instrumentation symbols. Reference direction for the `instrument.local` base graphic. | Current edition in project scope; confirm on the ISO catalogue. | ISO catalogue / ISO Store — search `ISO 15519-2:2015`. | Metadata and DeepPlant-authored role summaries only; no normative figures/tables/symbol artwork. | Restricted — see [policy](../workflow/standards.md). | Human verification against an authorized copy before any `human-verified` correspondence claim. |
| ANSI/ISA-5.1 | 2024 | Instrumentation and control symbols and identification. Relevant to later P&ID instrumentation work, not the current PFD-level step glyphs. | Current edition (ANSI/ISA-5.1-2024) per ISA's official committee page. | [ISA-5.1 committee page](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa5-1). | Metadata and role summaries only. | ISA prohibits entering ISA IP into AI tools and prohibits AI-created derivatives without express written permission — see [policy](../workflow/standards.md). | Human verification against an authorized copy before any ISA alignment claim. |
| IEC 62424 | 2016 | Later interoperability reference for P&ID ↔ process-control-engineering (PCE-CAE) exchange and representation of process control requests in P&IDs. | Current edition in project scope; confirm on the IEC Webstore. | IEC Webstore — search `IEC 62424:2016`. | Metadata and role summaries only. | Restricted — verify licence before any AI use; see [policy](../workflow/standards.md). | Human verification before any conformance/interoperability claim. |

## Open interoperability specification

| Standard | Version | Role in DeepPlant | Current status | Official source | Repository handling | AI handling | Verification requirement |
|---|---|---|---|---|---|---|---|
| DEXPI | 2.0 | Open semantic/interchange and information-model reference: semantic concepts, information-model mapping, interchange architecture, and graphics-data concepts. Not a drawing or symbol-style standard. | Published 2025-10-10 under CC BY 4.0 (official announcement and official GitLab repository both confirm the licence). | [DEXPI announcement](https://dexpi.org/dexpi-2-0-specification-published-a-new-standard-for-process-industry-data-exchange/); [gitlab.com/dexpi/Specification](https://gitlab.com/dexpi/Specification) (default branch `master`, tag `V2.0.0`). | CC BY 4.0 material may be stored/reproduced with attribution, licence link, and change indication. Embedded or third-party content must be checked to actually fall under the licence. | Agents may use the CC BY 4.0 specification with attribution; the licence permits sharing and adaptation including commercially. | Per-item check that reused material is actually covered by CC BY 4.0; semantic alignment vs DEXPI is a mapping concern, not a compliance claim. |

## DEXPI reference state

DEXPI is one of the project reference specifications. It is appropriate as an
open source for:

```text
semantic concepts
information-model mapping
interchange architecture
graphics-data concepts
reference/test material where covered by the licence
```

Recorded project reference state:

```text
specification: DEXPI
reference version: 2.0
repository tag inspected: V2.0.0 (default branch master)
licence: CC BY 4.0 with attribution
role: open semantic/interchange specification
```

DEXPI's role boundary is stated in the policy: DEXPI is **not** the DeepPlant
drawing standard, and its graphics model must not automatically become the
DeepPlant visual symbol style
([standards.md](../workflow/standards.md#dexpi-policy-boundary),
[ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md)).
Official sources are the DEXPI announcement and the official GitLab
specification repository listed above.

Version-freshness observations, the licence conclusion, and the official pages
inspected (with their dates) are recorded in the
[standards licensing evidence](../research/standards-licensing-evidence.md). A
change to the referenced DEXPI version is a registry update, driven by that
evidence rather than by an unrelated version announcement.

## Related

- [standards.md](../workflow/standards.md) — the active policy governing use of
  this reference set.
- [standards-licensing-evidence.md](../research/standards-licensing-evidence.md)
  — the source, licence, and provenance investigation.
- [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md) — the
  durable decision constraining this registry.
- [dev/reference/dexpi-process-adapter.md](dexpi-process-adapter.md) — the DEXPI
  Process adapter contract (supported subset, directions, and limits).
