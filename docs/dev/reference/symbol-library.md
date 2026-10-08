---
type: contract
status: active
canonical_for:
  - machine-rendered-symbol-library-contract
read_when:
  - symbol-asset-work
  - renderer-implementation
  - presentation-work
update_when:
  - symbol-contract-change
  - new-symbol
depends_on:
  - docs/dev/reference/symbol-seed-geometry.md
  - docs/dev/reference/mvp-symbol-coverage.md
  - docs/dev/reference/svg-symbols.md
  - docs/dev/workflow/standards.md
decision:
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0007-standards-and-symbol-provenance.md
  - docs/dev/decisions/ADR-0017-machine-rendered-symbol-definitions.md
evidence: []
superseded_by: null
---

# Machine-Rendered Symbol Library

> **Question this document answers:** how is one PFD/P&ID symbol defined,
> looked up, and turned into SVG, and what must a new symbol provide?

This is the developer-only contract for `deepplant.symbols` (Issue #119). It is
deliberately narrow: it describes the three representations the first slice
implements and the minimum machinery around them.

## Where this sits

Two different symbol mechanisms exist, and they are not the same thing:

| | `deepplant.symbols` (this document) | `basic` process pack ([svg-symbols.md](svg-symbols.md)) |
|---|---|---|
| Canonical geometry | a typed `SymbolDefinition` in Python | a hand-authored `.svg` asset file |
| Scope | standard PFD/P&ID representations | DeepPlant-original process/PFD fallback glyphs |
| Identity | stable symbol id (`valve.gate`) | presentation symbol role (`pump`) |
| Asset provenance | required per definition (`origin`, `license`) | recorded in the packaged pack README |
| Standards relationship | required by the `generic-iso` profile; `candidate-alignment` (intended, not human-verified) | `reference` / non-normative |

`docs/dev/reference/svg-symbols.md` and ADR-0008 remain in force for the
process pack. ADR-0017 records why the standard library takes the
definition-first route, and the process symbol pack is not retrofitted by this
slice.

## Flow

```text
project-owned seed geometry       docs/dev/reference/symbol-seed-geometry.md
        ↓
MVP/reference requirement        docs/dev/reference/mvp-symbol-coverage.md
        ↓
semantic concept                 valve / on-off isolation
        ↓
SymbolDefinition                 src/deepplant/symbols/catalogue.py
        ↓
registry                         SYMBOLS.get("valve.gate")
        ↓
renderer                         render_symbol_svg(definition)
        ↓
SVG                              generated output, never canonical source
        ↓
developer gallery                build/symbol-gallery, derived and ignored
```

The engineering object is never the SVG, the geometry is never hand-edited, and
no symbol carries a project tag, line number, or company convention. The
geometry itself is DeepPlant-authored project seed geometry
([symbol-seed-geometry.md](symbol-seed-geometry.md)): no standard figure or
company asset is copied, traced, or embedded.

## Coordinate system

Every coordinate is in the symbol's own normalized local view box,
`(min_x, min_y, width, height)`, canonical `0 0 100 100`
(`deepplant.symbols.CANONICAL_VIEW_BOX`). Coordinates are never screen pixels
and never depend on the consumer's zoom or sheet size.

The definition is validated on construction, so an invalid symbol fails at
import time rather than rendering badly:

- every primitive's coordinates must lie inside the declared view box;
- every anchor must lie inside or on the view box;
- the box must have a positive width and height.

`0 0 100 100` is the same normalized symbol-local box the process symbol pack
already uses (ADR-0008), so a future consumer has one coordinate convention.

## SymbolDefinition

```python
from deepplant.symbols import SYMBOLS, SymbolDefinition, render_symbol_svg

definition: SymbolDefinition = SYMBOLS.get("valve.gate")
svg: str = render_symbol_svg(definition)
```

| Field | Purpose |
|---|---|
| `symbol_id` | stable identity, a lowercase dotted name (`valve.gate`) |
| `name` | human-readable name |
| `category` | open catalogue subject area (`valve`, `equipment`, `instrument`) |
| `diagram_types` | the diagram types the representation may be drawn in |
| `profile` | the drawing profile the geometry belongs to |
| `primitives` | the geometry, in symbol-local coordinates |
| `anchors` | the explicit connection slots, in stable declaration order |
| `provenance` | required: where the geometry came from and under which licence |
| `standards` | the standards relationship and its verification state; optional at this level, but the `generic-iso` profile requires at least one intended correspondence |
| `view_box` | the normalized local coordinate box, canonical `0 0 100 100` |

`category` is an open string, like `ProcessStep.function` (ADR-0009): the
catalogue grows with the reference material rather than with a code change.
Everything else in the table that names a vocabulary is closed and validated.

### Primitives

Only the primitives the implemented symbols need exist:

| Primitive | Fields |
|---|---|
| `Line` | `x1`, `y1`, `x2`, `y2` |
| `Circle` | `cx`, `cy`, `r` (radius must be positive) |
| `Polygon` | `points` (at least three vertices, stroked outline) |

A further primitive is added when a verified symbol requires one. `Rect`,
`Ellipse`, `Polyline`, and grouping are deliberately not defined yet.

### Vocabularies

| Constant | Values |
|---|---|
| `PROFILES` | `generic-iso` |
| `DIAGRAM_TYPES` | `pfd`, `pid` |
| `ANCHOR_ORIENTATIONS` | `north`, `east`, `south`, `west` |
| `CONNECTION_KINDS` | `process`, `signal` |
| `ASSET_ORIGINS` | `deepplant-original` |
| `VERIFICATION_STATES` | `reference`, `candidate-alignment`, `human-verified` |

`generic-iso` is the canonical MVP drawing profile. It means DeepPlant-authored
geometry that is *intended* to correspond to the named standards, so the profile
itself requires at least one `StandardsReference` recording an intended
correspondence (`candidate-alignment` or `human-verified`); a bare `reference` is
not sufficient, because it claims no correspondence for a concrete geometry.
Company and project profiles (for example a Yara/CHPN profile) do not exist yet,
and adding one is a deliberate change to `PROFILES` plus its own provenance
rules. Standards correspondence stays **optional at the definition level** for
exactly that reason: a future company, project, or custom profile may legitimately
record none, and nothing invents a standards reference for it.

## Anchors

An anchor is a machine-readable connection slot: it says where a consumer may
attach a connection line. It is **not** inferred from the generated SVG, and it
is not a semantic connection object:

```text
symbol anchor != ProcessPort != Port != future Nozzle
```

The anchor contract has exactly two parts:

```text
orientation   geometric: which way the connection leaves the symbol
              (north / east / south / west), for routing and layout
kind          which connection class the slot accepts (process / signal)
```

```text
anchor orientation = geometric routing orientation
anchor kind        = process | signal
semantic flow direction is NOT part of the generic graphical anchor
```

`orientation` is deliberately *not* flow direction, signal direction, or
inlet/outlet meaning. A generic graphical anchor tells routing which way the line
leaves the symbol; engineering meaning comes from the anchor `name` and from
later semantic mapping. A generic gate valve therefore uses neutral `port_a` /
`port_b` connection names instead of `inlet` / `outlet`, while a pump keeps the
meaningful `suction` / `discharge` names and records their geometry separately
(`west` / `east`).

Each anchor also has a local `name` and an `x`/`y` position. Declaration order in
`SymbolDefinition.anchors` is the symbol's stable anchor order.

Validated invariants: names are unique within a symbol and match a lowercase
identifier, coordinates are finite and inside or on the view box, and
`orientation`/`kind` are vocabulary members.

## Standards relationship

The standards relationship is **optional at the definition level** and separate
from asset provenance; the `generic-iso` profile requires it (see
[profile requirement](#profile-requirement)). Each `StandardsReference` is
self-validating:

```python
StandardsReference(standard="ISO 10628-2:2012")  # -> verification="reference"
```

`standard` is the document identifier and edition. `locator` and `name` are
optional and stay unrecorded (`None`) until a permitted source or a recorded
human verification supplies them: the repository never copies a restricted
locator, table/figure reference, registration number, or the standard's own name
for a representation.

`verification` uses exactly the three canonical states of
[standards.md](../workflow/standards.md):

| State | Meaning | Evidence required |
|---|---|---|
| `reference` | the standard guides direction, terminology, or structure; no correspondence is claimed for this geometry | none |
| `candidate-alignment` | this concrete geometry is *intended* to correspond to the named standard, but no human has checked it against an authorized copy | none; **human verification is not a prerequisite for this state** |
| `human-verified` | a named human compared this concrete geometry against an authorized copy and recorded the result | a `locator`, `verified_by`, and `verified_on`; construction fails closed without them |

`verified_by` and `verified_on` are the human-verification evidence and may only
be recorded together with `human-verified`, so a `reference` or
`candidate-alignment` record can never misleadingly imply a human check. The
check may only be performed against material the verifier is entitled to use.
Until a symbol is `human-verified`, the repository must not present it as
standards-conformant (ADR-0007).

### Profile requirement

`reference` claims no correspondence for a concrete geometry, so it can never
make a symbol part of the profile whose meaning *is* intended correspondence. A
definition in `profile="generic-iso"` must therefore satisfy:

```text
at least one StandardsReference
and
every recorded relationship is an intended correspondence
    (candidate-alignment or human-verified)
```

Construction fails closed otherwise, so this is invalid:

```python
SymbolDefinition(..., profile="generic-iso", standards=())  # no standards
SymbolDefinition(
    ..., profile="generic-iso", standards=(StandardsReference(standard="ISO 10628-2:2012"),)
)
# -> bare `reference`: no intended correspondence
```

The requirement belongs to the profile, not to the class: standards
correspondence stays optional in `SymbolDefinition` for a future company,
project, or custom profile that has no standards relationship at all.

## Asset provenance

Every definition requires `AssetProvenance`, which answers a *different*
question from standards correspondence:

```python
AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only")
```

`origin` is one of `ASSET_ORIGINS`, which currently contains only
`deepplant-original`; `license` is the licence identifier the geometry is
distributed under. Both are validated on construction, so a distributed
definition cannot carry an unknown origin or a blank licence.

The pair also fails closed on an unsupported combination. Because this slice
supports exactly one origin, the rule is one explicit check rather than generic
licence policy:

```text
deepplant-original   ->   AGPL-3.0-only   (any other licence is rejected)
```

Third-party asset import is deferred until the first concrete third-party asset:
the two-field record is not sufficient for an imported asset, so no `third-party`
origin is accepted before the complete ADR-0007 provenance record (upstream
repository, ref, author/copyright holder, licence, modification state) is
implemented.

```text
asset provenance (origin, licence)  !=  standards correspondence (reference, state)
```

Consequences:

- all three definitions in the implemented catalogue are
  `origin="deepplant-original"`, `license="AGPL-3.0-only"`;
- a future company, project, or custom definition is a perfectly valid definition
  without a standards reference and must not be given a fake ISO reference, while
  the `generic-iso` profile requires an intended correspondence;
- copyright/licence provenance never implies a verification state, and vice
  versa.

This is a per-definition metadata record, not a runtime provenance manifest, an
asset-import pipeline, or an asset-management framework: those remain deferred
(ADR-0007, ADR-0017).


## Renderer

```python
def render_symbol_svg(definition: SymbolDefinition) -> str: ...
```

The renderer consumes only a definition and returns a complete standalone SVG
document with a trailing newline. Its output contract:

- **Deterministic.** The same definition renders byte-for-byte identically; a
  definition rebuilt from its own fields renders identically too.
- **Normalized.** An explicit `viewBox` and no fixed `width`/`height`, so the
  document scales like every other DeepPlant symbol asset.
- **Restricted.** One SVG namespace, and only `<svg>`, `<line>`, `<circle>`, and
  `<polygon>`: no text, scripts, event handlers, external references, `data:`
  URIs, raster images, or embedded fonts.
- **Themeable.** `fill="none"`, `stroke="currentColor"`, and a fixed
  `stroke-width` on the root, so a consumer themes it through `currentColor`.
  There is no styling engine, and none is planned until a consumer needs one.
- **Anchor-free.** Anchors are definition data and are deliberately *not*
  written into the document; a consumer reads them from the definition instead
  of inferring them from geometry.

## Registry

```python
SYMBOLS.get(symbol_id)  # -> SymbolDefinition, or SymbolDefinitionError
SYMBOLS.list()  # -> tuple[SymbolDefinition, ...] in symbol-id order
```

`SYMBOLS` is the built-in registry over the implemented catalogue;
`SymbolRegistry(definitions)` builds one over any definition iterable, which is
what the tests use. A duplicate symbol id is rejected at construction, and an
unknown id fails closed. There is no search, filter, variant, pack, or plugin
API: nothing needs one yet.

## Generating the symbol gallery

```bash
make symbol-gallery
```

The target renders every definition in `SYMBOLS.list()` through the production
`render_symbol_svg(definition)` into `build/symbol-gallery/` and prints a concise
summary:

```text
build/symbol-gallery/
├── .deepplant-symbol-gallery
├── index.html
└── symbols/
    ├── instrument.local.svg
    ├── pump.centrifugal.svg
    └── valve.gate.svg
```

The source-of-truth hierarchy stays one-way:

```text
SymbolDefinition  =  canonical symbol geometry
generated SVG     =  derived artifact
gallery           =  derived developer artifact
```

The gallery is a developer review aid, not a second catalogue: it maintains no
symbol id, name, metadata, anchor, or geometry of its own, so a newly registered
definition appears in it without a change to the generator. Each card shows the
definition's identity, the SVG the production renderer generated for it, every
anchor (name, coordinates, orientation, kind), the asset provenance, and the
standards relationship with its verification state. Anchor markers are
gallery-only CSS positioned from `SymbolDefinition.anchors`; nothing is written
back into the generated SVG, which stays anchor-free.

The page is static: embedded CSS only, no JavaScript, no remote resource, and no
raster preview, so `build/symbol-gallery/index.html` opens directly as a local
file. Generation is deterministic: the whole replacement is written beside the
target and swapped in only once it is complete, so a preview of a symbol that
left the registry cannot survive as a stale file and a failed refresh leaves the
previous gallery intact. The output directory is marked as generator-owned by
the `.deepplant-symbol-gallery` file the tool writes, so regeneration replaces
only a gallery directory the generator itself created, and the tool refuses —
before writing or deleting anything — to replace an existing directory that does
not carry that marker. The output is ignored (`build/` is in `.gitignore`), is
never committed, and is neither packaged nor a runtime dependency.

`make symbol-gallery` is the visual-review step that precedes expanding the
catalogue, and it is a review aid only. It checks presentation quality —
recognisability, centring, proportion, clipping, connection stubs meeting their
anchors, consistency with the rest of the catalogue. It does **not** establish
standards conformance and does **not** promote a symbol's standards relationship
to `human-verified`; that still requires the recorded human check against an
authorized copy ([workflow/standards.md](../workflow/standards.md)).

The expected developer workflow for adding or changing a symbol:

```text
add/update SymbolDefinition
        ↓
tests
        ↓
make symbol-gallery
        ↓
open build/symbol-gallery/index.html
        ↓
visually inspect geometry + anchors + provenance
        ↓
PR review
```

## Implemented catalogue

| Symbol id | Name | Diagram types | Anchors (name → orientation, kind) | Geometry |
|---|---|---|---|---|
| `valve.gate` | Gate valve | `pid` | `port_a` → `west`, `process`; `port_b` → `east`, `process` | Two triangles meeting apex to apex on the process axis, with a process line to each view-box edge. |
| `pump.centrifugal` | Centrifugal pump | `pfd`, `pid` | `suction` → `west`, `process`; `discharge` → `east`, `process` | A circular casing with a full horizontal line through it and two lines running from the casing top and bottom to the casing's right-hand point. |
| `instrument.local` | Local/field instrument | `pid` | `tap` → `south`, `process` | A plain instrument circle joined to the process by one vertical functional connection line. |

The exact primitive construction of each is recorded in
[symbol-seed-geometry.md](symbol-seed-geometry.md) — the project-owned spec all
three are authored from.

All three are `generic-iso`, DeepPlant-authored project seed geometry under
`AGPL-3.0-only` (`AssetProvenance(origin="deepplant-original",
license="AGPL-3.0-only")`): no standard figure or company asset was copied,
traced, or embedded, and none is claimed to be exact ISO geometry. Each records
its standards relationship conservatively at `candidate-alignment` - ISO
10628-2:2012 for the valve and the pump, ISO 15519-2:2015 for the instrument -
meaning the geometry is *intended* to correspond to that document, but no human
has checked it against an authorized copy. `candidate-alignment` claims no human
verification, and none of the three is `reference` or `human-verified`. The
coverage matrix records the concepts still to come
([mvp-symbol-coverage.md](mvp-symbol-coverage.md)).

The gate valve deliberately has no semantic inlet/outlet anchor contract: a
generic gate valve is not inherently an inlet/outlet device, so its ports are
named neutrally and carry only a geometric orientation. The pump keeps the
meaningful `suction`/`discharge` names, and its geometry records only where each
line leaves the symbol. The local instrument is the reusable base graphic with
one process tap and **no** mandatory signal anchor: a local indicator may have no
outgoing signal while a transmitter does, so a signal connection belongs to a
later concrete instrument-function composition, not to the base graphic.

A project tag such as `FV-101`, a line number, or a function letter code such as
`PIT` is **never** part of a definition. Instrument letter codes are composition
onto a base graphic, not geometry, and no separate `PIT`/`TI`/`FIC` symbol is
created.

## Adding a symbol

1. Find the concept in the coverage matrix
   ([mvp-symbol-coverage.md](mvp-symbol-coverage.md)); if it is not there, add
   it first.
2. Record the standard identifier (and edition) the representation is intended to
   align with: required for `generic-iso`, where the relationship must be at
   `candidate-alignment` or `human-verified`, and recorded together with the asset
   provenance (`deepplant-original` under `AGPL-3.0-only`). Do **not** record a
   locator, table/figure reference, registration number, or the standard's own
   name unless it comes from a permitted source or a recorded human verification.
3. Author the geometry independently from the primitives. Do not trace, extract,
   or reproduce standard artwork, and do not derive geometry from a company
   reference drawing.
4. Add a `SymbolDefinition` (with explicit anchors, geometric `orientation`, and
   `AssetProvenance`) to `src/deepplant/symbols/catalogue.py`.
5. Add the coverage-matrix row's status and the structural test for the new
   symbol.
6. Run `make symbol-gallery` and inspect the new symbol in
   `build/symbol-gallery/index.html` — geometry, anchor markers, asset
   provenance, and standards state — before requesting review.
7. Run `uv run pytest tests/symbols`, `make format-check`, `make lint`,
   `make typecheck`, and `make architecture-check`; run `make check` once before
   finalizing the pull request.

## Explicitly deferred

- The rest of the MVP catalogue, full valve families, all pump types, DCS/SIS
  symbols, and company/Yara-CHPN profiles.
- Composition and variant machinery: instrument letter-code composition, signal
  connections for instrument functions that have one, control valves with
  actuators, instruments with displays, multifunction instruments.
- Gallery extensions: filtering, search, side-by-side comparison, and any
  generated artifact other than the static developer page. The gallery itself now
  exists as the derived developer artifact delivered by Issue #121
  ([Generating the symbol gallery](#generating-the-symbol-gallery)); it stays a
  review aid, not a catalogue and not a conformance statement.
- Runtime provenance manifests, pack configuration, custom-pack loading, and
  arbitrary SVG import.
- Editor integration, drag-and-drop, routing, layout, DEXPI graphics, and tag or
  line-number generation.
- Writing anchor slots (or any editor metadata) into generated SVG.

## Related

- [mvp-symbol-coverage.md](mvp-symbol-coverage.md) — the MVP coverage matrix and
  per-concept status.
- [svg-symbols.md](svg-symbols.md) — the separate process symbol-pack and anchor
  contract, still in force.
- [../../contracts/rendering.md](../../contracts/rendering.md) — the headless
  process/PFD renderer that consumes the process pack.
- [../workflow/standards.md](../workflow/standards.md) and
  [standards-registry.md](standards-registry.md) — standards usage and the
  project reference set.
- [../decisions/ADR-0017-machine-rendered-symbol-definitions.md](../decisions/ADR-0017-machine-rendered-symbol-definitions.md)
  — the decision behind this contract.

