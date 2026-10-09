---
type: reference
status: active
canonical_for:
  - mvp-symbol-coverage-matrix
read_when:
  - symbol-asset-work
  - feature-planning
  - standards-alignment-claim
update_when:
  - mvp-symbol-scope-change
  - symbol-implementation-change
depends_on:
  - docs/dev/reference/symbol-library.md
  - docs/dev/reference/svg-symbols.md
  - docs/dev/workflow/standards.md
decision:
  - docs/dev/decisions/ADR-0007-standards-and-symbol-provenance.md
  - docs/dev/decisions/ADR-0017-machine-rendered-symbol-definitions.md
evidence:
  - DeepPlant MVP drawing support profile v0.1 (private reference bundle)
superseded_by: null
---

# MVP Symbol Coverage Matrix

> **Question this document answers:** which engineering concepts must the
> DeepPlant MVP be able to draw, how is each one meant to be represented, and how
> far has each one actually been implemented?

This is the Phase 0 coverage analysis behind
[Issue #119](https://github.com/Semtexcz/DeepPlant/issues/119). It is evidence
and routing data, not a contract: the rendering contract for implemented symbols
is [symbol-library.md](symbol-library.md).

## MVP Core selection

Issue #119 scopes the MVP to a deliberate vocabulary subset, the **MVP Core**:
the concepts the PFD and P&ID acceptance scenes must be able to draw, and nothing
else. The selection is derived from the operator-authored MVP drawing profile and
confirmed against production usage in
[../research/mvp-symbol-core-selection.md](../research/mvp-symbol-core-selection.md);
that evidence document owns the derivation, and this matrix owns each concept's
classification and status.

```text
28 Core entries    base symbols, composites, connections, annotations
 3 implemented     valve.gate, pump.centrifugal, instrument.local
25 remaining       planned, deferred, or out of the base library
```

Two rules follow from the selection, and both are already this matrix's rules:

- one representation per engineering concept — never one symbol per project code
  (`PI`, `PIT`, `TI`, `FIC`, `LIC` stay text composed onto a base graphic);
- company tag prefixes, fluid and insulation codes, line-designation rules,
  DCS/SIS practice, and corporate title blocks are `project-convention`, never
  base-library assets.

The Core is closed for MVP acceptance purposes: widening it is a profile change,
not a symbol implementation.

## Three different facts

The matrix keeps three separate statements apart, because they advance
independently:

```text
required by the MVP reference      does the MVP need this concept?
standards relationship            reference / candidate-alignment / human-verified
implemented in DeepPlant           does a SymbolDefinition exist yet?
```

```text
required by MVP reference
        ↓ independent
standards relationship
        ↓ independent
implementation state
```

A concept can be required and unimplemented, or implemented with no human check
claimed. Only the third state produces a symbol. The repository deliberately
records no restricted-derived symbol locator for the three current symbols, so no
row claims that a standard's own representation was located, inspected, or
assessed.

## Classification vocabulary

Per Issue #119, each concept is classified as exactly one of:

| Classification | Meaning |
|---|---|
| `symbol` | one standalone graphical representation |
| `composed-symbol` | a representation assembled from two or more base graphics |
| `annotation` | text, labels, or a rule that is not symbol geometry |
| `connection` | a line or link convention between objects |
| `project-convention` | company/project practice that is not part of a standard library |
| `composite-typical` | a reusable project-specific arrangement referencing a typical diagram |

## Verification vocabulary

The verification column uses exactly the canonical states of
[standards.md](../workflow/standards.md); a concept with no recorded standards
relationship is `reference`, because no correspondence is claimed for it either
way:

| State | Meaning for a coverage row |
|---|---|
| `reference` | the standard is named as the reference direction for this concept; no correspondence is claimed for any concrete geometry |
| `candidate-alignment` | this concrete geometry is *intended* to correspond to the standard, but no human has compared it against an authorized copy; no human verification is required for this state |
| `human-verified` | a human compared the DeepPlant geometry against an authorized copy and recorded the result |

No row is `human-verified`, and none may claim the standard's own locators or
construction: the standard's identifier is recorded, the standard's tables,
figures, and item numbers are not. The repository records no restricted-derived
symbol locator for the current symbols, so no row may claim that a standard's own
representation was located, inspected, or assessed.

## Reference material handling

The MVP reference bundle (the YARA / Chemoproject PFD, P&ID, and stretch
drawings, summarised by the *DeepPlant MVP drawing support profile v0.1*) is
private project material. It answers **what must be drawable**; it is never a
source of geometry. No symbol is copied, vectorised, traced, or measured from
it, and no title block, tag, note, or symbol sheet is reproduced
([standards.md](../workflow/standards.md), ADR-0007).

The companies' own conventions (tag prefixes, line designation, DCS/SIS
practice, interlock numbering) are recorded here as `project-convention` so they
cannot be mistaken for a standard base library.

