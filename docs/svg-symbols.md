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

First presentation-asset slice behind
[ADR-0008](decisions/ADR-0008-process-svg-symbol-and-anchor-contract.md). The
initial assets live in `assets/symbols/process/`. This slice is **not** the
renderer and **not** frontend work.

## Purpose

Prove that a future headless renderer can deterministically do:

```text
ProcessStep.type
        ↓
symbol lookup
        ↓
SVG geometry
        +
ordered input/output anchor slots
        ↓
future ProcessStream routing
```

without adding any presentation fields to the semantic model. The reference
workload is `examples/realistic-process-fragment/plant.yaml`, whose current
`ProcessStep.type` values are `source`, `mixing`, `pump`, `heat_exchanger`,
`splitting`, `vessel`, `sink`.

## Scope

- Process/PFD presentation only. The first symbol library represents
  `ProcessStep`.
- No symbol contracts for `Equipment`, `Port`, `Connection`, `Nozzle`, `Pipe`,
  `PipingLine`, `Valve`, `Instrument`, `Signal`, `Flange`, `Tee`, or `Reducer`.
- `FV-101` (physical control valve) is intentionally not represented. The first
  future renderer renders `ProcessModel`, not the physical P&ID topology.

## Semantic/presentation boundary

Do not add fields such as `x`, `y`, `width`, `height`, `rotation`, `symbol`,
`symbol_id`, `style`, `color`, `layout`, `anchor`, `view`, or `sheet` to any
semantic model. `src/deepplant/model.py` is unchanged. The relationship stays:

```text
semantic model
     ↓
presentation mapping / convention
     ↓
SVG assets
```

## Asset provenance rule

- All current geometry is **DeepPlant-original** and independently authored.
- No ISO/ISA/IEC figure copying, tracing, screenshot reuse, or AI derivation
  from restricted material; no draw.io / IPD Studio / ISPF assets.
- Licence: `AGPL-3.0-only` (repository licence).
- Standards alignment state: `reference` or `candidate-alignment` only; never
  `human-verified`, never "ISO compliant" / "standards compliant", until a named
  human verifies against an authorized copy and records it.
- Per-symbol provenance is recorded in
  `assets/symbols/process/README.md`. No machine-readable provenance framework
  yet.

## Engineering visual language

- Monochrome line art with a technical, orthographic, diagrammatic appearance.
- No gradients, shadows, 3D effects, perspective, decorative fills, rounded-card
  UI aesthetics, Material Design styling, or icon/pictogram/infographic
  styling.
- No unnecessary internal arrows; no ornament.
- `pump`, `heat_exchanger`, and `vessel` use conventional process-engineering
  visual grammar; `source`, `mixing`, `splitting`, and `sink` use the same
  technical drawing language and are process-function/boundary glyphs, not
  BPMN/flowchart blocks.

## Visual consistency requirements

The seven symbols share one visual grammar: same effective stroke weight,
similar visual density and apparent size, similar margin around geometry,
similar anchor treatment, and a similar level of abstraction. Geometry prefers
natural symmetry and avoids decorative asymmetry.

## Canonical coordinate system

```xml
viewBox="0 0 100 100"
```

No fixed pixel `width` / `height` attributes. The future renderer owns scale.

## Allowed SVG subset

Allowed elements: `g`, `path`, `line`, `polyline`, `polygon`, `rect`, `circle`,
`ellipse`. Forbidden in assets: `script`, `foreignObject`, embedded raster
images, external resources, external stylesheets, fonts, filters, masks, and
editor-specific constructs. Assets must remain easy to open and modify in
Inkscape without depending on Inkscape-specific XML.

## Style rules

- Monochrome and renderer-themeable: geometry uses `stroke="currentColor"` and
  `fill="none"`.
- Uniform stroke width (currently `2` within the 100x100 viewBox).
- No CSS classes external to the SVG; no brand colors.
- No engineering-instance labels (`P-101`, `PS-pump`, `Feed Pump`, `E-101`,
  `V-101`) and no stream ids in assets. Dynamic labels belong to the future
  renderer.

## Symbol identity

The canonical symbol id is the filename stem: `source`, `mixing`, `pump`,
`heat_exchanger`, `splitting`, `vessel`, `sink`. These match the current
`ProcessStep.type` values used by the realistic fragment, but
`ProcessStep.type` remains an open string — no enum and no domain validation
were added. Missing-symbol/fallback behavior belongs to the future renderer.

