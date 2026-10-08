# ADR-0017: Machine-Rendered Symbol Definitions

> Status: Accepted
> Date: 2026-10-08

## Context

ADR-0008 established the first presentation-asset slice: SVG as the asset
format, a hand-authored DeepPlant-original `basic` pack under
`src/deepplant/assets/symbols/process/basic/`, and a machine-readable anchor
group inside each asset. It deliberately deferred a runtime symbol registry,
pack configuration, and standards-aligned packs, and its assets are explicitly
non-normative fallback geometry whose canonical source is the `.svg` file
itself.

Issue #119 asks for something structurally different: a standard PFD/P&ID symbol
library whose canonical geometry is a machine-readable definition, from which
SVG is generated deterministically. Its requirements are explicit that symbols
must not be maintained primarily as manually authored standalone SVG files, that
the engineering object must not be the SVG, that connection anchors must be
explicit model data rather than something inferred from generated geometry, and
that no geometry may be copied from the supplied company reference drawings.

The MVP reference material (the YARA / Chemoproject PFD and P&ID drawings) fixes
*what must be drawable*. ISO 10628 and ISO 15519-2 are recorded as the reference
*direction* for how such a concept is conventionally drawn. The geometry in this
slice is DeepPlant-authored project seed geometry
([symbol-seed-geometry.md](../reference/symbol-seed-geometry.md)), not restricted
standard artwork, and each definition records its intended ISO relationship at
the conservative `candidate-alignment` state — an intent to correspond that no
human has yet checked against an authorized copy. A `human-verified` record
requires recorded human evidence, and restricted standard material never enters
the repository (ADR-0007).

## Decision

- **A symbol's canonical geometry is a typed `SymbolDefinition`, not an SVG
  file.** SVG is generated output. An `.svg` file is neither the source of truth
  nor a required artifact of the library, so definition and renderer cannot drift
  apart.
- **A new capability package owns the library.** `src/deepplant/symbols/`
  (`definition`, `catalogue`, `registry`, `svg`) holds presentation data only: it
  imports nothing outside the standard library, depends on neither the semantic
  model nor the application/transport/GUI layers, and is usable from Python and
  the CLI without an editor, browser, or network (ADR-0002, ADR-0003).
- **The existing process symbol pack is not retrofitted.** `basic`,
  `docs/dev/reference/svg-symbols.md`, and the role → pack → SVG + anchor contract
  remain in force unchanged. Two mechanisms exist on purpose: one
  DeepPlant-original process fallback pack, one machine-rendered standards-*aligned*
  symbol library whose geometry is likewise DeepPlant-authored, not
  standards-derived.
- **Geometry is normalized and validated.** Every coordinate lives on the
  symbol's local view box, canonical `0 0 100 100` — the same normalized
  convention the process pack already uses (ADR-0008). Construction fails closed
  when geometry or an anchor leaves the box, when a vocabulary value is unknown,
  when a symbol records no asset provenance, when a `deepplant-original` asset
  records a licence other than `AGPL-3.0-only`, and when the `generic-iso` profile
  carries no intended standards correspondence.
- **Connection anchors are explicit definition data, and their contract is
  geometric.** An anchor is a named, positioned slot with an `orientation`
  (`north`/`east`/`south`/`west`) and a connection `kind`
  (`process`/`signal`):

  ```text
  anchor orientation = geometric routing orientation
  anchor kind        = process | signal
  semantic flow direction is NOT part of the generic graphical anchor
  ```

  `orientation` says which way the connection leaves the symbol, which is what
  routing and layout need; it is deliberately not process flow direction, signal
  direction, or inlet/outlet meaning. Engineering meaning comes from the anchor
  name and from later semantic mapping. Consequently a generic gate valve uses
  neutral `port_a`/`port_b` connection names instead of `inlet`/`outlet`, while a
  pump keeps the meaningful `suction`/`discharge` names and records their
  geometry separately (`west`/`east`). Anchors are never inferred from generated
  SVG, `symbol anchor != ProcessPort != Port` continues to hold, and this slice
  does not write anchors into generated SVG.
- **The reusable base instrument graphic carries no mandatory signal anchor.** A
  local/field instrument may have no signal connection at all (a local indicator)
  or one (a transmitter), so the base `instrument.local` definition keeps only
  the process tap it needs to attach to the process. Signal anchors belong to a
  later concrete instrument-function composition, not to the reusable graphic.
- **Only the primitives an implemented symbol needs exist.** `Line`, `Circle`,
  and `Polygon` are defined; a further primitive is added when a verified symbol
  requires one.
- **The three implemented geometries are DeepPlant-authored project seed
  geometry.** Their primitives are authored from the project specification in
  [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md), they are not
  derived from normative standard artwork, and they are not claimed to be exact
  ISO geometry.
