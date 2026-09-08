# ADR-0008: Define the Process SVG Symbol and Anchor Contract

> Status: Accepted
> Date: 2026-09-08

## Context

The roadmap's first presentation-asset slice is a process/PFD SVG symbol set
with deterministic connection anchors for `ProcessStep`. A future headless
renderer must be able to take a `ProcessStep.type`, look up SVG geometry, and
route `ProcessStream`s through ordered input/output anchor slots — without
adding presentation fields to the semantic model (ADR-0003). The realistic
process fragment
([examples/realistic-process-fragment/plant.yaml](../examples/realistic-process-fragment/plant.yaml))
is the reference workload; its `ProcessStep.type` values are `source`, `mixing`,
`pump`, `heat_exchanger`, `splitting`, `vessel`, and `sink`.

The governance prerequisite is in place: ADR-0007 and `docs/standards.md`
require explicit provenance for distributed assets, restrict normative artwork,
and make DeepPlant-original geometry the default. A second side of the
exchanger, physical nozzles, and the physical/P&ID model are out of scope for
this first set.

## Decision

- **SVG is the initial presentation asset format.** The first set represents
  the process/PFD layer only (`ProcessStep`); physical/P&ID symbols are not part
  of this slice.
- **SVG symbols are presentation artifacts, never semantic domain objects.**
  No presentation fields are added to any semantic model, and
  `src/deepplant/model.py` is unchanged.
- **All MVP symbols use a uniform local coordinate system**:
  `viewBox="0 0 100 100"`, no fixed pixel dimensions, no raster/external
  content, and an explicit monochrome, renderer-themeable style
  (`stroke="currentColor"`, `fill="none"`).
- **Machine-readable ordered connection anchors are embedded in each SVG** in a
  single `g id="deepplant-anchors"` group with `anchor-in-N` / `anchor-out-N`
  ids and numeric coordinates.
- **Anchors encode presentation input/output slots, not semantic `ProcessPort`
  ids.** `SVG anchor != ProcessPort != Port != future Nozzle`.
- **Process input/output roles remain derived from `ProcessStream`
  incidence** (`stream.target` → input, `stream.source` → output); no
  `ProcessPort.direction` field is added and no assignment algorithm ships yet.
- **Dynamic labels, layout, routing, rotation, and view persistence are
  renderer/view concerns**, explicitly deferred.
- **Initial assets are DeepPlant-original and carry explicit provenance**:
  origin DeepPlant-original, licence AGPL-3.0-only, and a `reference` /
  `candidate-alignment` standards state (never `human-verified` or compliant
  without a recorded human check). Per-symbol provenance is recorded in
  `assets/symbols/process/README.md`.
- **The initial visual language targets professional engineering-diagram
  appearance**, not generic application-icon aesthetics.

## Consequences

### Positive

- A future headless renderer has a deterministic `type → geometry + ordered
  anchor slots` contract to build on, with no semantic-model change.
- Presentation geometry and engineering semantics stay strictly separate
  (ADR-0003); the semantic model remains open (`ProcessStep.type` stays a free
  string with no enum or per-type validation).
- Deterministic, dependency-free tests can validate every asset (XML, canonical
  viewBox, anchor naming/order/counts, forbidden content).
- The provenance and verification vocabulary from ADR-0007 is applied from the
  first asset, so the repository stays free of restricted or unprovenanced
  artwork.
- Assets remain plain, editable SVGs, which keeps a future
  user-authored-custom-symbol path open.

### Negative

- The set is small (seven process symbols) and deliberately carries no routing,
  layout, or labelling logic, so it is not yet a drawing capability on its own.
- Stream routing still requires a renderer to assign semantic ports to anchors;
  that work is deferred and will likely refine the anchor conventions.

## Deferred

- The renderer (layout, symbol placement, `ProcessPort`-to-anchor assignment,
  stream routing, composition, labels, CLI command).
- Rotation, mirroring, vertical flow, manual anchor movement, alternative
  orientations.
- Physical/P&ID symbol sets (`Equipment`, `Port`, `Connection`, nozzles, pipes,
  valves, instruments) and any later `ProcessStep.type` variants.
- Machine-readable provenance manifest and runtime asset packaging/lookup.
- Custom-symbol loading machinery (search paths, plugins, GUI import, Inkscape
  extension, CAD integration).

## Revisit When

A concrete renderer requirement forces a change to the anchor representation or
naming, a new symbol variant needs a different anchor cardinality or side
layout, or a distributed asset needs to come from a non-original source (which
then requires the ADR-0007 provenance gate).

## Related

- [docs/svg-symbols.md](../svg-symbols.md) — the contract in implementation
  detail.
- [ADR-0003-separate-semantic-and-presentation-models.md](ADR-0003-separate-semantic-and-presentation-models.md)
- [ADR-0007-standards-and-symbol-provenance.md](ADR-0007-standards-and-symbol-provenance.md)
- [docs/standards.md](../standards.md) — provenance policy and verification
  vocabulary.
- [docs/roadmap.md](../roadmap.md) — slice sequence; the next task is the basic
  headless read-only process renderer.