## PFD / process concepts

| Reference concept | Semantic concept | Classification | Category | Standard evidence & verification | Representation strategy | Variants | Project-specific | MVP | Status |
|---|---|---|---|---|---|---|---|---|---|
| Process boundary feed / product | process boundary connector | `annotation` | boundary | `generic-iso`; no standards relationship recorded yet; `reference` | boundary marker plus a label, never equipment geometry | incoming / outgoing | label text is project-specific | yes | planned |
| Filter | separation by filtration | `symbol` | equipment | `generic-iso`; no standards relationship recorded yet; `reference` | equipment outline with process anchors | liquid / gas | no | yes | planned |
| Compressor | compression | `symbol` | equipment | `generic-iso`; no standards relationship recorded yet; `reference` | equipment outline with process anchors | centrifugal / reciprocating | no | yes | planned |
| Air heater / superheater | heat exchange | `symbol` | equipment | `generic-iso`; no standards relationship recorded yet; `reference` | equipment outline with process anchors | heater / exchanger forms | no | yes | planned |
| Mixer | mixing | `symbol` | equipment | `generic-iso`; no standards relationship recorded yet; `reference` | equipment outline with multiple process anchors | 2-inlet / multi-inlet | no | yes | planned |
| Burner / reactor | reaction | `symbol` | equipment | `generic-iso`; no standards relationship recorded yet; `reference` | equipment outline with anchored connections | burner / vessel reactor | no | yes | planned |
| Pump | pumping | `symbol` | equipment | **ISO 10628-2:2012** (intended correspondence, not human-verified); `candidate-alignment` | DeepPlant-authored project seed geometry: a circular casing with a horizontal process line and two internal lines, recorded in [symbol-seed-geometry.md](symbol-seed-geometry.md) and [symbol-library.md](symbol-library.md) | centrifugal implemented; other pump types planned | no | yes | **implemented** (`pump.centrifugal`) |
| Storage / hold-up tank | storing material | `symbol` | equipment | `generic-iso`; no standards relationship recorded yet; `reference` | containment outline with process anchors | tank / vessel forms | no | optional | planned |
| Directional process stream | process stream | `connection` | piping | ISO 15519-2:2015 (connection conventions); `reference` | routed line plus an arrowhead | arrow forms | no | yes | already drawn by the process renderer as output, not as a symbol definition |
| Stream number label | process stream annotation | `annotation` | annotation | not a graphical symbol; numbering practice is company-specific | text placed along a stream | — | yes | yes | planned (text, never geometry) |
| Equipment tag label | equipment annotation | `annotation` | annotation | not a graphical symbol | text placed beside the representation | — | prefix rules are project-specific | yes | planned (text, never geometry) |
| Automatic stream property table | annotation | `annotation` | annotation | — | the MVP Properties panel, not an automatic drawing table | — | no | out of scope for v0.1 | deferred |


## P&ID / physical concepts

