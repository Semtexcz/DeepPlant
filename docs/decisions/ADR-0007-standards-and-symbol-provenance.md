# ADR-0007: Restrict Standards Content and Require Symbol Provenance

> Status: Accepted
> Date: 2026-09-08

## Context

The roadmap's next presentation slices (SVG symbol + anchor contract, then a
basic read-only renderer) will add distributed graphical assets to a public
AGPL-3.0 repository. DeepPlant is a process-plant semantic-engineering platform
that wants to align, where appropriate, with established standards: ISO
10628-1/-2, ISO 14617-1/-2, ANSI/ISA-5.1, IEC 62424, and the open DEXPI 2.0
specification.

ISO, ISA, and IEC publications are restricted copyrighted works. ISO's public
copyright policy states that ISO copyrighted content may not be used in AI
systems except where ISO explicitly provides it as ISO Open Data. ISA's
published policy prohibits entering ISA intellectual property into AI tools and
prohibits AI-created derivatives without express written permission from ISA's
CEO. IEC publications are similarly restricted under IEC copyright and Webstore
terms. Normative content from these bodies therefore must not enter the public
repository or AI workflows.

DEXPI 2.0 is different: it is published under CC BY 4.0 (confirmed on the
official DEXPI announcement of 2025-10-10 and in the official GitLab
specification repository). It is an open semantic/interchange and
information-model specification — not a drawing or symbol-style standard.

Detailed research and the standards registry live in
[docs/standards.md](../standards.md); this ADR records only the stable decision.

## Decision

- DeepPlant does **not** redistribute restricted standards content. Normative
  standards are referenced by identifier and verified by humans where
  necessary.
- AI agents work only from openly licensed standards material, DeepPlant-authored
  summaries, and public material whose applicable terms explicitly permit AI
  use. For ISO, public availability alone is not permission for AI ingestion;
  licensed, restricted, or otherwise non-permitted ISO/IEC/ISA content is never
  provided to AI tools.
- All distributed symbol assets require explicit redistributable provenance:
  origin/author, licence, modification state, upstream revision, intended
  standard, and human-verification state.
- Standards correspondence and asset copyright are separate concerns. Visual
  similarity is not compliance; alignment claims use the conservative states
  `reference` / `candidate-alignment` / `human-verified` defined in
  `docs/standards.md`.
- DEXPI may be directly used where its CC BY 4.0 licence permits, with the
  required attribution. DEXPI is an open interoperability/semantic reference,
  not the DeepPlant drawing standard, and its graphics model does not dictate
  DeepPlant's symbol style.
- DeepPlant-original geometry is the default for distributed symbols (AGPL-3.0-only);
  permissively licensed third-party assets may be imported only with complete
  provenance records and a licence compatible with the AGPL-3.0 repository and
  commercial redistribution.

## Consequences

### Positive

- The public repository stays free of restricted normative artwork and
  standards PDFs, protecting redistributors and downstream users.
- AI-assisted symbol development is safe: agents work only from public/openly
  licensed material and DeepPlant-authored summaries.
- Future symbol PRs have deterministic acceptance criteria (provenance +
  licence + verification state) before any file is added.
- DEXPI interoperability work can proceed openly with attribution.

### Negative

- DeepPlant cannot ship exact reproductions of ISO/ISA/IEC symbol figures; some
  users comparing drawings against the printed standards will need to verify
  correspondence themselves.
- Standards alignment requires human verification against authorized copies,
  which is slower than assuming compliance from visual similarity.
- Third-party asset sources need case-by-case legal/provenance review before
  import; the first symbol slice should assume mostly DeepPlant-original
  geometry.

## Deferred

- The SVG symbol library itself, the symbol/anchor contract, and any renderer.
- A machine-readable provenance manifest and any asset-management framework
  (see the illustrative example in `docs/standards.md`; not implemented).
- Import decisions for specific third-party packs (ISPF `ispf-pid-v1` remains
  blocked on upstream licence clarification; draw.io P&ID shapes remain
  candidates pending per-file licence confirmation).
- Licensed reproduction of normative standard artwork under a separate rights
  agreement, if ever needed for a commercial artifact outside the public
  repository.

## Revisit When

A concrete requirement demands storing restricted standards content (only
possible with an explicit rights agreement), an upstream symbol source's licence
ambiguity is resolved in writing, or a compliance claim must be made without
human verification (this ADR assumes that never happens).

## Related

- [docs/standards.md](../standards.md) — standards registry, research evidence,
  provenance policy, seven-symbol assessment.
- [ADR-0003-separate-semantic-and-presentation-models.md](ADR-0003-separate-semantic-and-presentation-models.md)
- [ADR-0002-semantic-model-is-the-core.md](ADR-0002-semantic-model-is-the-core.md)
- [AGENTS.md](../../AGENTS.md) — Licensed Standards instruction for agents.
