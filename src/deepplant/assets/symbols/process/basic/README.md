# DeepPlant basic process symbol pack

This directory is the initial `basic` pack. It is the canonical packaged
asset tree, installed inside the Python package under
`src/deepplant/assets/symbols/process/basic/`, so the headless process
renderer (`deepplant.render.render_process_svg`) can resolve it at runtime
through `importlib.resources`. It contains DeepPlant-original
fallback/reference SVG realizations of the **presentation symbol roles**
resolved for [examples/realistic-process-fragment/plant.yaml](../../../../../../examples/realistic-process-fragment/plant.yaml):
`source`, `mixing`, `pump`, `heat_exchanger`, `splitting`, `vessel`, and
`sink`. Roles are presentation semantics (ADR-0009), never canonical
engineering classifications; `ProcessStep.function` values such as `pumping`
or `heat_exchange` are distinct from these roles.

```text
pack: basic
origin: DeepPlant-original
licence: AGPL-3.0-only
purpose: fallback/reference implementation, contract validation, renderer
         development, and custom-symbol example
standards status: non-normative / unverified
```

The SVG + anchor contract is defined in [docs/svg-symbols.md](../../../../../../docs/svg-symbols.md)
and decided in [ADR-0008](../../../../../../docs/decisions/ADR-0008-process-svg-symbol-and-anchor-contract.md).

## Role, pack, and asset

A **symbol role** is a presentation category chosen at the rendering boundary
by the renderer's default `ProcessStep.function` -> role presentation policy
or by an explicit per-step `symbol_role_overrides` entry; it is never stored
on the semantic model. This `basic` pack realizes each covered role through
the filename convention `<role>.svg`; for example, role `pump` is realized
here by `basic/pump.svg`. A future standards-aligned, company, or custom pack
may realize the same role with materially different geometry and anchors.

## Provenance

Every SVG here is **DeepPlant-original** and independently authored. No
ISO/ISA/IEC figure was copied, traced, screenshot-reused, or AI-derived. No
geometry from draw.io, IPD Studio, ISPF, or any other third-party pack was
copied or adapted. This pack is governed by
[docs/standards.md](../../../../../../docs/standards.md) and
[ADR-0007](../../../../../../docs/decisions/ADR-0007-standards-and-symbol-provenance.md).

| Role | File | Origin | Licence | Copyright holder | Modification state | Upstream revision | Standards status |
|---|---|---|---|---|---|---|---|
| `source` | `source.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — non-normative fallback process-boundary glyph |
| `mixing` | `mixing.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — non-normative fallback process-function glyph |
| `pump` | `pump.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — non-normative fallback pumping-role glyph; not a standards-aligned pack asset |
| `heat_exchanger` | `heat_exchanger.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — non-normative fallback heat-exchange-role glyph; not a standards-aligned pack asset |
| `splitting` | `splitting.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — non-normative fallback process-function glyph |
| `vessel` | `vessel.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — non-normative fallback containment-role glyph; not a standards-aligned pack asset |
| `sink` | `sink.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — non-normative fallback process-boundary glyph |

These are non-normative DeepPlant-original fallback/basic glyphs. They express
each presentation symbol role sufficiently for the basic renderer and the
contract tests. They are not the definitive PFD/P&ID symbol library and are not
intended to replace a standards-aligned equipment-symbol pack. A future
standards-aligned pack may use materially different geometry after explicit
rights, per-asset provenance, and human verification against an authorized
copy.

## Anchor cardinalities (current basic variants)

| Role | Inputs | Outputs |
|---|---|---|
| `source` | 0 | 1 |
| `mixing` | 2 | 1 |
| `pump` | 1 | 1 |
| `heat_exchanger` | 1 | 1 |
| `splitting` | 1 | 2 |
| `vessel` | 1 | 1 |
| `sink` | 1 | 0 |

These counts are properties of the current `basic` variants only. They are not
semantic invariants, and a different pack can use different geometry and anchor
cardinalities for the same roles.

## Scope note

This is a process/PFD presentation pack for `ProcessStep` only — not
`Equipment`, `Port`, `Connection`, physical nozzles, or piping. `FV-101` in the
realistic fragment is a physical control valve and is intentionally not
represented here. The renderer (`render_process_svg`) renders `ProcessModel`,
not the physical P&ID topology.

## Runtime packaging

The canonical copy of this pack ships inside the installed Python package
(`deepplant/assets/symbols/process/basic/`); the headless process renderer
resolves it at runtime through `importlib.resources`, so it works from a
source checkout and from an installed wheel. The wheel is verified to contain
these SVG assets.

This is a human-readable provenance record, not a runtime provenance manifest.