| Reference concept | Semantic concept | Classification | Category | Standard evidence & verification | Representation strategy | Variants | Project-specific | MVP | Status |
|---|---|---|---|---|---|---|---|---|---|
| Piping line | piping connection | `connection` | piping | ISO 15519-2:2015 (connection conventions); `reference` | routed line between connection points | line-width conventions | no | yes | planned |
| Gate valve | on/off isolation | `symbol` | valve | **ISO 10628-2:2012** (intended correspondence, not human-verified); `candidate-alignment` | DeepPlant-authored project seed geometry: a bowtie of two triangles meeting apex to apex on the process axis, with two neutral process ports (`port_a` west / `port_b` east) and no flow semantics, in [symbol-seed-geometry.md](symbol-seed-geometry.md) | none implemented | no | yes | **implemented** (`valve.gate`) |
| Globe / ball / needle valve | throttling isolation | `symbol` | valve | ISO 10628-2:2012 (reference direction); `reference` | bowtie body with the variant's internal mark | globe / ball / needle | no | yes | planned |
| Check valve | one-way flow | `symbol` | valve | ISO 10628-2:2012 (reference direction); `reference` | bowtie body with the variant's flow mark | swing / globe | no | yes | planned |
| Safety / relief valve | overpressure protection | `symbol` | valve | ISO 10628-2:2012 (reference direction); `reference` | valve body with a spring-loaded indication | straight / angle | no | yes | planned |
| Control valve with actuator | control function | `composed-symbol` | valve | ISO 10628-2:2012 and ISO 15519-2:2015 (actuator conventions); `reference` | a valve body composed with an actuator graphic, not a new standalone symbol | diaphragm / cylinder / motor | no | yes | planned (composition framework deferred) |
| Fittings: strainer, reducer, blind, orifice plate | inline fitting | `symbol` | fitting | ISO 10628-2:2012 (reference direction); `reference` | small inline graphic on the piping axis | by fitting type | no | yes | planned |
| Process equipment in P&ID: vessel, column, exchanger, filter | equipment item | `symbol` | equipment | `generic-iso`; no standards relationship recorded yet; `reference` | equipment outline with nozzles and process anchors | by equipment type | no | yes | planned |
| Insulation / tracing / jacketing conventions | line treatment | `connection` | annotation | ISO 10628-1:2014 (diagram structure); `reference` | line decoration derived from authored data, never a tag embedded in geometry | insulation / tracing | code values are project-specific | yes | planned |
| Nozzle designation | equipment annotation | `annotation` | annotation | not a graphical symbol | text beside a nozzle | — | yes | yes | planned (text, never geometry) |


## I&C / instrumentation concepts

| Reference concept | Semantic concept | Classification | Category | Standard evidence & verification | Representation strategy | Variants | Project-specific | MVP | Status |
|---|---|---|---|---|---|---|---|---|---|
| Local / field instrument | measurement point on a field-mounted instrument | `symbol` | instrument | **ISO 15519-2:2015** (intended correspondence, not human-verified); `candidate-alignment` | DeepPlant-authored project seed geometry: a plain instrument circle connected to the process by one functional connection line, with no letter code or tag embedded; one process tap anchor and no mandatory signal anchor, in [symbol-seed-geometry.md](symbol-seed-geometry.md) | none implemented; this is the reusable base graphic | no | yes | **implemented** (`instrument.local`) |
| Panel / central instrument | measurement point reported to the control system | `symbol` | instrument | ISO 15519-2:2015 (reference direction); `reference` | the same base circle with an internal additional graphic, resolved as a variant rather than a new symbol | panel / subsidiary control system | no | yes | planned |
| Instrument function letter codes | measurement / control function | `annotation` | annotation | ISO 15519-2:2015 (instrument identification); `reference` | text composed onto a base symbol; **never** one symbol definition per code such as PIT, TI, or FIC | process variables / control functions / modifiers | tag values are project-specific | yes | planned (text, never geometry) |
| Signal / instrument connection lines | signal connection | `connection` | signal | ISO 15519-2:2015 (connection conventions); `reference` | line convention separate from piping, attached through an anchor whose kind is `signal` on a composed instrument function, never on the reusable base graphic | electric / pneumatic / hydraulic | media conventions are project-specific | yes | planned |
| Measurement sensors and elements | measurement sensor | `symbol` | instrument | ISO 15519-2:2015 (measurement symbols); `reference` | small measurement graphic placed on the piping or equipment | by measured variable | no | yes | planned |
| Instrument with integrated display | instrument display | `composed-symbol` | instrument | ISO 15519-2:2015 (display indication); `reference` | base circle composed with the display indication | form 1 / form 2 | no | optional | planned (composition deferred) |
| Multifunction instrument | multiple functions in one housing | `composed-symbol` | instrument | ISO 15519-2:2015 (multifunction housing); `reference` | two base circles placed side by side inside one envelope | by function count | no | optional | planned (composition deferred) |
| DCS / SIS representation | control-system participation | `project-convention` | control system | company practice, not a standard library asset | project convention; never part of a base symbol | DCS / SIS | yes | yes | out of the base library |
| Interlock, trip and SIF numbering | safety function annotation | `project-convention` | annotation | company practice, not a standard library asset | project text and numbering | interlock / trip / SIF | yes | yes | out of the base library |
| Reference to a typical diagram | project typical reference | `composite-typical` | annotation | ISO 15519-2:2015 (typical references); `reference` | a reference marker pointing at a documented typical, not a copy of it | — | yes | yes | deferred |

## Project conventions (deliberately not a symbol library)

