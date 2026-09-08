---
type: svg-symbol-contract
status: active
source_of_truth_for:
  - svg-symbol-and-anchor-contract
read_when:
  - symbol-asset-work
  - renderer-implementation
  - presentation-work
update_when:
  - symbol-contract-change
  - new-symbol-variant
---

# DeepPlant SVG Symbol and Anchor Contract

The first presentation-asset slice behind
[ADR-0008](decisions/ADR-0008-process-svg-symbol-and-anchor-contract.md) is the
DeepPlant `basic` process symbol pack in `assets/symbols/process/basic/`. This
slice is **not** renderer, frontend, or runtime symbol-selection work.

## Role, pack, and asset

Three concepts are deliberately distinct:

```text
symbol role
    semantic/presentation category corresponding to ProcessStep.type

symbol pack
    coherent set of graphical realizations for roles

SVG asset
    one graphical realization of one role within one pack
```

Example:

```text
role:  pump
pack:  basic
asset: assets/symbols/process/basic/pump.svg
```

`ProcessStep.type` identifies a symbol role. It does **not** globally select one
canonical SVG geometry. Within a pack, the filename-stem convention maps
`<role>.svg` to that role (`basic/pump.svg`, `basic/vessel.svg`); that is a
useful pack-local convention, but **role identity != graphical asset
identity**.

A future presentation layer may select a `basic`, standards-aligned,
company-specific, or custom/user pack. That selection is not implemented and is
not encoded in the semantic model:

```text
ProcessStep.type
        ↓
symbol role
        ↓
symbol pack selected by future presentation policy
        ↓
SVG geometry + ordered anchors
```

## Purpose and scope

The contract proves a future headless renderer can consume an explicitly chosen
pack and deterministically use SVG geometry plus ordered input/output anchor
slots for `ProcessStream` routing. The reference workload is
`examples/realistic-process-fragment/plant.yaml`, whose current roles are
`source`, `mixing`, `pump`, `heat_exchanger`, `splitting`, `vessel`, and `sink`.
The `basic` pack must cover those roles; it may contain additional valid SVG
assets.

- Process/PFD presentation only. The first pack represents `ProcessStep`.
- No symbol contracts for `Equipment`, `Port`, `Connection`, `Nozzle`, `Pipe`,
  `PipingLine`, `Valve`, `Instrument`, `Signal`, `Flange`, `Tee`, or `Reducer`.
- `FV-101` is intentionally not represented: the first renderer renders
  `ProcessModel`, not the physical P&ID topology.

## Semantic/presentation boundary

Do not add fields such as `x`, `y`, `width`, `height`, `rotation`, `symbol`,
`symbol_id`, `symbol_pack`, `symbol_profile`, `presentation_profile`, `style`,
`color`, `layout`, `anchor`, `view`, or `sheet` to any semantic model.
`src/deepplant/model.py` is unchanged. The architecture remains:

```text
semantic model
        ↓
presentation policy
        ↓
selected symbol pack
        ↓
SVG asset + anchors
```

## Basic-pack provenance and visual acceptance

The current pack is the **DeepPlant basic process symbol pack**: open,
DeepPlant-original, non-normative fallback/reference geometry for contract
validation, renderer development, and custom-symbol examples. It is not the
definitive PFD/P&ID symbol library.

`pump`, `heat_exchanger`, and `vessel` are `reference` / unverified basic
fallback glyphs. They express their semantic roles sufficiently for a coherent
DeepPlant basic technical-diagram fallback set; they are not claimed to be
production-quality standards-style PFD/P&ID symbols and are not intended to
replace a standards-aligned equipment-symbol pack. A future standards-aligned
pack may use materially different geometry.

All current geometry is DeepPlant-original under `AGPL-3.0-only`. No ISO/ISA/IEC
figure copying, tracing, screenshot reuse, or AI derivation from restricted
material occurred; no draw.io, IPD Studio, or ISPF asset was copied. Per-asset
provenance is recorded in `assets/symbols/process/basic/README.md`.

A future standards-aligned pack requires explicit rights, per-asset
provenance, and human standards verification against an authorized copy, and it
may be external or user-provided. This contract does not implement or source
such a pack.

## SVG contract

Each SVG asset uses `viewBox="0 0 100 100"`, has no fixed `width` or `height`,
and uses monochrome themeable geometry (`stroke="currentColor"`,
`fill="none"`). Only the restricted safe element/attribute subset validated by
the stdlib XML tests is allowed: no text, scripts, external references,
embedded data, fixed colors, or other active content.

Each asset contains exactly one `g id="deepplant-anchors"` group. Its direct
children are anchor circles whose ids are unique and match `anchor-in-N` or
`anchor-out-N`; within one direction the indices start at `0` and are
contiguous. Every anchor has numeric `cx` and `cy` coordinates inside the local
viewBox and is not visually rendered: `fill="none"` and `stroke="none"`. The
radius `r` is **not** prescribed by the contract; `r="0"`, a nonzero radius, or
an omitted radius are equally valid as long as the anchor stays unrendered.

Other SVG element ids are allowed for geometry groups, paths, editor objects,
or internal reusable elements. The contract constrains only the anchor group
and its anchor ids; it does not ban unrelated harmless ids and it does not
depend on Inkscape or editor metadata.

```xml
<circle
  id="anchor-in-0"
  cx="0"
  cy="50"
  r="1"
  fill="none"
  stroke="none"
/>
```

## Anchor meaning

```text
SVG anchor != ProcessPort != Port != future Nozzle

anchor-in-N  → visual slot for an incoming ProcessStream
anchor-out-N → visual slot for an outgoing ProcessStream
```

Input/output role is derived from `ProcessStream` incidence (`stream.target` →
input role, `stream.source` → output role). `ProcessPort.direction` is not
added to the semantic model, and semantic-port-to-anchor assignment is
renderer work, deferred.

The current `basic` variants use left-to-right material flow: inputs on the
left, outputs on the right; when a side has multiple anchors, `0` is upper and
`1` lower. Their current cardinalities are `source` 0/1, `mixing` 2/1, `pump`
1/1, `heat_exchanger` 1/1, `splitting` 1/2, `vessel` 1/1, and `sink` 1/0. These
are current basic-pack variant properties, not domain invariants.

## Explicitly deferred

- Renderer, layout, node coordinates, stream routing, labels, SVG composition,
  CLI render command, and semantic-port-to-anchor assignment.
- Runtime symbol registry, plugins, providers, pack configuration, CLI pack
  selector, custom-pack loading, and runtime provenance manifests.
- Standards-aligned, company-specific, and custom/user symbol packs.
- Physical/P&ID symbol sets, rotation, mirroring, alternative orientations, and
  manual anchor movement.

## Related

- [ADR-0008](decisions/ADR-0008-process-svg-symbol-and-anchor-contract.md) —
  durable decision for the pack-aware contract.
- [ADR-0003](decisions/ADR-0003-separate-semantic-and-presentation-models.md)
  and [ADR-0007](decisions/ADR-0007-standards-and-symbol-provenance.md).
- [standards.md](standards.md) — provenance/licensing policy and verification
  vocabulary.
- [roadmap.md](roadmap.md) — slice sequence; the next task is the basic headless
  read-only process renderer against the pack-aware contract.

