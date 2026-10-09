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
  - operator-selected MVP reference directory (private; neutral identifiers only)
  - DeepPlant MVP drawing support profile v0.1 (operator-bundled, status proposed)
superseded_by: null
---

# MVP Symbol Coverage Matrix

> **Question this document answers:** which engineering concepts must the
> DeepPlant MVP be able to draw, how is each one meant to be represented, and how
> far has each one actually been implemented?

This is the Phase 0 coverage analysis behind
[Issue #119](https://github.com/Semtexcz/DeepPlant/issues/119). It is the
canonical per-concept inventory of the final MVP Core and its current support
state, not a rendering contract: the rendering contract for implemented symbols
is [symbol-library.md](symbol-library.md).

## MVP Core selection

Issue #119 scopes the MVP to a deliberate vocabulary subset, the **MVP Core**: the
concepts the selected MVP reference content must be able to represent. The
operator-selected MVP reference directory is the **authoritative requirements
boundary**; the bundled MVP drawing profile v0.1 and this matrix are
interpretation, classification, and implementation-status aids, and neither
overrides it.

Ownership splits cleanly between the two documents:

```text
research/mvp-symbol-core-selection.md   evidence, derivation and reasoning
                                        (why each concept is in the Core)
this matrix                             canonical current Core coverage inventory
                                        and per-concept status
                                        (what the Core requires and how far it is supported)
```

Every final Core requirement therefore has its own canonical entry here, and the
evidence document does not own a current rule: it explains why an entry is
required, and this matrix states that it is required and what its current support
is. Core entry identifiers (`A…`, `B…`, `C…`, `D…`) are shared between the two
documents, so the Core reconciles mechanically.

That evidence document was corrected on 2026-10-09 (its first revision derived the
Core from the profile and demoted operator-selected content to "usage evidence
only"), and refined in the same change: a **required engineering concept family**
is no longer reported as one resolved `SymbolDefinition` while its graphical
identity is still undecided. Under that derivation the Core is:

```text
40 Core requirement entries
   17 base graphical requirement families
    5 composed representations
    7 connections
   11 annotations
13                   project conventions               (tracked outside the Core)
 6                   semantic gaps                     (tracked outside the Core)
12                   representation-design questions   (tracked outside the Core)

capability-specific implementation state
  base graphical requirements   17 families
    stable identities resolved  14
      implemented                3   (valve.gate, pump.centrifugal, instrument.local)
      resolved but missing      11
    identity / granularity unresolved  3
  composed        0 implemented / 5 missing
  connections     1 implemented / 1 partial / 5 missing
  annotations     1 implemented / 1 partial / 9 missing
```

Arithmetic: `17 = 14 + 3`; `14 = 3 + 11`; `40 = 17 + 5 + 7 + 11`.

Two earlier summaries are withdrawn. "28 Core entries / 3 implemented / 25
remaining" counted project conventions as a partition while excluding them from
the arithmetic, and reported annotations, connections, and compositions as if they
were remaining symbol definitions. "41 Core entries / 18 base symbols / 3
implemented / 15 missing" counted a standalone control-valve *body* identity the
selected evidence does not establish, and reported three identity-unresolved
requirement families as exact missing `SymbolDefinition`s (see
[Requirement status and stable identity](#requirement-status-and-stable-identity)).

Two rules follow from the selection, and both are already this matrix's rules:

- one representation per engineering concept — never one symbol per project code
  (`PI`, `PIT`, `TI`, `FIC`, `LIC` stay text composed onto a base graphic), and
  never one symbol per repeated instance;
- company tag prefixes, fluid and insulation codes, line-designation rules,
  DCS/SIS practice, and corporate title blocks are `project-convention`, never
  base-library assets.

The `Requirement` column in the tables below follows the corrected derivation:
`required` means required by the selected MVP reference content, `optional` means
allowed but not needed to preserve the selected information, and `not required`
means not needed for the selected MVP information, with the reason recorded in the
evidence document. Widening the Core is an operator selection decision, not a
symbol implementation and not a repository preference.

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

## Requirement status and stable identity

Two independent questions are recorded for every Core entry:

```text
Requirement      is this engineering / graphical capability in the MVP Core?
Stable identity  is there one decided graphical identity (SymbolDefinition) for it?
```

A base graphical requirement is therefore classified by its identity state:

| Stable identity | Meaning | How it is reported |
|---|---|---|
| `resolved` | the project has one stable graphical identity for the concept | `implemented`, or `missing base SymbolDefinition` |
| `unresolved` | the identity, or its granularity, is still a representation-design question | `representation identity unresolved — design decision required before SymbolDefinition implementation` |

`missing SymbolDefinition` is only ever used for a **resolved** identity. An
unresolved family is a required capability, not an exact missing symbol: three of
the base requirement families (heat-transfer equipment, vessel / tank / drum,
measurement sensor / primary element) and the control-valve composition's body are
in that state. A requirement family may also be `required` while its identity is
resolved, and a shared graphical primitive never by itself creates a shared stable
identity.

## Reference material handling

The operator-selected MVP reference bundle — one PFD sheet, two P&ID sheets, and
the project's piping-elements and instrumentation-and-control notation legends,
summarised by the operator-bundled *DeepPlant MVP drawing support profile v0.1* —
is private project material, and it is the authoritative MVP requirements
boundary. It answers **what must be representable** and **how the selected project
draws it**; it is never a source of geometry. No symbol is copied, vectorised,
traced, or measured from it, and no title block, tag, note, document identifier,
drawing title, or symbol sheet is reproduced
([standards.md](../workflow/standards.md), ADR-0007). It is referenced only by
neutral role identifiers ([../research/mvp-symbol-core-selection.md](../research/mvp-symbol-core-selection.md)).

The companies' own conventions (tag prefixes, line designation, DCS/SIS
practice, interlock numbering) are recorded here as `project-convention` so they
cannot be mistaken for a standard base library.

## MVP Core coverage

Canonical per-concept inventory of the final MVP Core. Every entry is one
requirement from the selected MVP reference content, and the identifiers match the
[evidence document](../research/mvp-symbol-core-selection.md). `Requirement` and
`Stable identity` are separate states (see
[Requirement status and stable identity](#requirement-status-and-stable-identity)).

### 1. Base graphical requirements (17 families)

| # | Concept | Context | Classification | Requirement | Stable identity | Standards evidence & verification | Current support & representation | Gap type |
|---|---|---|---|---|---|---|---|---|
| A01 | Filter | pfd + pid | `symbol` | required | resolved | `generic-iso`; no standards relationship recorded yet; `reference` | missing; equipment outline with process anchors | missing base SymbolDefinition |
| A02 | Compressor | pfd | `symbol` | required | resolved | `generic-iso`; no standards relationship recorded yet; `reference` | missing; equipment outline with process anchors | missing base SymbolDefinition |
| A03 | Heat-transfer equipment — heater, superheater, preheater, evaporator, exchanger (requirement family) | pfd + pid | `symbol` | required | **unresolved** | `generic-iso`; no standards relationship recorded yet; `reference` | missing; a heat-transfer duty family must be representable, and one reusable identity vs several duty / equipment identities is not decided (G11) | representation identity unresolved — design decision required before SymbolDefinition implementation |
| A04 | Mixer (two or more process inlets) | pfd | `symbol` | required | resolved | `generic-iso`; no standards relationship recorded yet; `reference` | missing; equipment outline with multiple process anchors | missing base SymbolDefinition |
| A05 | Reactor / burner | pfd | `symbol` | required | resolved | `generic-iso`; no standards relationship recorded yet; `reference` | missing; equipment outline with anchored connections | missing base SymbolDefinition |
| A06 | Pump | pfd + pid | `symbol` | required | resolved | **ISO 10628-2:2012** (intended correspondence, not human-verified); `candidate-alignment` | **implemented** (`pump.centrifugal`, `diagram_types = ("pfd", "pid")`); DeepPlant-authored project seed geometry ([symbol-seed-geometry.md](symbol-seed-geometry.md)) | — (geometry review before any notation-profile migration, per #127) |
| A07 | Vessel / tank / drum with nozzles (requirement family) | pfd + pid | `symbol` | required | **unresolved** | `generic-iso`; no standards relationship recorded yet; `reference` | missing; a containment outline with nozzles, and one reusable identity vs separate vessel / tank / drum / column identities is not decided (G2) | representation identity unresolved — design decision required before SymbolDefinition implementation |
| A08 | Gate valve | pid | `symbol` | required | resolved | **ISO 10628-2:2012** (intended correspondence, not human-verified); `candidate-alignment` | **implemented** (`valve.gate`); DeepPlant-authored project seed geometry, with neutral `port_a` / `port_b` process anchors that embed no flow semantics | — (external recognizability and exact geometry unresolved, per #127) |

| A09 | Globe valve | pid | `symbol` | required | resolved | ISO 10628-2:2012 (reference direction); `reference` | missing; valve body with the variant's internal mark | missing base SymbolDefinition |
| A10 | Check valve | pid | `symbol` | required | resolved | ISO 10628-2:2012 (reference direction); `reference` | missing; valve body with the variant's flow mark | missing base SymbolDefinition |
| A11 | Ball valve | pid | `symbol` | required | resolved | ISO 10628-2:2012 (reference direction); `reference` | missing; valve body with the variant's internal mark | missing base SymbolDefinition |
| A12 | Three-way valve | pid | `symbol` | required | resolved | ISO 10628-2:2012 (reference direction); `reference` | missing; three-port valve body | missing base SymbolDefinition |
| A14 | Safety / relief valve (spring-loaded indication) | pid | `symbol` | required | resolved | ISO 10628-2:2012 (reference direction); `reference` | missing; valve body with a spring-loaded indication | missing base SymbolDefinition |
| A15 | Restriction orifice | pid | `symbol` | required | resolved | ISO 10628-2:2012 (reference direction); `reference` | missing; small inline graphic on the piping axis | missing base SymbolDefinition |
| A16 | Reducer (concentric / eccentric) | pid | `symbol` | required | resolved | ISO 10628-2:2012 (reference direction); `reference` | missing; inline fitting on the piping axis | missing base SymbolDefinition |
| A17 | Instrument base graphic, field-mounted | pid | `symbol` | required | resolved | **ISO 15519-2:2015** (intended correspondence, not human-verified); `candidate-alignment` | **implemented** (`instrument.local`); DeepPlant-authored project seed geometry, with no function letters, tag, or mandatory signal anchor embedded | — (profile composition unresolved, #124) |
| A18 | Measurement sensor / primary element (inline on the process) (requirement family) | pid | `symbol` | required | **unresolved** | ISO 15519-2:2015 (measurement symbols); `reference` | missing; a small measurement graphic, and one reusable identity vs one graphic per measured variable is not decided (G4) | representation identity unresolved — design decision required before SymbolDefinition implementation |

The base-symbol identifier `A13` is retired. Earlier revisions counted a
standalone control-valve *body* identity here; the selected evidence requires a
**control valve** — the composed representation `B01` — and does not establish a
stable standalone identity named "control valve body", so the body requirement is
tracked with `B01` instead of as a resolved base symbol. Nothing is counted twice.

### 2. Composed representations (5)

| # | Concept | Context | Classification | Requirement | Current support | Gap type |
|---|---|---|---|---|---|---|
| B01 | Control valve with actuator (body composed with an actuator graphic) | pfd + pid | `composed-symbol` | required | missing; the body component is required, but the representation model that gives it a stable identity is not decided (G12) | composition gap; body identity a representation-design question |
| B02 | On/off actuated valve with position indication | pid | `composed-symbol` | required | missing | composition gap |
| B03 | Instrument function composition (base graphic + function letter code + loop designation) | pfd + pid | `composed-symbol` | required | missing (the base graphic exists; the letter-code and loop-designation annotations do not) | composition gap |
| B04 | Control-system instrument variant (panel / shared display / control-system participation) | pid | `composed-symbol` | required | missing | composition gap |
| B05 | Safety-system instrument variant (instrument marked as part of the safety system) | pid | `composed-symbol` | required | missing | composition gap (the referenced logic is semantic gap F3) |


### 3. Connections (7)

| # | Concept | Context | Classification | Requirement | Current support | Gap type |
|---|---|---|---|---|---|---|
| C01 | Directional process stream | pfd | `connection` | required | implemented — drawn by the process renderer as output, not as a `SymbolDefinition` | — |
| C02 | Process boundary connector (battery limit, labelled) | pfd + pid | `annotation` (boundary) | required | missing | connection-rendering gap (marker plus label, never equipment geometry) |
| C03 | Off-page connector (sheet-to-sheet continuation with a reference) | pfd + pid | `connection` | required | missing | connection-rendering gap |
| C04 | Piping line — orthogonal routing, branch / junction, direction indication | pid | `connection` | required | missing (routing exists for process streams only) | connection-rendering gap |
| C05 | Instrument process connection (functional tap) | pid | `connection` | required | partial — the `tap` anchor exists on `instrument.local`; the line convention does not | connection-rendering gap |
| C06 | Instrument signal line, electric | pid | `connection` | required | missing (signal lines must not become `Connection`) | connection-rendering gap |
| C07 | Line treatment — insulation, heating, tracing, as authored data | pid | `connection` (line treatment) | required as data; graphical decoration optional | missing (no authored carrier) | semantic-model gap (F5) |

### 4. Annotations (11)

| # | Concept | Context | Classification | Requirement | Current support | Gap type |
|---|---|---|---|---|---|---|
| D01 | Stream number label | pfd | `annotation` | required | implemented — the renderer's label layer draws the process stream id | — |
| D02 | Stream property / composition data (medium, phase, flows, temperature, pressure, density, molecular weight, composition, duty) | pfd + pid | `annotation` | required as data; an automatic drawing table is optional | missing | semantic-model gap (F1) |
| D03 | Equipment tag / name label (with the project equipment-code prefix) | pfd + pid | `annotation` | required | partial — step id and name labels are drawn for process steps only | annotation gap |
| D04 | Duty / rating / set-point annotation (heat duty, relief set pressure) | pfd + pid | `annotation` | required | missing | semantic-model gap (F6) |
| D05 | Nozzle designation | pid | `annotation` | required | missing | annotation gap |
| D06 | Line tag (medium + sequence + nominal size + piping class) | pfd + pid | `annotation` | required | missing (values are project conventions) | annotation gap |
| D07 | Instrument loop designation (function letters + loop number, with plant / location code) | pid | `annotation` | required | missing | semantic-model gap (F2) |
| D08 | Instrument alarm / limit annotation (high, high-high, low, low-low) | pid | `annotation` | required | missing | annotation gap |
| D09 | Fail-state annotation (fail-closed / fail-open / fail-lock / normally-closed) | pfd + pid | `annotation` | required | missing | annotation gap |
| D10 | Interlock / trip / permissive reference annotation | pid | `annotation` | required | missing | annotation gap plus semantic-model gap (F3) |
| D11 | Drawing note / general note (authored text annotation) | pfd + pid | `annotation` | required | missing | semantic-model gap (F4) |

## Outside the Core (retained concept inventory)

Retained so that broader reference-set vocabulary stays traceable. None of these
is an MVP Core requirement, and none is counted in the Core totals above.

| Concept | Classification | Why it is outside the Core |
|---|---|---|
| Automatic stream property table | `annotation` | The stream property *data* is required (D02); rendering it as an automatic drawing table is not. |
| Multifunction / multivariable instrument | `composed-symbol` | The selected content reports single-function loops. |
| Specialty valves defined by the piping legend but unused by the selected drawings (butterfly, plug, needle, injection, angle, stop-check, automatic-recirculating check, backflow preventer, vacuum breaker, breath valve, automatic vent valve, valve with built-in bypass) | `symbol` | Defined by the project notation legend only; no selected drawing needs them represented. |
| Piping fittings and accessories defined by the piping legend but unused by the selected drawings (spectacle blind / blank, strainer, cap and plug, sight glass, funnel / drain, steam trap, flame arrestor, flexible hose, expansion joint, mechanical coupling, sprayer, hose connection, silencer / damper) | `symbol` | Same reason: legend vocabulary, not selected drawing content. |
| Reference to a typical diagram | `composite-typical` | Not evidenced in the selected MVP content; tracked as a project convention. |
| Detailed electrical / motor-control representation | — | The selected drawings show actuators, position indications and fail states, but no detailed electrical schematic content. |
| Voting indication and trip / permissive diamond markers | `annotation` | Named by the bundled profile for the complexity gate but not evidenced in the inspected content; recorded as a semantic-gap candidate, not a Core requirement. |

## Project conventions (13, deliberately not a symbol library)

Company or project practice, tracked outside the Core. These values stay authored
data, and base-symbol geometry must not embed them.

| # | Convention | Classification | Handling |
|---|---|---|---|
| E01 | Equipment and valve tag prefixes, equipment-code letters | `project-convention` | Tag text is composed by the project, never embedded in base geometry. |
| E02 | Fluid / medium code list | `project-convention` | Values are authored data; the code list is not DeepPlant vocabulary. |
| E03 | Line-number and line-designation rules | `project-convention` | Authoring and validation concern outside the symbol library. |
| E04 | Piping-class and nominal-size designation | `project-convention` | Authored data, validated per project practice. |
| E05 | Insulation, heating and tracing codes | `project-convention` | Authored data; geometry may later carry only decoration. |
| E06 | Nozzle-role letter designations | `project-convention` | Project text; the nozzle annotation itself is a Core entry (D05). |
| E07 | Instrument letter-code system (measured variable, succeeding functions, modifiers) | `project-convention` | Drives the annotation composed onto the base graphic (B03); the code list is project notation. |
| E08 | Instrument loop and plant / location numbering | `project-convention` | Project numbering; the designation itself is a Core entry (D07). |
| E09 | Alarm, trip, permissive, safety-interlock and trip-group numbering systems | `project-convention` | Company-specific; excluded from the base library. |
| E10 | Control-system (DCS) and safety-system (SIS) participation, including the software-link convention | `project-convention` | Project notation; the instrument *variant* is a Core entry (B04, B05), the convention is not. |
| E11 | Actuator and control-system marking conventions (mounted location, fail position, positioner, solenoid, motor) | `project-convention` | Project notation layered on Core composition (B01, B02) and annotation (D09). |
| E12 | Corporate title block, revision table, drawing frame, equipment data table | `project-convention` | Document production; out of scope as symbol vocabulary. |
| E13 | Composite project typicals | `composite-typical` | Resolution of a typical reference is deferred; the reference marker is not a copy of the typical. |


## Current implementation status

| Symbol | Classification | Profile | Asset provenance | Standard reference | Verification | Anchors (name → orientation, kind) |
|---|---|---|---|---|---|---|
| `valve.gate` | `symbol` | `generic-iso` | `deepplant-original`, AGPL-3.0-only | ISO 10628-2:2012 | `candidate-alignment` | `port_a` → west, process; `port_b` → east, process |
| `pump.centrifugal` | `symbol` | `generic-iso` | `deepplant-original`, AGPL-3.0-only | ISO 10628-2:2012 | `candidate-alignment` | `suction` → west, process; `discharge` → east, process |
| `instrument.local` | `symbol` | `generic-iso` | `deepplant-original`, AGPL-3.0-only | ISO 15519-2:2015 | `candidate-alignment` | `tap` → south, process |

Everything else is reported per capability in
[MVP Core coverage](#mvp-core-coverage): each Core entry records its own support
state and gap type, and no identity-unresolved requirement family is counted as an
exact missing `SymbolDefinition`. See also the
[evidence document](../research/mvp-symbol-core-selection.md). No
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
- Whether each identity-unresolved requirement family — heat-transfer equipment
  (A03), vessel / tank / drum (A07), measurement sensor / primary element (A18) —
  maps to one stable `SymbolDefinition` or to several, and which representation
  model gives the control-valve body a stable identity (B01), are unresolved; the
  specific questions are recorded as representation-design questions G2, G4, G11
  and G12 in the [evidence document](../research/mvp-symbol-core-selection.md).
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