- **Asset provenance is required, and it is separate from standards
  correspondence.** Every definition carries an `AssetProvenance(origin,
  license)`: the geometry's origin and the licence it is distributed under.
  `ASSET_ORIGINS` currently accepts only `deepplant-original`, whose geometry is
  distributed under `AGPL-3.0-only`, and the two are validated as one explicit
  pair — a DeepPlant-original asset that records any other licence fails closed
  rather than being silently accepted. That is a single origin/licence check, not
  generic licence-policy machinery: third-party import provenance is deferred
  until the first concrete third-party asset, when the complete ADR-0007
  provenance requirements (upstream repository, ref, author/copyright holder,
  licence, modification state) must be implemented — the current two-field record
  is not sufficient for an imported asset.
- **Standards correspondence is optional at the definition level, is required by
  the `generic-iso` profile, records intent, and fails closed.** A definition
  records at most the standard identifiers its geometry is intended to correspond
  to, using exactly the canonical `reference` / `candidate-alignment` /
  `human-verified` vocabulary of [workflow/standards.md](../workflow/standards.md),
  and independently of the asset copyright/licence provenance. The requirement
  belongs to the profile rather than to the class: a future company, project, or
  custom profile may record no standards relationship at all, whereas
  `generic-iso` *means* intended correspondence and therefore demands at least one
  reference at `candidate-alignment` or `human-verified`. `reference` claims no
  correspondence for a concrete geometry and can never satisfy that profile.
  `candidate-alignment` records an intended correspondence with no human check —
  human verification is explicitly **not** a prerequisite for it; and
  `human-verified` construction fails closed unless it carries recorded evidence
  of the check (a locator, `verified_by`, and `verified_on`). Verifier evidence
  may only appear on a `human-verified` record, so a weaker state can never
  misleadingly imply a human check. Locators, table/figure references,
  registration numbers, and the standard's own names for a representation are
  recorded only when a permitted source or a recorded human verification supplies
  them — never from restricted material inspected by an agent. No standard
  artwork, table, figure, or normative text is stored, and project/company
  conventions (tag prefixes, line designation, DCS/SIS practice, interlock
  numbering) are explicitly *not* a base symbol library.
- **Instrumentation separates the graphic from the text.** The library holds one
  reusable base instrument representation; function letter codes such as PIT, TI,
  or FIC are composition/text onto that base graphic, never separate symbol
  definitions and never geometry.
- **Scope is the three representative representations of the first slice**, plus
  the minimum registry (`get`, `list`) and deterministic renderer around them.
  Composition, variants, profiles other than `generic-iso`, a gallery, and editor
  integration are deferred.

## Consequences

### Positive

- One canonical geometry source per symbol, validated at import time, with a
  deterministic renderer that cannot silently diverge from it.
- The standards relationship is recorded per symbol and machine readably, and
  separately from asset copyright provenance, so a later human verification is a
  data change rather than a rewrite.
- Standards material stays out of the repository, and the recorded relationship
  stays conservative: no locator, table or figure reference, registration number,
  or standard-authored name is stored unless a permitted source or a human
  verification supplies it.
- The library is dependency-free and framework-free, so it stays headlessly
  testable and does not widen the semantic model.
- A future company, project, custom, or DeepPlant-original symbol is a valid
  definition with its own provenance, no invented standards reference, and — unlike
  `generic-iso` — no profile-imposed standards requirement.

### Negative

- Two symbol mechanisms now coexist; the coverage matrix and the two reference
  documents must state clearly which one owns a given glyph.
- Generated SVG has no stored artifact in this slice, so there is no committed
  visual reference to diff against; determinism and structural tests are the
  evidence instead.
- Nothing is `human-verified` yet, so the library must not be presented as a
  standards-conformant symbol set: all three representations record their intended
  ISO relationship at the conservative `candidate-alignment` state, and their
  geometry is DeepPlant-authored project seed geometry.

## Deferred

- The rest of the MVP catalogue (further valves, pump types, equipment, fittings,
  measurement sensors), DCS/SIS symbols, and company/Yara-CHPN profiles.
- Composition and variant machinery: instrument letter codes, signal anchors for
  instrument functions that have one, control valves with actuators, instruments
  with integrated displays, multifunction instruments.
- A generated gallery, runtime provenance manifests, pack configuration,
  custom-pack loading, arbitrary SVG import, and editor integration.
- Third-party symbol import: deferred until the first concrete third-party asset,
  at which point the complete ADR-0007 provenance record must be implemented
  (upstream repository, ref, author/copyright holder, licence, modification
  state). No third-party origin is accepted before that.
- Writing anchor slots into generated SVG, and any editor metadata.

## Revisit When

A human verification promotes a symbol's standards relationship to
`human-verified`, a symbol needs a further primitive, a second drawing profile is
introduced, a consumer needs the anchors inside the SVG, or a gallery becomes the
cheapest way to review the catalogue.

## Related

- [symbol-library.md](../reference/symbol-library.md) — the contract that
  operationalizes this decision.
- [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) — the
  project-owned spec the implemented geometry is authored from.
- [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md) — the coverage
  matrix, per-concept status, and unresolved questions.
- [ADR-0003](ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0007](ADR-0007-standards-and-symbol-provenance.md),
  [ADR-0008](ADR-0008-process-svg-symbol-and-anchor-contract.md), and
  [ADR-0009](ADR-0009-separate-process-function-from-symbol-role.md).
