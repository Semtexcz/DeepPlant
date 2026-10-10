---
type: reference
status: active
canonical_for:
  - symbol-seed-geometry
read_when:
  - symbol-asset-work
  - standards-alignment-claim
update_when:
  - symbol-geometry-change
depends_on: []
decision:
  - docs/dev/decisions/ADR-0007-standards-and-symbol-provenance.md
  - docs/dev/decisions/ADR-0017-machine-rendered-symbol-definitions.md
evidence: []
superseded_by: null
---

# Project-Owned Symbol Seed Geometry

> **Question this document answers:** where did the geometry of the built-in
> symbol definitions come from, and what may DeepPlant claim about it?

This is the DeepPlant **project specification** the built-in symbol geometries
are authored from. It is the provenance record behind
`AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only")` in
[symbol-library.md](symbol-library.md).

## What this is, and what it is not

These are DeepPlant-authored **seed geometries**: recognizable, generic
presentation glyphs for architecture validation, drawn on the canonical
normalized view box `0 0 100 100` (ADR-0008). They exist to prove the
definition → registry → renderer architecture, not to reproduce a standard.

- They are **DeepPlant-original** and are **not** derived from normative standard
  artwork.
- They are **not** exact ISO geometry, and no ISO correspondence is claimed as
  verified.
- No standard figure, table, symbol artwork, locator, or normative wording is
  copied, traced, extracted, or recorded here.
