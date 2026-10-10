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
  concrete geometry. The `deepplant-default` restriction orifice instead records
  the weaker `reference` direction, which its profile permits and which likewise
  claims no correspondence for the concrete geometry
  ([workflow/standards.md](../workflow/standards.md)).

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

ID: `fitting.restriction_orifice`. Purpose: recognizable inline restriction / bore
presentation, and the first `deepplant-default` production representation (Issue
#130).

```text
line    (0, 50) → (42, 50)              process connection stub to the bore
circle  centre (50, 50), radius 8       expressed restriction / bore
line    (58, 50) → (100, 50)            process connection stub from the bore
```

Anchors: `port_a` at `(0, 50)`, orientation `west`, kind `process`; `port_b` at
`(100, 50)`, orientation `east`, kind `process`. The two stubs stop at the bore
edge, so the process axis is visibly interrupted by the restriction; inlet/outlet
and flow direction are again deliberately not encoded. This is an independently
authored DeepPlant practical `deepplant-default` representation — it reproduces no
standard figure and no company glyph, and it records no standards correspondence.

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