## Critical conceptual distinction

```text
SVG anchor    → presentation geometry
ProcessPort   → endpoint in the process graph
Port          → current physical/bootstrap endpoint
Nozzle        → future physical plant hardware
```

`SVG anchor != ProcessPort != Port != Nozzle`. Future presentation logic may map
semantic endpoints to graphical anchors; this PR defines only the anchor side of
that contract.

## Anchor naming

Each SVG contains exactly one machine-readable anchor group:

```xml
<g id="deepplant-anchors">
  ...
</g>
```

Anchor ids use:

```text
anchor-in-0, anchor-in-1, ...
anchor-out-0, anchor-out-1, ...
```

Indices start at zero. No semantic `ProcessPort.id` values and no role names
such as `anchor-suction` or `anchor-out_recycle` appear in generic symbol
assets.

## Anchor direction semantics

```text
anchor-in-N  → visual slot for an incoming ProcessStream
anchor-out-N → visual slot for an outgoing ProcessStream
```

Input/output role is derivable from stream incidence (`stream.target` → input
role, `stream.source` → output role). The semantic model does not carry
`ProcessPort.direction`; the full assignment algorithm is deferred to the
renderer.

## Anchor ordering and canonical orientation

The MVP contract uses left-to-right material flow: inputs on the left side,
outputs on the right side. When a side has multiple anchors, stable vertical
ordering applies: `0 = upper`, `1 = lower`. Rotation, mirroring, vertical flow,
manual anchor movement, and alternative orientations are not implemented.

## Current symbol variants

| Symbol id | Inputs | Outputs |
|---|---|---|
| `source` | 0 | 1 |
| `mixing` | 2 | 1 |
| `pump` | 1 | 1 |
| `heat_exchanger` | 1 | 1 |
| `splitting` | 1 | 2 |
| `vessel` | 1 | 1 |
| `sink` | 1 | 0 |

These counts are properties of the current variants, not semantic invariants; no
domain validator enforces them.

## Minimal anchor example

```xml
<circle
    id="anchor-in-0"
    cx="0"
    cy="50"
    r="0"
    fill="none"
    stroke="none"
/>
```

Anchor coordinates are machine-readable numeric `cx`/`cy` values inside the
viewBox. Anchors are not visibly rendered.

## Standards/provenance status

- `pump`, `heat_exchanger`, `vessel`: ISO 10628-2 / ISO 14617 are future
  human-verification references where applicable; initial state
  `candidate-alignment`, not `human-verified` / compliant.
- `source`, `mixing`, `splitting`, `sink`: DeepPlant process-graph presentation
  concepts; no forced ISO equipment-symbol correspondence.
- All assets: origin DeepPlant-original, licence AGPL-3.0-only, alignment
  `reference` / `candidate-alignment` per asset (see
  `assets/symbols/process/README.md`).

## Explicitly deferred features

- Graph layout, node coordinates, stream routing, arrowheads between nodes,
  `ProcessPort`-to-anchor assignment, automatic diagram generation, SVG canvas
  composition, labels, CLI render command.
- Renderer and any runtime presentation abstractions (`SymbolRegistry`,
  presentation/view model, layout/routing/anchor-resolver engines) — the future
  renderer will reveal what is actually needed.
- Rotation, mirroring, vertical flow, manual anchor movement, alternative
  orientations.
- Custom-symbol loading machinery: search paths, plugin loading, GUI import,
  Inkscape extension, CAD integration, symbol package registry.
- Machine-readable provenance manifest and runtime asset packaging.
- Additional symbol sets (physical/P&ID `Equipment` symbols and any later
  `ProcessStep.type` variants).

## Future custom symbols

A user-authored custom SVG should eventually be usable if it satisfies the same
SVG + anchor contract (same `viewBox`, allowed subset, anchor group and naming,
style rules, and provenance record). Nothing is implemented for this yet beyond
keeping the shipped assets plain and easy to edit.

## Related

- [ADR-0008](decisions/ADR-0008-process-svg-symbol-and-anchor-contract.md) —
  durable decision for this contract.
- [ADR-0003](decisions/ADR-0003-separate-semantic-and-presentation-models.md) and
  [ADR-0007](decisions/ADR-0007-standards-and-symbol-provenance.md).
- [standards.md](standards.md) — provenance/licensing policy and verification
  vocabulary.
- [roadmap.md](roadmap.md) — slice sequence; the next task is the basic headless
  read-only process renderer.