- The standards relationship of each symbol is recorded separately. The three
  `generic-iso` geometries record the conservative `candidate-alignment` state — an
  *intended* correspondence with no human check claimed — which is what that
  profile requires, because a bare `reference` claims no correspondence for a
  concrete geometry. The four `deepplant-default` geometries (the restriction
  orifice and the three Issue #132 basic valves) record **no** standards
  relationship at all, which their profile permits because they make no
  ISO/ISA/PIP conformance claim
  ([workflow/standards.md](../workflow/standards.md)). A coverage-matrix entry may
  still name a concept-level ISO reference *direction*; that is not a concrete
  correspondence for this geometry.

```text
project-owned seed geometry   this document
        ↓
SymbolDefinition              src/deepplant/symbols/catalogue.py
        ↓
generated SVG                 render_symbol_svg(definition)
```

## Seed A — gate valve

ID: `valve.gate`. Purpose: recognizable generic gate-valve presentation glyph for
architecture testing.

```text
line    (0, 50) → (28, 50)              process connection stub
polygon (28, 34), (28, 66), (50, 50)    left body
polygon (50, 50), (72, 34), (72, 66)    right body
line    (72, 50) → (100, 50)            process connection stub
```

Anchors: `port_a` at `(0, 50)`, orientation `west`, kind `process`; `port_b` at
`(100, 50)`, orientation `east`, kind `process`. Inlet/outlet and flow direction
are deliberately not encoded.

## Seed B — centrifugal pump

ID: `pump.centrifugal`. Purpose: recognizable generic centrifugal-pump
presentation glyph for architecture testing.

```text
circle  centre (50, 50), radius 24
line    (0, 50) → (100, 50)    horizontal process connection
line    (50, 26) → (74, 50)    upper internal line
line    (50, 74) → (74, 50)    lower internal line
```

Anchors: `suction` at `(0, 50)`, orientation `west`, kind `process`;
`discharge` at `(100, 50)`, orientation `east`, kind `process`. The anchor names
carry pump-specific engineering meaning; the orientations remain geometry only.

## Seed C — local field instrument

ID: `instrument.local`. Purpose: reusable generic field/local instrument
presentation base.

```text
circle  centre (50, 40), radius 20
line    (50, 60) → (50, 100)   process attachment
```

Anchor: `tap` at `(50, 100)`, orientation `south`, kind `process`. No signal
anchor, no function letter code (PIT, TIT, FIC), no tag, and no control-system
semantics are part of this base graphic.

## Seed D — restriction orifice

ID: `fitting.restriction_orifice`. Purpose: recognizable inline restriction
presentation, and the first `deepplant-default` production representation (Issue
#130).

```text
line    (0, 50)  → (38, 50)     west process connection stub
line    (38, 32) → (38, 68)     west outer intrinsic stroke
line    (50, 20) → (50, 43)     upper half of the centred intrinsic restriction stroke
line    (50, 57) → (50, 80)     lower half of the centred intrinsic restriction stroke
line    (62, 32) → (62, 68)     east outer intrinsic stroke
line    (62, 50) → (100, 50)    east process connection stub
```

The intrinsic glyph is the three transverse strokes between the stubs: two
continuous outer strokes framing a centred stroke split above and below the process
axis. There is deliberately **no** horizontal process-axis line between `x = 38`
and `x = 62`; the gap and central split distinguish the restriction indication from
the adjacent process connection geometry. The canonical normalized form is
DeepPlant-authored and drawn horizontally (`port_a` west, `port_b` east); a document
that draws the component on a vertical process line rotates the placement, which is
presentation, not this geometry. Private reference material was visually inspected
only to understand this qualitative form; no private artwork was measured, traced,
or reproduced, and these coordinates are independently DeepPlant-authored.

Anchors: `port_a` at `(0, 50)`, orientation `west`, kind `process`; `port_b` at
`(100, 50)`, orientation `east`, kind `process`. The two stubs stop at the outer
glyph strokes, so the process axis is visibly interrupted; inlet/outlet and flow
direction are again deliberately not encoded. This is an independently authored
DeepPlant practical `deepplant-default` representation — it reproduces no standard
figure and no company glyph, and it records **no** standards relationship. It
deliberately carries no project/document annotation: a tag such as `RO`, an item
number, a bore value, a tag bubble, and a leader line are authored document data,
not reusable base geometry, so none is embedded here.

## Seed E — globe valve

ID: `valve.globe`. Purpose: recognizable two-port globe-valve presentation, and one
of the three basic valve representations added by Issue #132 in the
`deepplant-default` profile.

```text
line    (0, 50)  → (28, 50)            west process connection stub
polygon (28, 34), (28, 66), (50, 50)   left body
polygon (50, 50), (72, 34), (72, 66)   right body
line    (72, 50) → (100, 50)           east process connection stub
circle  centre (50, 50), radius 8, filled
                                       variant mark: small solid central disc
```

The intrinsic glyph is the two-triangle valve body plus the **solidly filled**
central disc, drawn last so the disc reads over the apex. The disc is the *variant
mark*: it is what makes a globe valve recognizably different from the hollow-circle
ball valve and from the bare gate valve, so the outer body alone is not the
identity. The two horizontal stubs are DeepPlant's connection representation of the
adjacent pipeline, not part of the valve body.

The solid mark is why the primitive vocabulary gained its one boolean
`Circle.filled` capability: a stroked outline cannot express a filled region. The
capability is a boolean only — no colour, gradient, opacity, CSS, class, or theme
object — and `Polygon` deliberately has no fill until an implemented symbol needs
one.

Deliberately absent: any stem, handwheel, lever, or actuator, any function letter
code or tag, any flow arrow, and any annotation. Those are composition or document
data, not reusable base glyph geometry.

Anchors: `port_a` at `(0, 50)`, orientation `west`, kind `process`; `port_b` at
`(100, 50)`, orientation `east`, kind `process`. The body is symmetric, so no
inlet/outlet or flow direction is encoded.

Standards state: **no** relationship recorded. `deepplant-default` makes no
ISO/ISA/PIP conformance claim, so none is required and none is invented; the
coverage matrix's concept-level ISO reference direction is not a correspondence
for this geometry (ADR-0007).

## Seed F — check valve

ID: `valve.check`. Purpose: recognizable one-way check-valve presentation, and one
of the three basic valve representations added by Issue #132.

```text
line   (0, 50)  → (28, 50)     west process connection stub
line   (28, 34) → (72, 34)     body top edge
line   (72, 34) → (72, 66)     body east edge
line   (72, 66) → (28, 66)     body bottom edge
line   (28, 66) → (28, 34)     body west edge
line   (28, 34) → (72, 66)     closing stroke, corner to corner
line   (72, 50) → (100, 50)    east process connection stub
circle centre (28, 34), radius 5, filled
                               hinge peg: small solid corner mark
```

The intrinsic glyph is a rectangular valve body — deliberately a *different* outer
body from the bowtie the gate/globe/ball valves use — carrying a corner-to-corner
closing stroke and a small **solidly filled** hinge peg at one corner, drawn last so
the peg reads over the corner. The two horizontal stubs are DeepPlant's connection
representation of the adjacent pipeline.

The glyph is asymmetric, because a check valve is recognized by its one-way closing
element. That asymmetry is a recognizability mark and **not** a flow-direction
contract: the anchors stay the neutral two-port `port_a`/`port_b` pair, and no
`inlet`/`outlet`/`upstream`/`downstream` name, and no flow-direction field, is added
to `SymbolAnchor`.

Deliberately absent: any tag, arrow, leader, or annotation.

Anchors: `port_a` at `(0, 50)`, orientation `west`, kind `process`; `port_b` at
`(100, 50)`, orientation `east`, kind `process`.

Standards state: **no** relationship recorded, for the same reason as seed E.

## Seed G — ball valve

ID: `valve.ball`. Purpose: recognizable two-port ball-valve presentation, and one
of the three basic valve representations added by Issue #132.

```text
line    (0, 50)  → (18, 50)    west process connection stub
line    (18, 34) → (18, 66)    left outer vertical body edge
line    (18, 34) → (38, 41)    upper-left side edge to circle circumference
line    (18, 66) → (38, 59)    lower-left side edge to circle circumference
line    (82, 34) → (82, 66)    right outer vertical body edge
line    (62, 41) → (82, 34)    upper-right side edge from circle circumference
line    (62, 59) → (82, 66)    lower-right side edge from circle circumference
line    (82, 50) → (100, 50)   east process connection stub
circle  centre (50, 50), radius 15     hollow central body element
```

The intrinsic glyph is a **large hollow central circle** and left/right body-side
geometry: the outer vertical body edges connect by four diagonals that terminate
on the circle circumference. The circle is a structural body element, not a mark
painted over a completed bowtie, so its interior remains clean and no line passes
through it. The vertical outer edges join both diagonals on their respective sides,
forming continuous, symmetric wedges. Its hollow outline distinguishes the ball
valve from the globe valve's solid disc. The two horizontal stubs are DeepPlant's
connection representation of the adjacent pipeline.

Deliberately absent: any stem, lever, actuator, tag, annotation, or flow arrow.

Anchors: `port_a` at `(0, 50)`, orientation `west`, kind `process`; `port_b` at
`(100, 50)`, orientation `east`, kind `process`. The body is symmetric, so no
inlet/outlet or flow direction is encoded.

Standards state: **no** concrete relationship recorded, for the same reason as
seed E. The qualitative private reference evidence establishes form and
decomposition only; these normalized coordinates are independently
DeepPlant-authored and do not establish a standards relationship.

The three seeds E/F/G were authored after a qualitative visual review of the
operator's curated private reference gallery and, where useful, an actual MVP P&ID
occurrence. That material informed only the qualitative notation, the occurrence,
and the structural decomposition into body, variant mark, and connection geometry.
No private artwork was measured, traced, vectorised, or copied, these coordinates
are independently DeepPlant-authored, and no private filename, path, drawing
identifier, tag, or measurement is recorded here.

## Provenance consequence

Because the geometry is authored from this project specification rather than
derived from normative standard artwork, every definition records:

```text
origin  deepplant-original
license AGPL-3.0-only
```

`ASSET_ORIGINS` therefore accepts only `deepplant-original`, and the origin and
licence are validated as one explicit pair: DeepPlant-original geometry is
accepted only under `AGPL-3.0-only`, so another licence (for example `MIT`) is
rejected rather than silently recorded. Third-party import provenance is deferred
until the first concrete third-party asset, at which point the complete ADR-0007
provenance record must be implemented.

## Related

- [symbol-library.md](symbol-library.md) — the contract for the definitions,
  registry, and renderer that consume this geometry.
- [mvp-symbol-coverage.md](mvp-symbol-coverage.md) — the coverage matrix and
  per-concept status.
- [workflow/standards.md](../workflow/standards.md) and
  [standards-registry.md](standards-registry.md) — standards usage policy and the
  project reference set.
