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
  concrete geometry. The nine `deepplant-default` geometries (the restriction
  orifice, the three Issue #132 basic valves, and the five Issue #135 base
  representations) record **no** standards relationship at all, which their profile
  permits because they make no
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

## Seed H — three-way valve

ID: `valve.three_way`. Purpose: recognizable three-port valve presentation, added by
Issue #135 as one of the remaining MVP base P&ID representations.

```text
line    (0, 40)  → (24, 40)               west process connection stub
polygon (24, 22), (24, 58), (50, 40)      west body
polygon (76, 22), (76, 58), (50, 40)      east body
polygon (32, 74), (68, 74), (50, 40)      south body
line    (76, 40) → (100, 40)              east process connection stub
line    (50, 74) → (50, 100)              south process connection stub
```

The intrinsic glyph is **three** triangular body halves meeting at one junction
point `(50, 40)`: a west body and an east body on the process axis, and a third body
leaving that axis orthogonally to the south. The third connection is therefore real
body geometry, not a mark painted on the two-port bowtie, and it is what makes this a
three-port representation. No body overlaps another and none carries a line through
its interior.

Deliberately absent: any stem, handwheel, lever, or actuator, any flow arrow or
selected-path mark, any tag or line number, and any annotation. Path selection is a
document or operating state, so the reusable base representation states nothing about
which path is open. No `inlet`/`outlet`/`common` name is encoded either.

Anchors: `port_a` at `(0, 40)`, orientation `west`, kind `process`; `port_b` at
`(100, 40)`, orientation `east`, kind `process`; `port_c` at `(50, 100)`, orientation
`south`, kind `process`. One port per body, named neutrally, with the orientation
recording only where a line leaves the symbol.

Standards state: **no** relationship recorded, for the same reason as seeds E/F/G.

## Seed I — straight safety/relief valve

ID: `valve.safety_relief.straight`. Purpose: recognizable straight-through
safety/relief valve presentation, added by Issue #135. One of the two forms of Core
requirement A14.

```text
line    (0, 60)  → (28, 60)             west process connection stub
polygon (28, 44), (28, 76), (50, 60)    west body
polygon (50, 60), (72, 44), (72, 76)    east body
line    (72, 60) → (100, 60)            east process connection stub
line    (50, 60) → (50, 16)             spring-loaded indication stem
line    (44, 40) → (56, 32)             spring load mark 1
line    (44, 32) → (56, 24)             spring load mark 2
line    (44, 24) → (56, 16)             spring load mark 3
```

The intrinsic glyph is a two-port valve body plus a **spring-loaded indication**: a
stem on the body's axis and three parallel load marks crossing it. That indication,
not a tag, letter code, or annotation, is what makes the device recognizably a
safety/relief valve rather than a plain valve. Each load mark is drawn as its own
"line", never as a closed `Polygon` (a polygon closes its path and would add a
spurious edge).

In this straight form both process connections stay on one axis, and the spring
indication is drawn on the body's perpendicular stem. The angle form is seed J: the
two forms differ in real connection topology, so they are two definitions and not one
definition with a variant selector.

Deliberately absent: any discharge or flow-direction arrow, any set-pressure value,
tag, or annotation. A relief set pressure is authored document data (D04) and is never
embedded in reusable base geometry, and a discharge arrow would add flow semantics the
base glyph does not own.

Anchors: `port_a` at `(0, 60)`, orientation `west`, kind `process`; `port_b` at
`(100, 60)`, orientation `east`, kind `process`. The pair is neutral: the spring mark
is a recognizability mark, not a flow-direction contract.

Standards state: **no** relationship recorded, for the same reason as seeds E/F/G. The
coverage matrix names a concept-level ISO reference direction for A14; that is not a
correspondence for this geometry.

## Seed J — angle safety/relief valve

ID: `valve.safety_relief.angle`. Purpose: recognizable angle safety/relief valve
presentation, added by Issue #135. The second form of A14.

```text
line    (0, 48)  → (24, 48)             west process connection stub
polygon (24, 28), (24, 64), (50, 48)    west body
polygon (32, 80), (68, 80), (50, 48)    south body
line    (50, 80) → (50, 100)            south process connection stub
line    (50, 48) → (50, 18)             spring-loaded indication stem
line    (44, 36) → (56, 28)             spring load mark 1
line    (44, 28) → (56, 20)             spring load mark 2
line    (44, 20) → (56, 12)             spring load mark 3
```

The intrinsic glyph is the same reusable safety/relief form as seed I — a valve body
plus the spring-loaded indication — but the second process connection leaves the body
orthogonally instead of continuing the axis, so the body is bent rather than
straight-through. The spring indication is drawn on the body axis above the junction,
so it reads as the valve's stem and load rather than as an actuator or as a line
treatment on the process line.

The angle form is **not** a rotated straight form: `port_b` is a genuine south
connection at `(50, 100)`, and the bent body is a different connection topology. Both
forms are one Core requirement (A14) with two reviewed forms, which is why they are
two definitions rather than one definition with a variant selector.

Deliberately absent: any discharge or flow-direction arrow, any set-pressure value,
tag, or annotation, for the same reasons as seed I.

Anchors: `port_a` at `(0, 48)`, orientation `west`, kind `process`; `port_b` at
`(50, 100)`, orientation `south`, kind `process`.

Standards state: **no** relationship recorded, for the same reason as seed I.

## Seed K — two-sloping-side reducer

