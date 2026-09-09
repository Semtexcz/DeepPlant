# ADR-0008: Define the Process SVG Symbol-Pack and Anchor Contract

> Status: Accepted, partially superseded by ADR-0009
> Date: 2026-09-08

> **Supersession note (ADR-0009):** ADR-0009 supersedes **only** the
> `ProcessStep.type` → symbol-role coupling assumed here (the historical text
> below preserves that assumption as written). The role → pack → SVG + anchor
> contract and the role-identity != graphical-asset-identity distinction remain
> fully in force. Since ADR-0009, `ProcessStep.function` is canonical
> engineering semantics and the presentation layer resolves symbol roles (by
> default policy or explicit per-step override), so the symbol pack no longer
> reads a role from the semantic model.

## Context

The roadmap's first presentation-asset slice supplies process/PFD SVG geometry
with deterministic connection anchors for `ProcessStep`. A future headless
renderer needs a role from `ProcessStep.type`, a presentation-layer choice of
symbol pack, and then SVG geometry plus ordered anchors for `ProcessStream`
routing.

Treating `ProcessStep.type` as a global identity for one canonical SVG geometry
would make a standards-aligned, company-specific, or custom realization
impossible without changing the semantic model. Graphical realization must
therefore be selected through a symbol-pack concept, and the current
DeepPlant-original geometry should be the first `basic`/fallback pack rather
than the globally canonical engineering representation.

The realistic process fragment
([examples/realistic-process-fragment/plant.yaml](../examples/realistic-process-fragment/plant.yaml))
is the reference workload; its `ProcessStep.type` values are `source`, `mixing`,
`pump`, `heat_exchanger`, `splitting`, `vessel`, and `sink`. ADR-0007 requires
explicit provenance for distributed assets and restricts normative artwork, so
the initial assets are independently authored DeepPlant geometry.

## Decision

- **SVG is the initial presentation asset format.** The first pack represents
  the process/PFD layer only (`ProcessStep`); physical/P&ID symbols are not part
  of this slice.
- **`ProcessStep.type` identifies a symbol role, not globally canonical SVG
  geometry.** A symbol pack is one graphical realization of that role, and role
  identity is distinct from graphical asset identity.
- **The current DeepPlant-original assets form the initial `basic` pack** at
  `assets/symbols/process/basic/`. Within that pack the filename stem maps
  directly to the role (`basic/pump.svg`), a pack-local convention only.
- **Symbol-pack selection belongs to the future presentation layer** and is not
  encoded in the semantic model. No runtime registry, provider, plugin,
  configuration API, or renderer is introduced here.
- **SVG symbols are presentation artifacts, never semantic domain objects.** No
  presentation fields are added to any semantic model, and
  `src/deepplant/model.py` is unchanged.
- **All pack assets use a uniform local coordinate system**:
  `viewBox="0 0 100 100"`, no fixed pixel dimensions, no raster/external
  content, and an explicit monochrome, renderer-themeable style
  (`stroke="currentColor"`, `fill="none"`).
- **Machine-readable ordered connection anchors are embedded in each SVG** in a
  single `g id="deepplant-anchors"` group with unique contiguous `anchor-in-N` /
  `anchor-out-N` ids and numeric coordinates. Anchors are visually hidden via
  `fill="none"` / `stroke="none"`; the radius is not prescribed. Unrelated
  internal SVG ids are allowed.
- **Anchors encode presentation input/output slots, not semantic `ProcessPort`
  ids.** `SVG anchor != ProcessPort != Port != future Nozzle`.
- **Process input/output roles remain derived from `ProcessStream`
  incidence** (`stream.target` → input, `stream.source` → output); no
  `ProcessPort.direction` field is added and no assignment algorithm ships yet.
- **The `basic` pack is non-normative DeepPlant-original fallback/reference
  geometry** for contract validation, renderer development, and custom-symbol
  examples. Its `pump`, `heat_exchanger`, and `vessel` glyphs are not claimed to
  be standards-aligned equipment symbols and are not intended to replace a
  future standards-aligned pack, which may use materially different geometry
  and would require explicit rights, per-asset provenance, and human
  verification against an authorized copy.
- **Dynamic labels, layout, routing, rotation, and view persistence are
  renderer/view concerns**, explicitly deferred.

## Consequences

### Positive

- A future headless renderer can render the same `ProcessStep.type` through any
  selected pack; the smallest renderer may explicitly choose `basic` as its
  development pack without making that a permanent global identity assumption.
- Presentation geometry and engineering semantics stay strictly separate
  (ADR-0003); the semantic model remains open (`ProcessStep.type` stays a free
  string with no enum or per-type validation).
- Dependency-free tests validate every asset without over-constraining the
  serialization: unrelated internal ids and a nonzero hidden anchor radius are
  valid.
- The provenance and verification vocabulary from ADR-0007 is applied from the
  first asset, so the repository stays free of restricted or unprovenanced
  artwork.

## Negative

- No runtime pack-selection mechanism exists yet; the contract is
  filesystem/documentation only until the renderer justifies a lookup boundary.
- The `basic` pack is intentionally small, non-normative, and not a drawing
  capability on its own.

## Deferred

- The renderer (layout, symbol placement, `ProcessPort`-to-anchor assignment,
  stream routing, composition, labels, CLI command) and its pack lookup.
- Runtime symbol registry, plugins, providers, pack configuration, custom-pack
  loading, and runtime provenance manifests.
- Standards-aligned, company-specific, and custom/user symbol packs and their
  sourcing/loading.
- Rotation, mirroring, vertical flow, manual anchor movement, alternative
  orientations, and physical/P&ID symbol sets.

## Revisit When

A concrete renderer requirement forces a change to the anchor representation or
naming, a new graphical variant needs a different anchor cardinality or side
layout, a distributed asset needs to come from a non-original source (which
then requires the ADR-0007 provenance gate), or a second symbol pack is
introduced.

## Related

- [docs/svg-symbols.md](../svg-symbols.md) — the contract in implementation
  detail.
- [ADR-0009-separate-process-function-from-symbol-role.md](ADR-0009-separate-process-function-from-symbol-role.md) —
  supersedes only this ADR's `ProcessStep.type` → symbol-role coupling.
- [ADR-0003-separate-semantic-and-presentation-models.md](ADR-0003-separate-semantic-and-presentation-models.md)
- [ADR-0007-standards-and-symbol-provenance.md](ADR-0007-standards-and-symbol-provenance.md)
- [docs/standards.md](../standards.md) — provenance policy and verification
  vocabulary.
- [docs/roadmap.md](../roadmap.md) — slice sequence and current next tasks.
