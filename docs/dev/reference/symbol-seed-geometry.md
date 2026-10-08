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
- They were **not** traced, measured, extracted, or otherwise derived from the
  standard's artwork or from the company reference drawings.
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
polygon (28, 34), (28, 66), (58, 50)    body triangle
line    (62, 34) → (62, 66)             seat line, separated by a gap
line    (62, 50) → (100, 50)            process connection stub
```

Anchors: `inlet` at `(0, 50)`, orientation `west`, kind `process`; `outlet` at
`(100, 50)`, orientation `east`, kind `process`. This definition is the case
where a semantic connection *role* is meaningful: `inlet`/`outlet` name the role,
while `orientation` remains purely geometric and no `flow_direction` concept
exists on a generic anchor. The 4-unit gap between the triangle apex at
`x = 58` and the seat line at `x = 62` is deliberate: it keeps the two marks from
merging into one shape.

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
