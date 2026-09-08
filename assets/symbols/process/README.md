# assets/symbols/process — DeepPlant process/PFD symbol assets

First DeepPlant presentation-asset slice: a seven-symbol process/PFD set for the
`ProcessStep.type` values used by
[examples/realistic-process-fragment](../../../examples/realistic-process-fragment/plant.yaml):

```text
source
mixing
pump
heat_exchanger
splitting
vessel
sink
```

The SVG + anchor contract is defined in [docs/svg-symbols.md](../../../docs/svg-symbols.md)
and decided in [ADR-0008](../../../docs/decisions/ADR-0008-process-svg-symbol-and-anchor-contract.md).

## Provenance

Every asset in this directory is **DeepPlant-original**: independently authored
line geometry for this repository. No ISO/ISA/IEC figure was copied, traced, or
AI-derived; nothing from draw.io, IPD Studio, ISPF, or any other third-party
pack was copied or adapted. This directory is governed by
[docs/standards.md](../../../docs/standards.md) and
[ADR-0007](../../../docs/decisions/ADR-0007-standards-and-symbol-provenance.md).

| Symbol id | File | Origin | Licence | Copyright holder | Modification state | Upstream revision | Standards alignment |
|---|---|---|---|---|---|---|---|
| `source` | `source.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — no ISO equipment correspondence forced (process-graph boundary concept) |
| `mixing` | `mixing.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — no ISO equipment correspondence forced (process-function glyph) |
| `pump` | `pump.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `candidate-alignment` — intended to read as a pumping function; ISO 10628-2 / ISO 14617 are future human-verification references; not `human-verified` |
| `heat_exchanger` | `heat_exchanger.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `candidate-alignment` — intended to read as heat exchange; ISO 10628-2 / ISO 14617 are future human-verification references; not `human-verified` |
| `splitting` | `splitting.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — no ISO equipment correspondence forced (process-function glyph) |
| `vessel` | `vessel.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `candidate-alignment` — intended to read as containment; ISO 10628-2 / ISO 14617 are future human-verification references; not `human-verified` |
| `sink` | `sink.svg` | DeepPlant-original | AGPL-3.0-only | DeepPlant contributors | Original, unmodified | None (original asset) | `reference` — no ISO equipment correspondence forced (process-graph boundary concept) |

No asset in this directory is claimed to be ISO/ISA/standards compliant. Visual
conventions are ordinary, independently known process-engineering drawing
vocabulary; correspondence with any restricted standard remains **unverified**
until a named human checks it against an authorized copy and records the result.

## Anchor cardinalities (current variants)

| Symbol id | Inputs | Outputs |
|---|---|---|
| `source` | 0 | 1 |
| `mixing` | 2 | 1 |
| `pump` | 1 | 1 |
| `heat_exchanger` | 1 | 1 |
| `splitting` | 1 | 2 |
| `vessel` | 1 | 1 |
| `sink` | 1 | 0 |

These are properties of the current symbol variants only. They are not semantic
invariants: no validator in the domain model enforces them, and future variants
may differ.

## Scope note

This is a process/PFD presentation set. It represents `ProcessStep` only — not
`Equipment`, `Port`, `Connection`, physical nozzles, or piping. `FV-101` in the
realistic fragment is a physical control valve and is intentionally not
represented here. A future renderer renders `ProcessModel`, not the physical
P&ID topology.

This is a human-readable provenance record, not a machine-readable provenance
framework. A machine-readable manifest is deferred until the renderer needs
runtime asset lookup.
