---
type: evidence
status: active
canonical_for:
  - mvp-core-graphical-vocabulary-selection
read_when:
  - symbol-asset-work
  - feature-planning
  - mvp-scope-change
update_when:
  - new-source-inspection
  - mvp-symbol-scope-change
  - symbol-selection-change
depends_on:
  - docs/dev/reference/mvp-symbol-coverage.md
  - docs/dev/reference/symbol-library.md
  - docs/dev/reference/symbol-seed-geometry.md
  - docs/dev/research/notation-profile-classification.md
  - docs/dev/workflow/standards.md
decision:
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0007-standards-and-symbol-provenance.md
  - docs/dev/decisions/ADR-0017-machine-rendered-symbol-definitions.md
evidence:
  - operator-selected MVP reference directory (private; neutral identifiers only)
  - DeepPlant MVP drawing support profile v0.1 (operator-bundled, status proposed)
superseded_by: null
---

# MVP Core graphical vocabulary selection

## Outcome card

- **Question investigated:** which concrete graphical vocabulary — base symbols,
  composed representations, connections, and annotations — must the MVP be able to
  represent, given the reference set the operator selected as the MVP
  product-requirements boundary?
- **Status:** closed evidence, **corrected**. The first revision of this document
  had the scope authority reversed; this revision re-derives the MVP Core from the
  operator-selected reference set itself and supersedes that revision's 28-entry
  result, its partition counts, and its remainder metric.
