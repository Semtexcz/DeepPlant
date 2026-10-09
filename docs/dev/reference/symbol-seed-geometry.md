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
evidence:
  - Operator-authorized private engineering reference bundle (the relevant engineering standard and company/project P&ID material)
superseded_by: null
---

# Project-Owned Symbol Seed Geometry

> **Question this document answers:** where did the geometry of the implemented
> `generic-iso` symbols come from, and what may DeepPlant claim about it?

This is the DeepPlant **project specification** the current symbol
geometries are authored from. It is the provenance record behind
`AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only")` in
[symbol-library.md](symbol-library.md).

## What this is, and what it is not

These are DeepPlant-authored **seed geometries**: recognizable, generic
presentation glyphs for architecture validation, drawn on the canonical
normalized view box `0 0 100 100` (ADR-0008). They exist to prove the
definition → registry → renderer architecture, not to reproduce a standard.
This document is the canonical project-owned geometry specification for every
definition currently in the `deepplant.symbols` catalogue.

- They are **DeepPlant-original** and are **not** derived from normative standard
  artwork.
- They were **not** traced, extracted, auto-vectorized, or otherwise
  mechanically derived from the standard's artwork or from the company reference
  drawings, and no source coordinates or dimensions were mechanically transferred
  into a DeepPlant definition. The previous engineering review consulted relative
  visual proportions as reference evidence; the final normalized coordinates are
  independently selected DeepPlant project coordinates. Where an
  operator-authorized private reference was inspected for a concept, it informed
  the *engineering reading* only — which features carry the meaning and what the
  glyph must be recognizable as
  ([Authorized reference inspection](#authorized-reference-inspection)).
- They are **not** exact ISO geometry, and no ISO correspondence is claimed as
  verified.
- No standard figure, table, symbol artwork, locator, or normative wording is
  copied, traced, extracted, or recorded here.
- Generated SVG remains **derived** output of these definitions, never the
  canonical source, and it is never hand-edited ([symbol-library.md](symbol-library.md)).
- The standards relationship of each symbol is recorded separately, at the
  conservative `candidate-alignment` state — an *intended* correspondence with no
  human check claimed ([workflow/standards.md](../workflow/standards.md)). That
  state, and not a bare `reference`, is what the `generic-iso` profile requires,
  because `reference` claims no correspondence for a concrete geometry.

```text
project-owned seed geometry   this document
        ↓
SymbolDefinition              src/deepplant/symbols/catalogue.py
        ↓
generated SVG                 render_symbol_svg(definition)
```

## Authorized reference inspection

The geometry here is authored, not copied, but two authoring tasks were informed
by material the operator explicitly authorized for a specific task as a **private
local reference bundle**. Private-reference inspection is a project workflow gate,
not a licence override: it applies only when the operator is also entitled to
permit that AI use under the applicable rights (policy:
[workflow/standards.md](../workflow/standards.md#operator-authorized-private-reference-material)):

- the relevant **engineering standard**, inspected as the technical reference for
  what a concept's conventional notation actually is: its defining topology, and
  the features that distinguish it from neighbouring concepts;
- the **company/project P&ID material**, inspected as real-world corroboration:
  how the same concepts are drawn in an actual project legend and on a process
  sheet.

Both were used as engineering evidence only. Authorization to inspect is not
authorization to redistribute, and inspection is not verification:

- no source file, page, screenshot, crop, extracted image, table, title block, or
  project identifier is stored, quoted, or committed anywhere in this repository;
- no source artwork was traced, auto-vectorized, imported, or reproduced. No
  source coordinates or dimensions were mechanically transferred into the
  DeepPlant definition: the previous review consulted relative visual proportions
  as reference evidence, and the coordinates below are independently selected
  DeepPlant project coordinates on the canonical `0 0 100 100` box. No
  source-specific measured ratio is recorded here, and a standardized engineering
  shape naturally resembles the reference;
- no company-specific convention is adopted into the `generic-iso` profile: the
  reference material says *what* must be recognizable, while a project-specific
  representation would belong to a separate, explicitly scoped profile;
- the standards relationship of every definition stays `candidate-alignment`, an
  *intended* correspondence. A `human-verified` state still requires the recorded
  named-human check, which no agent inspection provides.

Seed E below is the case where that evidence changed the geometry: the previous
triangle-plus-seat-line reading was replaced once the reference inspection showed
which features actually carry the check-valve notation.

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

## Seed D — ball valve

ID: `valve.ball`. Purpose: recognizable generic ball-valve presentation glyph,
built on the same connectable body as the gate valve with the ball marked.

```text
line    (0, 50) → (28, 50)              process connection stub
polygon (28, 34), (28, 66), (50, 50)    left body
polygon (50, 50), (72, 34), (72, 66)    right body
circle  centre (50, 50), radius 8       ball on the process axis
line    (72, 50) → (100, 50)            process connection stub
```

Anchors: `port_a` at `(0, 50)`, orientation `west`, kind `process`; `port_b` at
`(100, 50)`, orientation `east`, kind `process`. A generic ball valve is not
inherently an inlet/outlet device, so the names stay neutral exactly as for the
gate valve, and no flow direction is encoded.

## Seed E — check valve

ID: `valve.check`. Purpose: recognizable generic check-valve presentation glyph
whose one-way character is carried by the geometry alone.

```text
line    (0, 50) → (28, 50)              process connection stub
polygon (28, 34), (28, 66), (50, 50)    upstream body half
polygon (50, 50), (72, 34), (72, 66)    downstream body half
circle  centre (28, 34), radius 8,      closure-element marker, upstream corner
        filled=True                     (solid; the only filled primitive)
line    (72, 50) → (100, 50)            process connection stub
```

Anchors: `inlet` at `(0, 50)`, orientation `west`, kind `process`; `outlet` at
`(100, 50)`, orientation `east`, kind `process`. This definition is the case
where a semantic connection *role* is meaningful: `inlet`/`outlet` name the role,
while `orientation` remains purely geometric and no `flow_direction` concept
exists on a generic anchor.

Engineering reading: the valve family shares **one connectable body** — two
triangles meeting apex to apex on the process axis, which is the body the gate
and ball valves already use. A check valve is that body with its **closure
element marked**: a distinctly separate circle sits on the body's *upstream top
corner*, above the process axis. The marker therefore exists on the inlet side
only, so the one-way character is carried by *where the marker sits* and not by
an arrow or by a flow-direction field, and the process connection stays on the
axis at both ends, which keeps the anchor contract unchanged.

Design notes:

- The marker keeps radius `8`, i.e. `0.5` of the body half-height — the same
  marker magnitude the ball valve already uses, and the same order as the
  closure-element mark the reference notation draws. Scale consistency inside the
  catalogue is deliberate: the marker's *position*, not its size, is what makes
  the glyph a check valve rather than a ball valve.
- The marker is drawn as a **solid** `currentColor` circle:
  `Circle(center=(28, 34), radius=8, filled=True)`. The renderer paints that
  primitive's interior with the themeable `currentColor` fill, so the closure
  element matches the reference's solid closure mark. It is the only filled
  primitive this slice requires, and `filled` is one binary graphical fact —
  hollow versus solid — not a styling option; every other circle in the catalogue
  stays hollow.
- The two body halves are `Polygon`s and the marker is a `Circle`, so the
  definition stays inside the existing `Line` / `Polygon` / `Circle` primitives.

Why this is not the earlier triangle-plus-seat-line reading: that reading drew a
lone triangle on the axis with a separate vertical line behind it, which shares
no body with the rest of the catalogue's valve family and reads as a generic
flow-direction marker rather than as a valve, and it is not the notation the
reference material uses for a check valve.

## Seed F — reducer

ID: `fitting.reducer`. Purpose: recognizable generic inline size-change fitting.

```text
line    (0, 50) → (28, 50)                              process connection stub
polygon (28, 34), (72, 42), (72, 58), (28, 66)          tapered body
line    (72, 50) → (100, 50)                            process connection stub
```

Anchors: `large_end` at `(0, 50)`, orientation `west`, kind `process`;
`small_end` at `(100, 50)`, orientation `east`, kind `process`. The names
describe the canonical geometry the drawing actually fixes; they deliberately
imply no process flow direction, because a reducer may be installed in either
orientation. They are therefore **not** named `inlet`/`outlet`.

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