| Reference convention | Classification | Handling |
|---|---|---|
| Equipment / valve tag prefixes | `project-convention` | Tag text is composed by the project, never embedded in base symbol geometry. |
| Line designation rules | `project-convention` | Authoring/validation concern outside the symbol library. |
| Insulation, tracing and piping-class codes | `project-convention` | Values are authored data; symbol geometry only carries the decoration. |
| DCS / SIS conventions, interlock and trip numbering | `project-convention` | Company-specific; excluded from the `generic-iso` profile. |
| Composite project typicals | `composite-typical` | Resolution of a typical reference is deferred entirely. |


## Current implementation status

| Symbol | Classification | Profile | Asset provenance | Standard reference | Verification | Anchors (name → orientation, kind) |
|---|---|---|---|---|---|---|
| `valve.gate` | `symbol` | `generic-iso` | `deepplant-original`, AGPL-3.0-only | ISO 10628-2:2012 | `candidate-alignment` | `port_a` → west, process; `port_b` → east, process |
| `pump.centrifugal` | `symbol` | `generic-iso` | `deepplant-original`, AGPL-3.0-only | ISO 10628-2:2012 | `candidate-alignment` | `suction` → west, process; `discharge` → east, process |
| `instrument.local` | `symbol` | `generic-iso` | `deepplant-original`, AGPL-3.0-only | ISO 15519-2:2015 | `candidate-alignment` | `tap` → south, process |

Everything else above is `planned`, `deferred`, or `out of the base library`. No
concept outside these three is implemented, no standards relationship is
`human-verified`, and the three implemented geometries are DeepPlant-authored
project seed geometry ([symbol-seed-geometry.md](symbol-seed-geometry.md)), not
derived from a standard's artwork or from a company drawing. They are recorded at
`candidate-alignment` because the project intends them to correspond to the named
ISO family, with no human check claimed. Because `generic-iso` *means* that
intended correspondence, a definition in that profile must record at least one
relationship at `candidate-alignment` or `human-verified`; a bare `reference`
cannot carry the profile ([symbol-library.md](symbol-library.md)).

## Unresolved questions

- Whether these three DeepPlant-authored representations are close enough to the
  standards they name is open: the symbols are recorded at `candidate-alignment`,
  and any promotion to `human-verified` requires a human comparison against an
  authorized copy, recorded with the standard, the symbol, the date, and the
  verifier ([standards.md](../workflow/standards.md)). `candidate-alignment`
  itself requires no human check.
- A permitted or human-recorded locator for each representation has not been
  recorded, so `StandardsReference.locator`, `.name`, `.verified_by`, and
  `.verified_on` stay unset; human verification can add that evidence later.
- The ISO 10628-1:2014 diagram-structure rules relevant to line treatment
  (insulation, tracing, line-class breaks) are recorded only as a reference
  direction; no line-treatment representation is implemented.
- ISO 15519-2:2015 and the ISO 14617 series overlap. Which document DeepPlant
  cites as the primary reference for measurement and instrument symbols is
  unresolved.
- The pump representation currently treats suction and discharge as its only
  process anchors. Whether a driver/energy anchor belongs on the pump symbol or
  on a separate composed symbol is unresolved.
- Whether generated symbol SVG should also carry the hidden anchor slots used by
  the existing process symbol-pack contract is unresolved; in this slice anchors
  remain definition data only.
- Restricted standard material is never committed to the repository and is never
  provided to AI tooling; the identifiers recorded here should be confirmed
  against the official ISO catalogue by a human before any compliance-sensitive
  claim, and DeepPlant never claims compliance from visual similarity
  ([standards.md](../workflow/standards.md)).

## Related

- [symbol-library.md](symbol-library.md) — the machine-rendered symbol library
  contract and the implemented definitions.
- [symbol-seed-geometry.md](symbol-seed-geometry.md) — the project-owned spec the
  three implemented geometries are authored from.
- [svg-symbols.md](svg-symbols.md) — the separate, DeepPlant-original process
  symbol-pack and anchor contract.
- [../workflow/standards.md](../workflow/standards.md) and
  [standards-registry.md](standards-registry.md) — standards usage policy and
  the project reference set.
- [../research/mvp-symbol-core-selection.md](../research/mvp-symbol-core-selection.md)
  — the evidence behind the MVP Core selection named above.
- [../research/standards-licensing-evidence.md](../research/standards-licensing-evidence.md)
  — the source and licence investigation behind those rules.