- **Inspection scope and date:** the operator-selected MVP reference directory
  (three drawing sheets, two notation legend sheets, one duplicate legend copy,
  and the operator-bundled MVP drawing profile v0.1) plus the DeepPlant-authored
  repository material listed under [Sources](#sources). Re-inspected and
  recomputed **2026-10-09**; the three drawing sheets were then re-inspected as
  **rendered graphics**, sheet by sheet at tile resolution and with targeted
  crops of the symbol forms in question (**2026-10-10**), so symbol
  form, marker shape, and signal-line style were inspected directly rather than
  inferred, and no geometry was measured, traced, or copied. No restricted
  ISO/ISA/IEC content was inspected, and no standards locator, figure, table, or
  item number is recorded.
- **Conclusions:**
  - The operator-selected reference directory is the **authoritative requirements
    boundary**. The bundled profile and the repository coverage matrix are
    interpretation, classification, and implementation-status aids: they may
    confirm, classify, and explain a requirement, but they never silently remove
    engineering content the operator placed inside that boundary.
  - Re-derived from that boundary, the MVP Core is **40 requirement entries**:
    **17** base graphical requirement families, **5** composed representations,
    **6** connections, **11** annotations, and **1** classification-unresolved
    capability (the labelled process boundary connector, whose family is question
    G10). Project conventions (13), semantic gaps (6), and representation-design
    questions (12) are tracked **outside** the Core count.
  - Base requirement families separate two states: **13** carry a resolved stable
    graphical identity (4 implemented, 9 resolved but missing), and **4** carry an
    unresolved identity / granularity (filter, heat-transfer equipment, vessel /
    tank / drum, measurement sensor / primary element), so those four are not
    counted as exact missing `SymbolDefinition`s. Composed representations 0
    implemented / 5 missing; connections 1 implemented / 1 partial / 4 missing;
    annotations 1 implemented / 1 partial / 9 missing; classification-unresolved
    capability 1. The earlier single "25 remaining" metric is withdrawn, because it
    mixed capabilities that are not SymbolDefinitions at all; the earlier "18 base
    symbols / 15 missing" count is withdrawn too, because it claimed an unresolved
    control-valve body identity and three unresolved families as exact symbols.
  - A concept the selected content needs in **both** the PFD and the P&ID is not
    thereby one resolved `SymbolDefinition`: whether one cross-context representation
    serves both contexts, or each context has its own form, is question G1. Only
    `pump.centrifugal` already answers it (`diagram_types = ("pfd", "pid")`), so the
    filter, heat-transfer-equipment and vessel / tank / drum families stay unresolved
    alongside their granularity questions.
  - Everything the profile called nice-to-have, was silent about, or excluded
    without reference to the selected *drawing* content — storage, pumping,
    filter/strainer, heat exchanger, control-system instruments, ball and
    safety valves, alarm/fail-state/interlock annotation, general notes, and the
    complexity-gate vocabulary — is re-derived here as **required**, **optional**,
    or **not required**, with the selected evidence or the recorded reason stated.
  - The three `generic-iso` implementations keep the classification given them by
    [notation-profile-classification.md](notation-profile-classification.md):
    `valve.gate` and `instrument.local` are `deepplant-default` candidates;
    `pump.centrifugal` stays `REVIEW_BEFORE_MIGRATION / INSUFFICIENT_EVIDENCE`.
    **This document changes neither the profile assignment nor the geometry.**
  - The **graphics audit of the three selected drawing sheets confirms occurrence
    and changes nothing else**: the Core stays **40** requirement entries, no row's
    requirement, stable identity, profile, or gap type moves, and the two
    text-layer evidence gaps recorded in the first revision (purely graphical
    occurrences; voting and trip markers) are corrected rather than carried
    ([Graphics audit of the selected sheets](#graphics-audit-of-the-selected-sheets)).
- **Resulting decision:** none in production code. The selection is scope evidence
  for the [coverage matrix](../reference/mvp-symbol-coverage.md), which names the
  MVP Core explicitly.
- **Conditions for revisiting:** the operator widens or narrows the selected
  reference directory; a recorded discrepancy or scope question below is
  answered; the bundled profile is approved or revised; the active milestone
  changes; or a Core concept's implementation changes.

**This document owns no current rule and implements no symbol.** It records what
was selected and why. The rendering contract stays
[symbol-library.md](../reference/symbol-library.md); per-concept status stays
[mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md).

## Research question

> Which concrete graphical vocabulary must the MVP be able to draw, and which
> parts of the inspected reference set are deliberately outside it?

This is the scoping half of Issue #119. This document derives the selection and
records its evidence; the canonical per-concept Core inventory and its
implementation status live in [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md).
The matrix states *what the Core requires and how far each entry is supported*;
this document records *why each entry is required*.

```text
operator-selected reference directory  the requirements boundary      (authoritative)
MVP drawing profile v0.1               interpretation / classification aid
MVP Core (this document)               the minimal reusable vocabulary that represents it
coverage matrix                        per-concept classification and implementation status
catalogue.py                           the representations implemented so far
```

## Scope authority (corrected)

The inputs, and their deliberately unequal authority:

| Input | Authority | Used for |
|---|---|---|
| Operator-selected MVP reference directory (three drawing sheets plus the project notation legends) | **authoritative requirements boundary** | what the MVP must be able to represent |
| *DeepPlant MVP drawing support profile v0.1* (bundled in that directory, status `proposed`) | **classification and interpretation aid** | naming the subset the operator proposed, its required / nice-to-have / explicitly excluded vocabulary, and explaining why a concept matters |
| Repository coverage matrix and symbol contract | classification vocabulary and implementation status | each concept's classification, its current support, and the rendering contract |
| Implemented catalogue (read-only) | current capability | what exists today |

The profile may classify, explain, and propose. It must not override the operator's
selection: where the two disagree, the discrepancy is recorded (see
[Recorded discrepancies and scope questions](#recorded-discrepancies-and-scope-questions)).

### Derivation rule

```text
A concept belongs to the MVP requirements when:
    it occurs in the operator-selected reference set
AND
    DeepPlant must represent it to preserve the intended engineering
    information of that selected MVP content.
```

It is minimized only at the **reusable representation level**:

```text
PIT, PIC, TI, FIC   ->  one instrument base graphic
                        + function-letter composition
                        + the relevant connection capabilities
                    !=  four base symbols
```

Repeated use of one concept does not multiply the vocabulary either: the selected
content contains many valves, many instruments, several parallel equipment items
and repeated control loops, and each of those deduplicates to one representation
plus, where needed, composition, annotation, or project data.

The rule the first revision applied is **withdrawn**:

```text
withdrawn   profile silent + selected set uses concept   ->  excluded
corrected   profile silent + selected set uses concept   ->  requirement,
                                                             or a recorded gap
```

How the profile's own statements are used:

```text
profile says "required"      ->  requirement (confirms the selected content)
profile says "nice-to-have"  ->  requirement when the selected drawings need it;
                                 otherwise optional for the selected information
profile is silent            ->  requirement, or a recorded evidence / semantic /
                                 graphical / composition gap — never a silent exclusion
profile says "out of scope"  ->  a recorded reason for "not required", valid only
                                 when the selected drawing content itself does not
                                 need the concept represented
```

## Recorded discrepancies and scope questions

- **Complexity-gate sheet.** The bundled profile designates the second P&ID sheet
  as the post-MVP complexity gate ("not part of MVP acceptance"). That sheet sits
  inside the directory the operator selected as the MVP requirements boundary, so
  its content is treated here as *inside* the boundary, and the profile's
  designation is recorded as a discrepancy for the operator to resolve. This
  document does not resolve it by excluding the sheet.
- **Legend vocabulary.** The selected bundles contain the project's notation
  legends, which define a wider vocabulary than the selected drawings use. This
  selection treats a legend definition that no selected drawing uses as
  *not required for the selected MVP information*, and records it explicitly (see
  [Not required for the selected MVP information](#not-required-for-the-selected-mvp-information))
  so that nothing is dropped silently. If the operator intends the selected
  **legend vocabulary itself** to be MVP-required, the Core widens by that
  recorded list; that is an operator decision, not a repository one.
- **Unused "supported in the data model" claim.** The profile states that detailed
  stream properties (density, volumetric flow, composition, molecular weight) are
  supported in the data model. The current `ProcessStream` carries only `id`,
  `name`, `source`, and `target` ([contracts/process-model.md](../../contracts/process-model.md)),
  and the physical layer records no unit/quantity typing yet, so no such carrier
  exists today. That discrepancy is recorded as a semantic gap rather than
  accepted as a profile fact.
- **Profile status.** The profile is `proposed`, not approved. That remains useful
  context, and it is **no longer** a prerequisite for recognizing requirements the
  operator already selected.

## Reference material handling

The reference set is a private company bundle, selected by the operator as the MVP
requirements boundary. Its drawings state requirements and supply qualitative
notation/form evidence; they are **never a source of copied or measured geometry**,
and they are not redistributed:

- Nothing from it is committed, quoted, traced, vectorised, or measured. No
  symbol artwork, layout, title block, revision table, equipment data block, note
  text, tag value, line-tag value, or symbol-sheet item is reproduced here or in
  the repository.
- The selected material is referenced **only by neutral role identifiers** (see
  [Inspected evidence](#inspected-evidence)). No source filename, document number,
  drawing title, private path, title-block value, customer or project identifier,
  tag, line number, or copied legend text is recorded.
- Only **concept-level vocabulary** is recorded: generic engineering concepts
  ("gate valve", "centrifugal pump", "off-page connector") that the repository
  already names. The sheets name standard families; **no standard locator, figure
  reference, table number, or item number observed on them is recorded**, because
  only a permitted source or a recorded human verification may supply that
  ([standards.md](../workflow/standards.md), ADR-0007).
- The implemented geometries remain DeepPlant-authored project seed geometry
  ([symbol-seed-geometry.md](../reference/symbol-seed-geometry.md)). The bundle
  supplies qualitative notation/form evidence only: no coordinate, proportion,
  path, pixel, dimension, or piece of artwork is measured, traced, vectorised, or
  copied from it, before or after this inspection, and no normalized seed
  coordinate is a derivative copy of its artwork.

```text
used as      the requirements boundary (which engineering concepts must the MVP represent?)
             and qualitative notation/form evidence (how the selected project depicts
             them, and which linework is intrinsic glyph versus connection versus
             annotation)
not used as  copied or measured geometry, locator, naming, layout, or compliance evidence
```

## Inspected evidence

Seven PDF pages across three documents, plus one bundled profile document. Listed
by neutral role, not by content.

| Neutral identifier | What it is | Role in this evidence |
|---|---|---|
| MVP PFD reference A | one PFD sheet | process-side requirements |
| MVP P&ID reference A | one P&ID sheet | physical and instrumentation requirements |
| MVP P&ID reference B | one P&ID sheet (the sheet the bundled profile designates as the complexity gate) | richer physical and instrumentation requirements |
| Supporting P&ID legend A | the project's piping-elements notation legend | valve/fitting vocabulary and piping, line-number and insulation conventions |
| Supporting P&ID legend B | the project's instrumentation-and-control notation legend | instrument, signal-line, actuator and letter-code notation |
| Duplicate legend copy | the same two legend sheets appear again in the second bundle in the directory | counted **once**: the two copies' inspected text layers are identical, so they are duplicate copies, not a distinct revision |
| MVP drawing profile v0.1 | the operator-bundled profile document | classification and interpretation aid only |

The sheets also carry project document apparatus (revision tables, title blocks,
equipment data tables, connector lists). It was inspected only to classify it as
project convention; none of it is recorded.

Read-only inspection also covered
[mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md), [symbol-library.md](../reference/symbol-library.md),
[symbol-seed-geometry.md](../reference/symbol-seed-geometry.md),
[notation-profile-classification.md](notation-profile-classification.md),
[catalogue.py](../../../src/deepplant/symbols/catalogue.py),
[profiles.py](../../../src/deepplant/symbols/profiles.py), and
[contracts/process-model.md](../../contracts/process-model.md) to confirm the
implemented definitions, their `notation_profile` and `diagram_types`, the
classification vocabulary, and the current model's stream contract.

## Observed reference-set vocabulary (concept level)

Recorded so the Core can be read against the selected content. This is a
*superset* of the Core: nothing here is added to the Core by being observed, and
nothing here is removed from consideration silently. Each family below was also
located in the rendered sheets, drawings and legends alike, so the selection is
not text-layer-only
([Graphics audit of the selected sheets](#graphics-audit-of-the-selected-sheets)).

| Capability class | Observed in the selected drawing sheets (concept level) |
|---|---|
| PFD process steps | filtration; compression; heat exchange in several duties (heating, superheating, preheating, evaporation); mixing; reaction / burning; pumping; hold-up / storage; a vessel or drum item |
| P&ID equipment | storage tank with lettered nozzles; centrifugal pumps (duty and stand-by instances); heat exchangers / evaporators; filters; vessels and drums with internals |
| P&ID inline components | gate, globe, check, ball, three-way and control valves; restriction orifices; spring-loaded safety / relief valves; reducers; flanged joints |
| Instrumentation | flow, level, pressure, differential-pressure and temperature measurement with indicator / transmitter / controller / element functions; locally mounted, panel-mounted and safety-system instruments; alarms (high, high-high, low, low-low), set points; interlocks |
| Connections | directional process streams; battery-limit boundaries; off-page / continuation connectors; routed piping with branches; functional instrument taps; electric signal lines |
| Annotations | stream numbers and a stream property / composition table; equipment tags and names; nozzle designations; line tags; instrument loop designations; alarm and fail-state annotations; drawing notes |
| Project notation defined by the legends | valve, fitting, actuator, instrument and signal-line vocabulary; the instrument letter-code system; fluid and equipment code lists; line-designation rules; insulation and heating codes; safety-interlock and trip numbering systems; title block and revision table |

Findings that matter for scoping:

```text
1. the selected drawing content is wider than the bundled profile's "required"
   list: storage, pumping, filters, exchangers, ball and safety valves,
   control-system instruments, alarms, fail-state and interlock annotation, and
   notes all occur in the selected drawing content
2. the selected content also contains the complexity-gate sheet's richer vocabulary
3. the legends define a vocabulary wider than any selected drawing sheet uses
4. tag, code, numbering and layout data in the selected content is project-owned
   and must never be embedded in symbol geometry
```

## The MVP Core vocabulary

Four representation-capability classes are counted in the Core, one
**classification-unresolved** capability is counted separately (a required concept
whose capability family is not yet decided), and three cross-cutting lists are
tracked separately. Classification values are exactly the coverage matrix's
vocabulary; every row below also has (or gains) a row there. The graphics audit
of the selected sheets confirms that each requirement below occurs in the selected
drawing content; it adds no row and changes none
([Graphics audit of the selected sheets](#graphics-audit-of-the-selected-sheets)).

```text
counted in the Core (four capability classes + the classification-unresolved class)
    required      symbols, composed representations, connections, annotations
    optional      same classes, allowed but not needed for the selected information
    not required  same classes, with the reason recorded

counted in the Core as unresolved (one capability)
    a required concept whose capability family (annotation vs connection) is a
    representation-design question — counted once, in no other class

tracked outside the Core (never added to the Core total)
    project conventions
    semantic gaps
    representation-design questions
```

Column meanings:

```text
Context         the diagram context the selected content needs the concept in
Requirement     required / optional / not required, per the derivation rule above
Stable identity resolved / unresolved, from mvp-symbol-coverage.md — whether one
                graphical identity is decided, as distinct from whether the
                capability is required
Selected evidence  the neutral reference(s) that establish the requirement
Current support implemented / partial / missing, from mvp-symbol-coverage.md
Gap type        the precise gap where support is not implemented
```

### 1. Base graphical requirements (17 families: 13 resolved identities, 4 unresolved)

A **required concept family** and a **resolved symbol identity** are separate
states: a family may be required while its graphical identity or granularity is
still a representation-design question. Only a resolved identity can be a
`missing base SymbolDefinition`.

| # | Concept | Context | Classification | Requirement | Stable identity | Selected evidence | Current support | Gap type |
|---|---|---|---|---|---|---|---|---|
| A01 | Filter | pfd + pid | `symbol` | required | **unresolved** | PFD A (gas and liquid filtration steps); P&ID B (filter equipment) | missing | representation identity unresolved — one cross-context identity vs context-specific forms must be decided before SymbolDefinition implementation (question G1) |
| A02 | Compressor | pfd | `symbol` | required | resolved | PFD A | missing | missing base SymbolDefinition |
| A03 | Heat-transfer equipment — heater, superheater, preheater, evaporator, exchanger (requirement family) | pfd + pid | `symbol` | required | **unresolved** | PFD A (several heat-transfer duties); P&ID B (evaporator equipment) | missing | representation identity unresolved — one reusable identity vs several duty / equipment identities is not decided (question G11) |
| A04 | Mixer (two or more process inlets) | pfd | `symbol` | required | resolved | PFD A | missing | missing base SymbolDefinition |
| A05 | Reactor / burner | pfd | `symbol` | required | resolved | PFD A | missing | missing base SymbolDefinition |
| A06 | Pump | pfd + pid | `symbol` | required | resolved | PFD A; P&ID A (duty and stand-by instances) | **implemented** (`pump.centrifugal`, `diagram_types = ("pfd", "pid")`) | — (geometry review before any profile migration, per #127) |
| A07 | Vessel / tank / drum with nozzles (requirement family) | pfd + pid | `symbol` | required | **unresolved** | PFD A; P&ID A; P&ID B | missing | representation identity unresolved — one reusable identity vs separate vessel / tank / drum / column identities is not decided (question G2) |
| A08 | Gate valve | pid | `symbol` | required | resolved | P&ID A; P&ID B | **implemented** (`valve.gate`) | — (external recognizability and exact geometry unresolved, per #127) |
| A09 | Globe valve | pid | `symbol` | required | resolved | P&ID A | missing | missing base SymbolDefinition |
| A10 | Check valve | pid | `symbol` | required | resolved | P&ID A; P&ID B | missing | missing base SymbolDefinition |
| A11 | Ball valve | pid | `symbol` | required | resolved | P&ID B | missing | missing base SymbolDefinition |
| A12 | Three-way valve | pid | `symbol` | required | resolved | P&ID A | missing | missing base SymbolDefinition |
| A14 | Safety / relief valve (spring-loaded indication) | pid | `symbol` | required | resolved | P&ID B (several, with set pressure); P&ID A | missing | missing base SymbolDefinition |
| A15 | Restriction orifice | pid | `symbol` | required | resolved | P&ID A; P&ID B | **implemented** (`fitting.restriction_orifice`; two continuous outer strokes framing a centred split restriction stroke) | — |
| A16 | Reducer (concentric / eccentric) | pid | `symbol` | required | resolved | P&ID B (a reducer in series with a check valve) | missing | missing base SymbolDefinition |
| A17 | Instrument base graphic, field-mounted | pid | `symbol` | required | resolved | P&ID A; P&ID B; PFD A (instruments drawn on the PFD too) | **implemented** (`instrument.local`) | — (profile composition unresolved, #124) |
| A18 | Measurement sensor / primary element (inline on the process) (requirement family) | pid | `symbol` | required | **unresolved** | P&ID A (a flow element); P&ID B | missing | representation identity unresolved — one reusable identity vs one graphic per measured variable is not decided (question G4) |

The identifier `A13` is retired. Earlier revisions recorded a standalone
control-valve *body* here; the selected evidence requires a **control valve**
(composed representation `B01`) and does not establish a stable standalone body
identity, so that requirement is tracked with `B01` and the body's identity model
is recorded as a representation-design question (G12).

### 2. Composed representations (5 required)

| # | Concept | Context | Classification | Requirement | Selected evidence | Current support | Gap type |
|---|---|---|---|---|---|---|---|
| B01 | Control valve with actuator (body composed with an actuator graphic; the body component is required, but its standalone stable identity is a representation-design question, G12) | pfd + pid | `composed-symbol` | required | P&ID A; P&ID B; PFD A | missing | composition gap |
| B02 | On/off actuated valve with position indication | pid | `composed-symbol` | required | P&ID A; P&ID B | missing | composition gap |
| B03 | Instrument function composition (base graphic + function letter code + loop designation) | pfd + pid | `composed-symbol` | required | P&ID A; P&ID B; PFD A | missing | composition gap (the base graphic exists; the letter-code annotation does not) |
| B04 | Control-system instrument variant (panel / shared display / control-system participation) | pid | `composed-symbol` | required | P&ID A; P&ID B (control-system functions, alarms and set points are reported rather than local) | missing | composition gap |
| B05 | Safety-system instrument variant (instrument marked as part of the safety system) | pid | `composed-symbol` | required | P&ID B (safe-location routing, safety interlocks, safety valves) | missing | composition gap (the referenced logic is a semantic gap, F3) |

### 3. Connections (6 required)

| # | Concept | Context | Classification | Requirement | Selected evidence | Current support | Gap type |
|---|---|---|---|---|---|---|---|
| C01 | Directional process stream | pfd | `connection` | required | PFD A (direction arrows on every stream) | implemented — drawn by the process renderer as output, not as a SymbolDefinition | — |
| C03 | Off-page connector (sheet-to-sheet continuation with a reference) | pfd + pid | `connection` | required | PFD A; P&ID A; P&ID B | missing | connection-rendering gap |
| C04 | Piping line — orthogonal routing, branch / junction, direction indication | pid | `connection` | required | P&ID A (branches, parallel branches); P&ID B | missing | connection-rendering gap (routing exists for process streams only) |
| C05 | Instrument process connection (functional tap) | pid | `connection` | required | P&ID A; P&ID B | partial — the `tap` anchor exists on `instrument.local`; the line convention does not | connection-rendering gap |
| C06 | Instrument signal line, electric | pid | `connection` | required | P&ID A; P&ID B (reported functions) | missing | connection-rendering gap (signal lines must not become `Connection`) |
| C07 | Line treatment — insulation, heating, tracing, as **authored data** | pid | `connection` (line treatment) | required as data; graphical decoration optional (not needed to preserve the selected information; the selected content states treatment as a property or note) | P&ID A (a selected note requires tracing); legend A (insulation and heating codes) | missing (no authored carrier) | semantic-model gap (F5) |

### 3a. Classification-unresolved capability (1)

| # | Concept | Context | Classification | Requirement | Selected evidence | Current support | Gap type |
|---|---|---|---|---|---|---|---|
| C02 | Process boundary connector (battery limit, labelled) | pfd + pid | **unresolved** (annotation vs connection) | required | PFD A; P&ID A (incoming and outgoing boundaries) | missing | classification unresolved — which capability family owns a labelled boundary connector is question G10 |

Whether a labelled boundary connector is an `annotation` or a `connection` is not
decided by the requirements evidence, so it is not counted in the connection total
and not forced into the annotation class. Its representation is a marker plus a
label associated with a boundary / stream endpoint: it is **not** equipment
geometry and **not** a normal standalone equipment `SymbolDefinition`. The
canonical coverage matrix records it in its own classification-unresolved
capability class.

### 4. Annotations (11 required)

| # | Concept | Context | Classification | Requirement | Selected evidence | Current support | Gap type |
|---|---|---|---|---|---|---|---|
| D01 | Stream number label | pfd | `annotation` | required | PFD A (every stream numbered) | implemented — the renderer's label layer draws the process stream id | — |
| D02 | Stream property / composition data (medium, phase, mass / volume / molar flow, temperature, pressure, density, molecular weight, composition, duty) | pfd + pid | `annotation` | required as data; an automatic drawing table is optional (the information is preserved without it) | PFD A (a full stream property and composition table) | missing | semantic-model gap (F1) |
| D03 | Equipment tag / name label (with the project equipment-code prefix) | pfd + pid | `annotation` | required | PFD A; P&ID A; P&ID B | partial — step id and name labels are drawn for process steps only | annotation gap |
| D04 | Duty / rating / set-point annotation (heat duty, relief set pressure) | pfd + pid | `annotation` | required | PFD A (heat duty per equipment item); P&ID B (relief set pressure) | missing | semantic-model gap (F6) |
| D05 | Nozzle designation | pid | `annotation` | required | P&ID A; P&ID B (equipment nozzles carry lettered role designations) | missing | annotation gap |
| D06 | Line tag (medium + sequence + nominal size + piping class) | pfd + pid | `annotation` | required | PFD A; P&ID A; P&ID B | missing | annotation gap (values are project conventions) |
| D07 | Instrument loop designation (function letters + loop number, with plant / location code) | pid | `annotation` | required | P&ID A; P&ID B | missing | semantic-model gap (F2) |
| D08 | Instrument alarm / limit annotation (high, high-high, low, low-low) | pid | `annotation` | required | P&ID A; P&ID B | missing | annotation gap |
| D09 | Fail-state annotation (fail-closed / fail-open / fail-lock / normally-closed) | pfd + pid | `annotation` | required | P&ID B; PFD A (a normally-closed valve state); legend B | missing | annotation gap |
| D10 | Interlock / trip / permissive reference annotation | pid | `annotation` | required | P&ID B (interlock references) | missing | annotation gap plus semantic-model gap (F3) |
| D11 | Drawing note / general note (authored text annotation) | pfd + pid | `annotation` | required | PFD A; P&ID A; P&ID B (notes carry engineering information needed to read the content) | missing | semantic-model gap (F4) |

### 5. Project conventions (13, tracked outside the base symbol library)

| # | Convention | Handling |
|---|---|---|
| E01 | Equipment and valve tag prefixes, equipment-code letters | Tag text is composed by the project; never embedded in base geometry. |
| E02 | Fluid / medium code list | Values are authored data; the code list is not DeepPlant vocabulary. |
| E03 | Line-number and line-designation rules | Authoring and validation concern outside the symbol library. |
| E04 | Piping-class and nominal-size designation | Authored data, validated per project practice. |
| E05 | Insulation, heating and tracing codes | Authored data; geometry may later carry only decoration. |
| E06 | Nozzle-role letter designations | Project text; the nozzle annotation itself is a Core entry (D05). |
| E07 | Instrument letter-code system (measured variable, succeeding functions, modifiers) | Drives the annotation composed onto the base graphic (B03); the code list is project notation. |
| E08 | Instrument loop and plant / location numbering | Project numbering; the designation itself is a Core entry (D07). |
| E09 | Alarm, trip, permissive, safety-interlock and trip-group numbering systems | Company-specific; excluded from the base library. |
| E10 | Control-system (DCS) and safety-system (SIS) participation, including the software-link convention | Project notation; the instrument *variant* is a Core entry (B04, B05), the convention is not. |
| E11 | Actuator and control-system marking conventions (mounted location, fail position, positioner, solenoid, motor) | Project notation layered on Core composition (B01, B02) and annotation (D09). |
| E12 | Corporate title block, revision table, drawing frame, equipment data table | Document production; out of scope as symbol vocabulary. |
| E13 | Composite project typicals | Resolution of a typical reference is deferred; the reference marker is not a copy of the typical. |

### Not required for the selected MVP information

Recorded explicitly, so that no operator-selected vocabulary is dropped silently.
Each entry is defined by the selected project notation but is not needed to
represent the selected *drawing* content.

| Concept (concept level) | Reason it is not required |
|---|---|
| Specialty valves defined by legend A but not used by the selected drawings: butterfly, plug, needle, injection, angle, stop-check, automatic-recirculating check, backflow preventer, vacuum breaker, breath valve, automatic vent valve, valve with built-in bypass | Defined by the selected notation legend only; no selected drawing needs it represented. No occurrence of these named forms was located in the graphics audit of the selected sheets. Because a sheet-only inspection cannot name a valve type — the legend's first valve rows are the general valve open / closed forms — this stays a recorded scope statement rather than an assertion about what is absent ([Graphics audit of the selected sheets](#graphics-audit-of-the-selected-sheets)). |
| Piping fittings and accessories defined by legend A but not used by the selected drawings: spectacle blind / blank, cap and plug, screwed cap, sight glass, funnel / drain, steam trap / condensate trap, flame arrestor, flexible hose, expansion joint, mechanical coupling, sprayer, dividing chute, hose connection, silencer / damper | Same reason: defined by the selected notation legend only, and no occurrence of these named forms was located in the graphics audit. Recorded rather than assumed. |
| Instrument letter-code combinations not used by the selected drawings: record, integrate / totalise, scan, multivariable / multifunction instrument, and position or limit switches beyond the evidenced ones | Defined by legend B and not located in the selected drawing content. The graphics audit did locate the instrument presentation variants with their letter and loop designations, but not these specific letter-code combinations. Multivariable and multifunction instruments also stay out of the Core because the selected content reports single-function loops. |
| Detailed electrical and motor-control representation | The selected drawings show actuators, position indications and fail states, but no detailed electrical schematic content. |
| Voting indication (2-out-of-2 / 2-out-of-3), trip / permissive diamond markers | **Corrected after the graphics audit:** these markers do occur in the selected P&ID content, so they are no longer recorded as an evidence gap. They are not a separate requirement: a voting indication and a trip / permissive marker are markings of the interlock / trip / permissive reference annotation already in the Core (D10) and of the safety-system instrument variant (B05), the numbering stays a project convention (E09), and the referenced logic stays semantic gap F3 ([Graphics audit of the selected sheets](#graphics-audit-of-the-selected-sheets)). |
| Vendor / package detail, title-block and revision content | Document production, not symbol vocabulary (see E12). |
| Duplicate / parallel equipment and repeated control loops | Not a representation question: they deduplicate to one representation plus project numbering (E01, E08) and repeated instances. |

### Pumping across the PFD and the P&ID

The process model's `ProcessStep` must stay distinct from the physical `Equipment`
([contracts/process-model.md](../../contracts/process-model.md)), and the PFD and
the P&ID are separate diagram contexts. That semantic distinction does **not**
create a second graphical identity:

```text
different semantic object   =/=>  different graphical symbol identity
```

`pump.centrifugal` is the graphical representation the repository implements
today, and its contract already declares `diagram_types = ("pfd", "pid")`, so it is
the available representation in **both** diagram contexts. This selection
therefore records **one** pumping entry (A06) and does **not** introduce a
PFD-specific pump `SymbolDefinition`. Its #127 conclusion — geometry review before
any notation-profile migration, redesign possible but not established — is
unchanged. If the selected references genuinely require a different PFD graphical
concept for pumping, that is a representation-design question, not a new identity
declared here.

The pump is the **only** concept for which the cross-context question is already
answered. The other concepts the selected content requires in both contexts —
filter (A01), heat-transfer equipment (A03), vessel / tank / drum (A07) — do not
inherit that answer from the pump: whether one representation serves both contexts
or each context has its own form is question G1, so those identities stay
unresolved until it is answered. Requiring the same engineering word twice in two
contexts is neither evidence for one graphical identity nor evidence against it.

### Valve identity

```text
shared graphical construction primitive  !=  shared stable symbol identity
```

The gate valve's neutral `port_a` / `port_b` anchors are reusable,
notation-independent connection points: they mean only that this representation
does not embed inlet/outlet flow semantics. Other valve concepts may reuse
graphical construction primitives where appropriate, but they retain distinct
stable symbol identities and representations. `valve.gate` represents a gate
valve; it does **not** represent globe, check, ball, three-way, control, or
safety / relief valve concepts, and this selection keeps those entries distinct
(A09-A14).

The correct distinctions used in this document:

```text
distinct engineering / graphical concept  ->  distinct stable symbol identity
shared visual construction                ->  reusable primitive / composition
state, tag, code, numbering               ->  annotation, composition, or project data
```

No valve identity architecture is redesigned here.

## Semantic gaps (6, tracked outside the Core)

A selected MVP requirement with no valid current DeepPlant semantic
representation. Recorded, **not solved**: no domain-model solution is invented
here, and the preserved boundaries are `ProcessStep != Equipment`,
`ProcessStream != physical Connection / PipingLine`, and
`ProcessPort != physical Port / Nozzle`.

| # | Concept | Diagram context | Why the current model is insufficient | Neutral MVP reference that requires it | Future decision needed |
|---|---|---|---|---|---|
| F1 | Stream properties and composition (medium, phase, flow, temperature, pressure, density, molecular weight, composition, duty) | PFD | `ProcessStream` carries only `id`, `name`, `source`, `target`; no quantity/unit typing exists yet | MVP PFD reference A (Core D02) | How qualified engineering quantities attach to a stream without turning it into a table |
| F2 | Instrument as a semantic object, and its loop designation | P&ID | No instrument entity exists; only a graphical base representation does, so a designation has nothing to attach to | MVP P&ID references A and B (Core D07, B03) | Whether an instrument/loop object belongs in the model or in a presentation layer |
| F3 | Safety-interlock / trip / permissive reference and the logic it refers to | P&ID | No representation for the referenced logic; `ProcessStream`/`Connection` are the wrong carriers | MVP P&ID reference B (Core D10, B05) | Where interlock references live without becoming piping or signals |
| F4 | Authored drawing notes | PFD and P&ID | The model has no note / annotation carrier at all | MVP PFD reference A; MVP P&ID references A and B (Core D11) | Whether notes are model objects or a document layer |
| F5 | Line treatment as authored data (insulation, heating, tracing) | P&ID | No authored carrier on the piping layer | MVP P&ID reference A (Core C07) | Where treatment data lives, given the code values stay project conventions |
| F6 | Equipment duty and device set-point values (heat duty, relief set pressure) | PFD and P&ID | No quantity typing on equipment or devices | MVP PFD reference A; MVP P&ID reference B (Core D04) | Whether the qualified-quantity work (research: [qualified-engineering-quantities.md](qualified-engineering-quantities.md)) is the carrier |

## Representation-design questions (12, tracked outside the Core)

Recorded rather than decided. None of them authorizes a new identity.

| # | Question | Raised by |
|---|---|---|
| G1 | One cross-context representation per equipment concept, or context-specific forms? Four base concepts are required in both the PFD and the P&ID (filter A01, pump A06, heat-transfer equipment A03, vessel / tank / drum A07), and the composed control-valve requirement (B01) is required in both contexts too; only `pump.centrifugal` (A06) currently establishes that one representation can be available in both contexts, so the filter, heat-transfer-equipment and vessel / tank / drum identities stay unresolved | Selected PFD and P&ID content |
| G2 | Does the A07 family need one reusable identity, or separate vessel / tank / drum / column identities (the selected PFD draws a column / tower item)? | MVP PFD reference A |
| G3 | Are both concentric and eccentric reducer forms required (A16)? | MVP P&ID reference B |
| G4 | One reusable measurement-sensor representation, or one graphic per measured variable (A18)? | MVP P&ID references A and B |
| G5 | Which actuator graphics does the selected content require (diaphragm, cylinder, motor, solenoid, manual, positioner)? | MVP P&ID references A and B; legend B |
| G6 | Straight or angle relief-valve forms, and where the set pressure is carried (A14, D04)? | MVP P&ID reference B |
| G7 | Does the MVP need automatic stream-table rendering, or only the authored data (D02)? The selected PFD draws a property table; the information is preserved without it | MVP PFD reference A |
| G8 | Does line treatment need graphical decoration, or only the authored property (C07)? | MVP P&ID reference A |
| G9 | Is the selected *legend* vocabulary itself MVP-required, widening the Core by the not-required list above? | Recorded scope question |
| G10 | Which capability family is the labelled process boundary connector (C02) — annotation or connection? Until it is answered, C02 is counted in the coverage matrix's classification-unresolved capability class and not in the connection total | MVP PFD reference A; MVP P&ID reference A |
| G11 | Does the heat-transfer family (A03) map to one stable identity, or to several duty / equipment identities (heater, superheater, preheater, evaporator, exchanger)? | MVP PFD reference A; MVP P&ID reference B |
| G12 | Which representation model gives the control-valve composition (B01) a stable body identity — a dedicated `valve.control` body identity, another reusable valve-body identity, an explicitly typed composition primitive, or another representation model? Not decided by the requirements evidence | MVP P&ID references A and B |

## Implementation coverage

Capability-specific, mechanically reconciled with the tables above. An annotation, a
connection, or an identity-unresolved requirement family is never reported as a
"missing SymbolDefinition".

```text
base graphical requirements        17 families
  stable identities resolved       13
    implemented                     4   valve.gate, pump.centrifugal, instrument.local,
                                       fitting.restriction_orifice
    resolved but missing            9
  identity / granularity unresolved  4   filter (A01, cross-context identity, G1),
                                         heat-transfer equipment (A03),
                                         vessel / tank / drum (A07),
                                         measurement sensor / primary element (A18)

composed representations
        required        5
        implemented     0
        missing         5

connection capabilities / styles
        required        6
        implemented     1   directional process stream (renderer output, not a SymbolDefinition)
        partial         1   instrument process connection (tap anchor exists; line convention missing)
        missing         4

classification-unresolved capability
        required        1   labelled process boundary connector (C02; its capability
                            family is question G10, so it is not counted as a connection)

annotation capabilities
        required       11
        implemented     1   stream number label (process renderer label layer)
        partial         1   equipment / step id-and-name labels (process steps only)
        missing         9

tracked outside the Core
        project conventions                  13
        semantic gaps                         6
        representation-design questions      12
```

## Selection summary

```text
40  MVP Core requirement entries
   17  base graphical requirement families
    5  composed representations
    6  connections
   11  annotations
    1  classification-unresolved capability

13  project conventions             tracked outside the Core
 6  semantic gaps                   tracked outside the Core
12  representation-design questions tracked outside the Core

base graphical requirement families  17
  stable identities resolved         13
    implemented                       4   valve.gate, pump.centrifugal, instrument.local,
                                          fitting.restriction_orifice
    resolved but missing              9
  identity / granularity unresolved   4
```

Reconciliation, counting every Core row exactly once:
`40 = 17 + 5 + 6 + 11 + 1`; base `17 = 13 + 4`; resolved base `13 = 4 + 9`;
composed `5 = 0 + 5`; connections `6 = 1 + 1 + 4`; annotations `11 = 1 + 1 + 9`;
classification-unresolved capability `1`.

The previous revision of this document recorded **28** Core entries across five
"partitions", counted project conventions as a partition while excluding them from
the arithmetic, and reported a single "25 remaining" metric. All three statements
are withdrawn: the Core total now counts only representation-capability classes,
project conventions are tracked separately, and implementation state is reported
per capability. The corrected revision that followed still reported **41** entries
with **18** base symbols and **15** missing; that is withdrawn too, because it
counted a standalone control-valve *body* identity the evidence does not establish
and reported three identity-unresolved requirement families as exact missing
`SymbolDefinition`s. The "7 connections" and "14 resolved base identities" counts
are withdrawn as well: the labelled boundary connector's capability family is
question G10, so it is counted in its own class, and the filter's cross-context
identity is question G1, so it is unresolved rather than resolved. The Core now
separates a required capability from a resolved stable graphical identity.

The Core is closed for MVP acceptance purposes only through the same operator
decision as the reference set: widening it requires an operator selection or an
answer to a recorded discrepancy — not a symbol implementation, and not a
repository preference.

## Relationship to the three `generic-iso` representations

| Symbol | Keeps the classification from #127 | MVP Core role |
|---|---|---|
| `valve.gate` | `deepplant-default` candidate (internal design grounds); external recognizability insufficiently evidenced; exact standards geometry unresolved | the Core's gate-valve base symbol (A08) — one of several distinct valve identities |
| `pump.centrifugal` | `REVIEW_BEFORE_MIGRATION / INSUFFICIENT_EVIDENCE`; redesign possible but not established; exact standards geometry unresolved | the Core's pumping representation (A06), available in both the PFD and the P&ID context |
| `instrument.local` | `deepplant-default` candidate; instrumentation-specific context relevant; exact standards geometry unresolved; standards-specific profile composition unresolved under #124 | the Core's reusable instrument base graphic (A17) |

Three properties of these definitions are load-bearing for the Core and are not
reopened here:

- the gate valve's neutral `port_a` / `port_b` anchors are reusable,
  notation-independent connection points; they express only that this
  representation embeds no inlet/outlet flow semantics, and they do not make
  `valve.gate` a shared identity for throttling, check, ball, or other valve duty;
- the pump's `suction` / `discharge` anchors are engineering names for a pump,
  with anchor geometry recording only where a line leaves the symbol;
- the instrument base graphic deliberately carries **no** function letters, tag,
  and no mandatory signal anchor, because letter composition and signal
  connections belong to composition (B03, B04, B05), not to the base graphic.

```text
this document    selects vocabulary        no production change
#127             classifies profiles       no production change
#124 / #125      own profile architecture  separate scope
```

## Explicit non-goals

- No symbol is implemented, redesigned, or re-anchored by this document; no new
  PFD-specific or valve-family identity is introduced.
- No `notation_profile` assignment changes; `generic-iso` stays the transitional
  profile for all three `generic-iso` definitions.
- No geometry is authored, adjusted, or measured — and no copied or measured
  geometry is taken from the reference set.
- No standard is claimed, no locator recorded, and no compliance inferred from
  visual similarity, from a production drawing, or from a project legend
  ([standards.md](../workflow/standards.md)).
- No verification state is promoted: nothing in this document compares any
  geometry with any standard.
- No project-specific value (tag, line number, note, code, title-block field)
  becomes part of DeepPlant's vocabulary; those stay authored data.
- No private drawing identity — filename, document number, drawing title, path,
  title-block value, customer or project identifier — is recorded.

## Graphics audit of the selected sheets

The vocabulary above was first read from the sheets' text layer. Each sheet was
then re-inspected as **rendered graphics**, tile by tile, so that what a text layer
cannot carry — symbol form, marker shape, signal-line style, line treatment — was
inspected directly instead of being recorded as unverifiable. The audit locates
forms; it does not measure, compare, vectorise, trace, or copy anything, and it
records no tag, code value, line designation, note text, title-block field, or
document identifier ([standards.md](../workflow/standards.md), ADR-0007).

```text
located in the rendered sheets (concept level)

base equipment graphics   compressor; reactor / burner with internals; mixer;
                          vessel / drum and tank outlines with nozzles; a column;
                          filters; heat-transfer items with internals; pumps
inline valve bodies       more than one distinguishable two-triangle body form; a
                          body carrying an internal mark; a three-port body; an
                          inline body carrying a mounted operator
inline fittings           restriction orifice with an expressed bore; reducer;
                          spring-loaded safety / relief valve
instruments               a field-mounted base graphic; a control-system
                          (shared-display) variant; a safety-system variant; alarm
                          and limit letters; set-point values; functional taps
connections               routed piping with branches; battery-limit boundaries;
                          off-page / continuation markers; electric signal lines
                          drawn distinctly from process lines
annotations               stream numbers; equipment tags and names; nozzle
                          designations; line designations; drawing and data notes;
                          line-treatment (tracing) marks
markers                   safety-interlock boxes carrying voting indication
                          (2-out-of-2 / 2-out-of-3); trip / permissive diamond
                          markers; a composite-typical reference marker
```

What the audit changes, and nothing else:

```text
1. occurrence is confirmed; no requirement is added: the Core stays 40 entries and
   no row's requirement, stable identity, profile, or gap type moves
2. two text-layer limitations recorded in the first revision are corrected,
   because the forms they doubted were located directly
3. a sheet alone cannot name a valve type: the legend's first valve rows are the
   general valve open / closed forms, so a two-triangle body on a sheet is not
   evidence for one named valve type in particular — the Core keeps distinct valve
   requirement rows, and the type-to-form mapping stays legend evidence
4. voting indication and trip / permissive markers are markings of the interlock /
   trip / permissive reference annotation already in the Core (D10) and of the
   safety-system instrument variant (B05), so they are recorded inside those
   requirements rather than as a new entry
```

The audit is occurrence evidence only. It takes no copied or measured geometry, and
it is not naming, layout, or compliance evidence; it promotes no verification state:
observing that a sheet contains a symbol form establishes no standards relationship
([standards.md](../workflow/standards.md), ADR-0007).

## Evidence gaps and limitations

- **The complexity-gate discrepancy is unresolved.** The selected directory
  contains the sheet the bundled profile calls the post-MVP gate; this selection
  treats it as inside the boundary and records the discrepancy for the operator.
- **The legend scope question is unresolved.** Whether the selected legend
  vocabulary is itself MVP-required is an operator decision; until it is answered,
  legend-only concepts stay in the recorded not-required list.
- **Graphics-audit limits (this replaces the former text-layer limitation).** The
  sheets were re-inspected as **rendered graphics**, not only through their text
  layer, so the earlier limitation — that a purely graphical occurrence cannot be
  confirmed — no longer applies to the selected sheets
  ([Graphics audit of the selected sheets](#graphics-audit-of-the-selected-sheets)).
  What remains open is naming rather than occurrence: the valve legend's first rows
  are the general valve open / closed forms, so a two-triangle body on a sheet is
  not evidence for one named valve type in particular; a sheet-level graphics look
  cannot measure or compare geometry; and an occurrence that was not located is
  recorded as a scope statement, never as proof of absence.
- **Voting and trip markers (corrected).** The graphics audit located voting
  indication (2-out-of-2 / 2-out-of-3) and trip / permissive diamond markers in the
  selected content, so they are no longer recorded as an evidence gap and no longer
  as a semantic-gap candidate by themselves. They are markings of the interlock /
  trip / permissive reference annotation already in the Core (D10) and of the
  safety-system instrument variant (B05); the numbering stays a project convention
  (E09) and the referenced logic stays semantic gap F3. This correction adds no
  Core entry and changes no count.
- **Construction details** (weld, flange, cap/plug, funnel, drain) occur in the
  selected notation but are not needed to represent the selected drawing content;
  their exclusion is recorded in the not-required list, not silently decided.
- **Whether a driver / energy anchor belongs on the pump symbol** stays open (same
  question as the coverage matrix's unresolved list).
- **How a control valve's actuator composition is modelled** (variant of a valve
  body, or a separate actuator graphic composed at render time) is not settled by
  this selection, and neither is the standalone stable identity of the valve body
  (G12); the requirement is only that the control-valve representation stay
  required and its semantic subtype stay explicit.
- **The bundled profile's stream-property claim** does not match the current model
  (see [Recorded discrepancies and scope questions](#recorded-discrepancies-and-scope-questions)).
- **The bundled profile remains `proposed`.** That is now context, not a gate: it
  no longer decides whether an operator-selected requirement is recognized.

## Recommended follow-up slices

Research recommendations, **not** created Issues, and **not** implementation
authorization. Each requires its own separately scoped and Ready Issue.

| # | Slice | Category | Depends on |
|---|---|---|---|
| 1 | Resolve the recorded discrepancies: confirm whether the complexity-gate sheet is inside the MVP boundary, and whether the selected legend vocabulary is MVP-required | A — scope | operator decision |
| 2 | Implement the P&ID base symbols whose stable identity is resolved (globe, check and ball valve, restriction orifice, safety / relief valve, reducer), one small slice each; resolve the vessel / tank / drum identity / granularity question (G2) before implementing that family | B — base symbols | 1; existing symbol contract |
| 3 | Implement the PFD process-step representations the process model needs, keeping `ProcessStep` distinct from `Equipment`; resolve the heat-transfer identity / granularity question (G11) before implementing that family | C — base symbols | 1; [contracts/process-model.md](../../contracts/process-model.md) |
| 4 | Deliver composition machinery (function-letter composition, actuator composition, control-system and safety-system instrument variants), resolving the control-valve body representation model (G12) | D — composition | 2, 3 |
| 5 | Deliver the connection capabilities (off-page connector, branching routed piping, electric signal line), resolving the boundary-connector capability family (G10) before adding the boundary connector | E — connections | 2, 3 |
| 6 | Deliver the annotation capabilities, with the semantic carriers F1-F4 scoped in their own model Issue | F — annotations and model gaps | 4; a model Issue for the carriers |
| 7 | Focused review of `pump.centrifugal` geometry before any notation-profile migration, per the [notation-profile classification](notation-profile-classification.md) | G — review before migration | — |

The coverage matrix now carries the MVP Core status per row and separates its
current profile from target notation and standards evidence, so no matrix-shaped
slice remains. Selecting and persisting a concrete notation profile stays Issue
#124's scope and is not restated here as a new recommendation.

Explicitly not recommended: creating these Issues automatically, or widening the
Core by observing the reference set without recording the selection decision.

## Sources

### Repository-authored evidence actually used

- [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md) — classification
  vocabulary, per-concept status, and the reference-material handling rules.
- [symbol-library.md](../reference/symbol-library.md) — the symbol contract, the
  implemented representations, and their `diagram_types`.
- [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) — the
  DeepPlant-owned geometry spec the definitions are authored from.
- [notation-profile-classification.md](notation-profile-classification.md) — the
  current profile classification, preserved unchanged.
- [contracts/process-model.md](../../contracts/process-model.md) — the stream and
  step contract, and therefore the basis for semantic gaps F1, F2, F4 and F6.
- [qualified-engineering-quantities.md](qualified-engineering-quantities.md) — the
  quantity/unit evidence relevant to F1 and F6.
- [standards.md](../workflow/standards.md),
  [standards-registry.md](../reference/standards-registry.md) — standards usage
  and provenance policy.
- [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md),
  [ADR-0017](../decisions/ADR-0017-machine-rendered-symbol-definitions.md).
- [catalogue.py](../../../src/deepplant/symbols/catalogue.py) and
  [profiles.py](../../../src/deepplant/symbols/profiles.py) — read-only
  confirmation of the implemented catalogue, its anchors, and its profile
  vocabulary.
- Issues #119, #124, #127 and PR #123 — scoping context.

### Private reference set actually inspected (requirements boundary)

Listed by neutral role in [Inspected evidence](#inspected-evidence). The bundle is
not committed, and no artwork, locator, item number, layout, tag, code, note text,
document identifier, or drawing title from it is reproduced here.

```text
MVP PFD reference A                     process-side requirements
MVP P&ID reference A                    physical and instrumentation requirements
MVP P&ID reference B                    complexity-gate requirements
supporting P&ID legend A                piping-elements notation
supporting P&ID legend B                instrumentation-and-control notation
duplicate legend copy                   counted once (identical inspected text layer)
MVP drawing profile v0.1                operator-bundled interpretation aid
```

### External AI-usable material actually inspected

None. No external source was used as evidence: no restricted ISO/ISA/IEC content
was inspected, and the reference set is company-private material used only for
scoping and qualitative notation/form interpretation.

## Related

- [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md) — the per-concept
  matrix; the MVP Core named there is derived from this document.
- [symbol-library.md](../reference/symbol-library.md) — the rendering contract and
  the implemented definitions.
- [notation-profile-classification.md](notation-profile-classification.md) — the
  profile classification this selection preserves.
- [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) — the geometry
  spec for the implemented representations.
- [standards-licensing-evidence.md](standards-licensing-evidence.md) — why the
  reference set may inform scope and qualitative form but never supply copied or
  measured geometry or standard detail.