ID: `fitting.reducer.concentric`. Purpose: recognizable two-sloping-side reducer
presentation, added by Issue #135. One of the two forms of Core requirement A16.

```text
line    (0, 50)  → (25, 50)                       west process connection stub
polygon (25, 14), (75, 32), (75, 68), (25, 86)    tapering body, symmetric
line    (75, 50) → (100, 50)                      east process connection stub
```

The intrinsic glyph is a single closed polygon that tapers **symmetrically** about the
process axis: the west end plane at `x = 25` is 72 units tall and the east end plane
at `x = 75` is 36 units tall, with equal offsets on each side of the axis, so both
connection faces stay centred on the same axis and both anchors stay collinear.

The body is authored **tall and compact**, not long and shallow: the larger end is the
visually dominant vertical face, the smaller end is about half its height and still
reads as a face rather than as a line, and the two end faces are closer together than
either of them is tall, so both connecting sides rise **steeply** into the small end.
The silhouette is a tall taper, not a shallow length of duct. No nominal size, bore,
or `DN` value is embedded.

Deliberately absent: any tag, size value, tag bubble, or leader line, which are
authored document data rather than reusable base geometry.

Anchors: `port_a` at `(0, 50)`, orientation `west`, kind `process`; `port_b` at
`(100, 50)`, orientation `east`, kind `process`. The canonical normalized form is
DeepPlant-authored and drawn horizontally with the taper running west to east; a
document that mirrors it or draws the fitting on a vertical process line rotates or
mirrors the placement, which is presentation rather than this geometry. No flow
direction is encoded.

Standards state: **no** relationship recorded, for the same reason as seeds E/F/G. The
coverage matrix names a concept-level ISO reference direction for A16; that is not a
correspondence for this geometry.

## Seed L — one-flat-side reducer

ID: `fitting.reducer.eccentric`. Purpose: recognizable one-flat-side reducer
presentation, added by Issue #135. The second form of A16.

```text
line    (0, 50)  → (25, 50)                     west stub, at the larger end face centre
polygon (25, 14), (75, 14), (75, 50), (25, 86)  tapering body, flat side, one-sided
line    (75, 32) → (100, 32)                    east stub, at the smaller end face centre
```

The intrinsic glyph is a single closed polygon with the **same end sizes, the same
end-face planes, the same body extent and the same tall/compact proportions as seed
K** — 72 units at the west end plane `x = 25` and 36 units at the east end plane
`x = 75` — but with a **one-sided** taper. The edge from `(25, 14)` to `(75, 14)` is a
straight side parallel to the process axis along the top of the larger face, and the
opposite edge `(25, 86)` to `(75, 50)` carries the whole reduction. The form is
therefore one long horizontal side plus one long **sloping** side whose diagonal is
clearly steeper than either slope of seed K, rather than a shallow trapezoid. That
offset is what distinguishes this form from seed K, and it cannot be produced by
rotating the two-sloping-side form, which stays symmetric about the axis under
rotation.

Each connection stub leaves through the **centre of its own end face**, as on every
other inline representation in this library: `port_a` is the centre of the larger west
face `(25, 14)–(25, 86)` and `port_b` the centre of the smaller east face
`(75, 14)–(75, 50)`. The two anchors are therefore offset by 18 units, which is
exactly half the end-size difference — the eccentricity the fitting exists to create —
and the larger west end keeps the same face centre, and the same stub, as seed K.
Placing each connection point at its own face centre is deliberate: drawing both stubs
collinear with the flat side would put them on the end *corners* instead of through
the middle of the ends.

That anchor offset is geometry and **not** a semantic direction: no
`flat_on_top`/`flat_on_bottom` field, and no `inlet`/`outlet` name, is added to the
anchors.

Deliberately absent: any tag, size value, or leader line, for the same reason as seed
K.

Anchors: `port_a` at `(0, 50)`, orientation `west`, kind `process`; `port_b` at
`(100, 32)`, orientation `east`, kind `process`. As with seed K, the canonical form is
drawn horizontally with the larger end west, and a document may mirror or rotate the
placement.

Standards state: **no** relationship recorded, for the same reason as seed K.

The five seeds H/I/J/K/L were authored after a qualitative visual review of the
operator's curated private reference material: the MVP P&ID symbol legend and the
actual MVP P&ID occurrence pages. In that review, two private gallery entries for
different valve forms turned out to be byte-identical copies, so the legend and the
occurrence pages — not the gallery filenames — established the reviewed A12 and A14
forms; the released evidence for this slice is the legend and the occurred notation,
not a gallery listing. That material informed only the qualitative notation, the
occurrence, and the structural decomposition into body, indication or variant mark,
and connection geometry. A discharge/flow arrow and a relief set pressure were
observed in the reference and are deliberately **not** embedded, because they are flow
semantics and authored document data rather than reusable base geometry. No private
artwork was measured, traced, vectorised, or copied, these coordinates are
independently DeepPlant-authored, and no private filename, path, drawing identifier,
tag, or measurement is recorded here.

A later operator visual review of the same curated material corrected the **body
proportions** of seeds K and L, whose first authored pass read as too long and too
shallow beside the selected reference silhouettes. Both forms were re-authored as a
steeper, taller and more compact taper with a visually dominant larger end, as
described above. That correction changed qualitative shape only: the two topologies,
the stable ids, the shared end-face planes and end sizes, and the connection
decomposition are unchanged, and no source dimension, pixel proportion, or traced
geometry was copied or transferred — these coordinates remain independently
DeepPlant-authored.

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
