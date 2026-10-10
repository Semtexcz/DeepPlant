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
    6 connections
   11 annotations
    1 classification-unresolved Core capability    (C02)
13                   project conventions               (tracked outside the Core)
 6                   semantic gaps                     (tracked outside the Core)
12                   representation-design questions   (tracked outside the Core)

capability-specific implementation state
  base graphical requirements   17 families
    stable identities resolved  13
      implemented                7   (valve.gate, pump.centrifugal, instrument.local,
                                      fitting.restriction_orifice, valve.globe,
                                      valve.check, valve.ball)
      resolved but missing       6
    identity / granularity unresolved  4
  composed        0 implemented / 5 missing
  connections     1 implemented / 1 partial / 4 missing
  annotations     1 implemented / 1 partial / 9 missing
  classification-unresolved  1   (C02 process boundary connector — whether a
                                  labelled boundary connector is an annotation or a
                                  connection is representation-design question G10)
```

Arithmetic: `17 = 13 + 4`; `13 = 7 + 6`; `6 = 1 + 1 + 4`; `11 = 1 + 1 + 9`;
`40 = 17 + 5 + 6 + 11 + 1`.

Three earlier summaries are withdrawn. "28 Core entries / 3 implemented / 25
remaining" counted project conventions as a partition while excluding them from
the arithmetic, and reported annotations, connections, and compositions as if they
were remaining symbol definitions. "7 connections" is withdrawn too: whether the
labelled process boundary connector (C02) is an `annotation` or a `connection` is
unresolved (representation-design question G10), so C02 is counted in its own
classification-unresolved capability class and not in the connection total.
"41 Core entries / 18 base symbols / 3 implemented / 15 missing" counted a
standalone control-valve *body* identity the selected evidence does not establish,
and reported three identity-unresolved requirement families as exact missing
`SymbolDefinition`s (see
[Requirement status and stable identity](#requirement-status-and-stable-identity)).

A later consistency repair in the same change applies the same rule to two further
rows. The labelled process boundary connector (C02) moves out of the connection
count into its own classification-unresolved capability class, because whether it
is an `annotation` or a `connection` is representation-design question G10. The
filter (A01) becomes identity-unresolved rather than resolved, because whether a
concept required in both the PFD and the P&ID has one cross-context identity or
context-specific forms is representation-design question G1 — the same reasoning
that already kept the heat-transfer, vessel / tank / drum and measurement-sensor
families unresolved.

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

## Independent facts

The matrix keeps separate statements apart, because they advance independently:

```text
required by the MVP reference      does the MVP need this concept?
stable graphical identity          is one decided SymbolDefinition identity recorded for it?
notation profile                   which profile does an implemented representation carry now?
standards relationship             the standard named as the reference direction, or `—` when
                                   none is recorded
verification                       the state of an existing standards relationship
                                   (`reference` / `candidate-alignment` / `human-verified`)
implemented in DeepPlant           does a SymbolDefinition exist yet?
```

```text
required by MVP reference
        ↓ independent
stable graphical identity
        ↓ independent
notation profile  ── independent ──  standards relationship
        ↓ independent
implementation state
```

A concept can be required and unimplemented, or implemented with no human check
claimed. Only the implementation state produces a symbol. The repository
deliberately records no restricted-derived symbol locator for the current symbols,
so no row claims that a standard's own representation was located, inspected, or
assessed.

## Notation profile and target notation

Notation profile and standards relationship are **separate axes**: a profile is a
presentation-layer selection, while a standards relationship is evidence about one
concrete geometry ([symbol-library.md](symbol-library.md), ADR-0003). They must not
be collapsed into one field.

```text
stable concept / symbol identity
        ↓
DeepPlant-owned practical representation
        ↓
deepplant-default          future MVP product default, where approved (#124)

standards relationship     separate evidence axis, never a profile
```

The three legacy representations — `valve.gate`, `pump.centrifugal`,
`instrument.local` — are `generic-iso` because #125 did not migrate them. The
`deepplant-default` profile now holds four built-in representations: the
restriction orifice (A15, Issue #130) and the three basic P&ID valves (A09, A10,
A11, Issue #132). `generic-iso` is **not** the automatic future MVP
target notation for every new Core concept:

```text
Current profile          the profile an actually-implemented representation carries today
                         (`generic-iso` for the three legacy definitions and
                         `deepplant-default` for `fitting.restriction_orifice`,
                         `valve.globe`, `valve.check` and `valve.ball`; `—` for a Core
                         concept whose representation does not exist yet, and for a
                         capability that cannot carry a notation profile at all)
Target MVP notation      the intended notation direction for the required representation
                         (`deepplant-default target` / `deepplant-default candidate` /
                         `unresolved pending representation design`; `not applicable
                         (<reason>)` where the architecture claims no notation profile
                         at all — a composed representation, a connection style, or
                         authored text — and the constituents, not the capability, carry
                         the notation)
Standards relationship   the standards family named as the reference direction for the
                         concept; `—` when no relationship is recorded, so no alignment
                         direction is claimed for it
Verification             the alignment state for this concept (`reference` /
                         `candidate-alignment` / `human-verified`); `—` when no standards
                         relationship is recorded, so no correspondence is claimed for it
                         in either direction
```

Only an **implemented** representation may carry a current production profile. A
Core concept that does not exist yet is `—`, never `generic-iso`: assigning
`generic-iso` to an unimplemented concept would claim an intended standards
correspondence for geometry that does not exist. `deepplant-default` marks a
future direction where the architecture supports it, and never claims that a
concrete geometry has been approved — where a representation's graphical identity
is still undesigned, the target notation is `unresolved pending representation
design`. Not every Core capability has a notation profile at all: a composed
arrangement, a connection style, and an annotation belong to future
presentation-profile architecture, so their target notation is `not applicable
(<reason>)`, and `deepplant-default` is recorded only for a base graphical
requirement ([symbol-library.md](symbol-library.md)).

## Classification vocabulary

Per Issue #119, a concept whose classification is **resolved** is classified as
exactly one of:

| Classification | Meaning |
|---|---|
| `symbol` | one standalone graphical representation |
| `composed-symbol` | a representation assembled from two or more base graphics |
| `annotation` | text, labels, or a rule that is not symbol geometry |
| `connection` | a line or link convention between objects |
| `project-convention` | company/project practice that is not part of a standard library |
| `composite-typical` | a reusable project-specific arrangement referencing a typical diagram |

**Classification unresolved** is not a seventh class and is not an alternative
outcome of the six: it is a **temporary status** for a required concept whose
capability family is not yet decided, and such a concept resolves into exactly one
of the six. It exists so that no concept is forced prematurely into a class merely
to preserve a total: the labelled process boundary connector (C02) is an
`annotation` or a `connection` depending on representation-design question G10, so
C02 is counted once in its own classification-unresolved capability class in the
tables below, and never in the connection total.

## Verification vocabulary

A verification state only ever describes an **existing standards relationship**. It
is never a property of a concept that has none. The canonical vocabulary of
[standards.md](../workflow/standards.md) therefore contains exactly three
verification states — `reference`, `candidate-alignment`, and `human-verified` —
and `—` is **not** one of them.

When no standards relationship is recorded for a concept, both the relationship
and the verification columns carry `—`:

```text
Standards relationship = —
Verification           = —
```

`—` is not a verification state. It means there is no recorded
`StandardsReference` for this concept, so there is no standards relationship to
which a verification state could apply, and no correspondence is claimed in either
direction.

When a standards relationship does exist, its verification state is exactly one of:

| Verification state | Meaning for a coverage row |
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
| `unresolved` | the identity, its granularity, or its cross-context form is still a representation-design question | `representation identity unresolved — design decision required before SymbolDefinition implementation` |

`missing SymbolDefinition` is only ever used for a **resolved** identity. An
unresolved family is a required capability, not an exact missing symbol: four of
the base requirement families (filter, heat-transfer equipment, vessel / tank /
drum, measurement sensor / primary element) and the control-valve composition's
body are in that state. A requirement family may also be `required` while its
identity is resolved, and a shared graphical primitive never by itself creates a
shared stable identity.

A concept that the selected content requires in **both** the PFD and the P&ID has
one further identity question: whether one cross-context representation serves both
contexts or each context has its own form (representation-design question G1).
`pump.centrifugal` is the only base concept that already establishes the
cross-context answer — its contract declares `diagram_types = ("pfd", "pid")` — so
the other cross-context base concepts (filter A01, heat-transfer equipment A03,
vessel / tank / drum A07) stay `unresolved` until that question is answered.
Requiring a concept in both contexts is never itself evidence that one stable
`SymbolDefinition` exists.

## Reference material handling

The operator-selected MVP reference bundle — one PFD sheet, two P&ID sheets, and
the project's piping-elements and instrumentation-and-control notation legends,
summarised by the operator-bundled *DeepPlant MVP drawing support profile v0.1* —
is private project material, and it is the authoritative MVP requirements
boundary. It answers **what must be representable**, **how the selected project
draws it**, and **which linework is intrinsic glyph versus connection versus
annotation**; it serves as qualitative notation/form evidence, and it is never a
source of **copied or measured** geometry. No artwork, coordinate, proportion,
path data, dimension, or pixel is traced, vectorised, measured, or reproduced from
it, and no title block, tag, note, document identifier, drawing title, or symbol
sheet is reproduced
([standards.md](../workflow/standards.md), ADR-0007). It is referenced only by
neutral role identifiers ([../research/mvp-symbol-core-selection.md](../research/mvp-symbol-core-selection.md)),
and DeepPlant normalized seed geometry remains independently authored.
The concept-level selection this matrix records was additionally verified against
the sheets' **rendered graphics** (symbol form, marker shape, and signal-line
style); that audit locates forms only, takes no copied or measured geometry, and
establishes no standards correspondence ([mvp-symbol-core-selection.md, graphics
audit](../research/mvp-symbol-core-selection.md#graphics-audit-of-the-selected-sheets)).

The companies' own conventions (tag prefixes, line designation, DCS/SIS
practice, interlock numbering) are recorded here as `project-convention` so they
cannot be mistaken for a standard base library.

## MVP Core coverage

Canonical per-concept inventory of the final MVP Core. Every entry is one
requirement from the selected MVP reference content, and the identifiers match the
[evidence document](../research/mvp-symbol-core-selection.md). `Requirement` and
`Stable identity` are separate states (see
[Requirement status and stable identity](#requirement-status-and-stable-identity)).

### 1. Base graphical requirements (17 families: 13 resolved identities, 4 unresolved)

| # | Concept | Context | Classification | Requirement | Stable identity | Current profile | Target MVP notation | Standards relationship | Verification | Current support & representation | Gap type |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A01 | Filter | pfd + pid | `symbol` | required | **unresolved** | — | unresolved pending representation design | — | — | missing; equipment outline with process anchors | representation identity unresolved — one cross-context identity vs context-specific forms must be decided before SymbolDefinition implementation (G1) |
| A02 | Compressor | pfd | `symbol` | required | resolved | — | `deepplant-default` target | — | — | missing; equipment outline with process anchors | missing base SymbolDefinition |
| A03 | Heat-transfer equipment — heater, superheater, preheater, evaporator, exchanger (requirement family) | pfd + pid | `symbol` | required | **unresolved** | — | unresolved pending representation design | — | — | missing; a heat-transfer duty family must be representable, and one reusable identity vs several duty / equipment identities is not decided (G11) | representation identity unresolved — design decision required before SymbolDefinition implementation |
| A04 | Mixer (two or more process inlets) | pfd | `symbol` | required | resolved | — | `deepplant-default` target | — | — | missing; equipment outline with multiple process anchors | missing base SymbolDefinition |
| A05 | Reactor / burner | pfd | `symbol` | required | resolved | — | `deepplant-default` target | — | — | missing; equipment outline with anchored connections | missing base SymbolDefinition |
| A06 | Pump | pfd + pid | `symbol` | required | resolved | `generic-iso` | `deepplant-default` unresolved — focused review required before migration (#127) | ISO 10628-2:2012 | `candidate-alignment` | **implemented** (`pump.centrifugal`, `diagram_types = ("pfd", "pid")`); DeepPlant-authored project seed geometry ([symbol-seed-geometry.md](symbol-seed-geometry.md)) | — (geometry review before any notation-profile migration, per #127) |
| A07 | Vessel / tank / drum with nozzles (requirement family) | pfd + pid | `symbol` | required | **unresolved** | — | unresolved pending representation design | — | — | missing; a containment outline with nozzles, and one reusable identity vs separate vessel / tank / drum / column identities is not decided (G2) | representation identity unresolved — design decision required before SymbolDefinition implementation |
| A08 | Gate valve | pid | `symbol` | required | resolved | `generic-iso` | `deepplant-default` candidate — external recognizability unresolved (#127) | ISO 10628-2:2012 | `candidate-alignment` | **implemented** (`valve.gate`); DeepPlant-authored project seed geometry, with neutral `port_a` / `port_b` process anchors that embed no flow semantics | — (external recognizability and exact geometry unresolved, per #127) |
| A09 | Globe valve | pid | `symbol` | required | resolved | `deepplant-default` | `deepplant-default` | ISO 10628-2:2012 | `reference` | **implemented** (`valve.globe`); DeepPlant-authored project seed geometry (two-triangle body with a **solid** central-disc variant mark), with neutral `port_a` / `port_b` process anchors that embed no flow semantics | — (the representation records no standards relationship; the ISO column is concept-level reference direction only) |
| A10 | Check valve | pid | `symbol` | required | resolved | `deepplant-default` | `deepplant-default` | ISO 10628-2:2012 | `reference` | **implemented** (`valve.check`); DeepPlant-authored project seed geometry (rectangular body with a corner-to-corner closing stroke and a **solid** hinge mark) whose asymmetry is a recognizability mark only, with neutral `port_a` / `port_b` process anchors that embed no flow semantics | — (the representation records no standards relationship; the ISO column is concept-level reference direction only) |
| A11 | Ball valve | pid | `symbol` | required | resolved | `deepplant-default` | `deepplant-default` | ISO 10628-2:2012 | `reference` | **implemented** (`valve.ball`); DeepPlant-authored project seed geometry (two-triangle body with a large **hollow** central-circle variant mark), with neutral `port_a` / `port_b` process anchors that embed no flow semantics | — (the representation records no standards relationship; the ISO column is concept-level reference direction only) |
| A12 | Three-way valve | pid | `symbol` | required | resolved | — | `deepplant-default` target | — | — | missing; three-port valve body | missing base SymbolDefinition |
| A14 | Safety / relief valve (spring-loaded indication) | pid | `symbol` | required | resolved | — | `deepplant-default` target | ISO 10628-2:2012 | `reference` | missing; valve body with a spring-loaded indication | missing base SymbolDefinition |
| A15 | Restriction orifice | pid | `symbol` | required | resolved | `deepplant-default` | `deepplant-default` | — | — | **implemented** (`fitting.restriction_orifice`); DeepPlant-authored practical representation (two continuous outer transverse strokes framing a centred split restriction stroke, with no circle), with neutral `port_a` / `port_b` process anchors that embed no flow semantics; no tag or bore annotation is embedded | — (no standards relationship is recorded, and `—` is the absence of a recorded relationship, not a verification state) |
| A16 | Reducer (concentric / eccentric) | pid | `symbol` | required | resolved | — | `deepplant-default` target | ISO 10628-2:2012 | `reference` | missing; inline fitting on the piping axis | missing base SymbolDefinition |
| A17 | Instrument base graphic, field-mounted | pid | `symbol` | required | resolved | `generic-iso` | `deepplant-default` candidate — standards-specific composition unresolved (#124) | ISO 15519-2:2015 | `candidate-alignment` | **implemented** (`instrument.local`); DeepPlant-authored project seed geometry, with no function letters, tag, or mandatory signal anchor embedded | — (profile composition unresolved, #124) |
| A18 | Measurement sensor / primary element (inline on the process) (requirement family) | pid | `symbol` | required | **unresolved** | — | unresolved pending representation design | ISO 15519-2:2015 (measurement symbols) | `reference` | missing; a small measurement graphic, and one reusable identity vs one graphic per measured variable is not decided (G4) | representation identity unresolved — design decision required before SymbolDefinition implementation |

`Current profile` is `—` for every concept with no implemented representation, so
no future MVP concept inherits `generic-iso`. `Target MVP notation` states the
intended direction only (see
[Notation profile and target notation](#notation-profile-and-target-notation)) and
never claims an approved or implemented `deepplant-default` geometry. `Standards
relationship` and `Verification` are the separate evidence axis: `reference` is
reference direction only, never a correspondence claim.

The base-symbol identifier `A13` is retired. Earlier revisions counted a
standalone control-valve *body* identity here; the selected evidence requires a
**control valve** — the composed representation `B01` — and does not establish a
stable standalone identity named "control valve body", so the body requirement is
tracked with `B01` instead of as a resolved base symbol. Nothing is counted twice.

### 2. Composed representations (5)

| # | Concept | Context | Classification | Requirement | Current profile | Target MVP notation | Standards relationship | Verification | Current support | Gap type |
|---|---|---|---|---|---|---|---|---|---|---|
| B01 | Control valve with actuator (body composed with an actuator graphic) | pfd + pid | `composed-symbol` | required | not applicable | not applicable (composition; constituents carry notation) | ISO 10628-2:2012; ISO 15519-2:2015 (actuator conventions) | `reference` | missing; the body component is required, but the representation model that gives it a stable identity is not decided (G12) | composition gap; body identity a representation-design question |
| B02 | On/off actuated valve with position indication | pid | `composed-symbol` | required | not applicable | not applicable (composition; constituents carry notation) | — | — | missing | composition gap |
| B03 | Instrument function composition (base graphic + function letter code + loop designation) | pfd + pid | `composed-symbol` | required | not applicable | not applicable (composition; constituents carry notation) | ISO 15519-2:2015 (instrument identification) | `reference` | missing (the base graphic exists; the letter-code and loop-designation annotations do not) | composition gap |
| B04 | Control-system instrument variant (panel / shared display / control-system participation) | pid | `composed-symbol` | required | not applicable | not applicable (composition; constituents carry notation) | ISO 15519-2:2015 (reference direction) | `reference` | missing | composition gap |
| B05 | Safety-system instrument variant (instrument marked as part of the safety system) | pid | `composed-symbol` | required | not applicable | not applicable (composition; constituents carry notation) | — | — | missing | composition gap (the referenced logic is semantic gap F3) |

A composed representation is not itself a `SymbolDefinition`, so it carries neither
a current profile nor a notation profile of its own: `Current profile` and
`Target MVP notation` are both `not applicable (composition; constituents carry
notation)`, because the notation is carried by the base graphics the
representation composes. `deepplant-default` is never recorded for a composed
representation, and no approved geometry is claimed for one.


### 3. Connections (6)

| # | Concept | Context | Classification | Requirement | Current profile | Target MVP notation | Standards relationship | Verification | Current support | Gap type |
|---|---|---|---|---|---|---|---|---|---|---|
| C01 | Directional process stream | pfd | `connection` | required | not applicable | not applicable (connection style) | ISO 15519-2:2015 (connection conventions) | `reference` | implemented — drawn by the process renderer as output, not as a `SymbolDefinition` | — |
| C03 | Off-page connector (sheet-to-sheet continuation with a reference) | pfd + pid | `connection` | required | not applicable | not applicable (connection style) | — | — | missing | connection-rendering gap |
| C04 | Piping line — orthogonal routing, branch / junction, direction indication | pid | `connection` | required | not applicable | not applicable (connection style) | ISO 15519-2:2015 (connection conventions) | `reference` | missing (routing exists for process streams only) | connection-rendering gap |
| C05 | Instrument process connection (functional tap) | pid | `connection` | required | not applicable | not applicable (connection style) | — | — | partial — the `tap` anchor exists on `instrument.local`; the line convention does not | connection-rendering gap |
| C06 | Instrument signal line, electric | pid | `connection` | required | not applicable | not applicable (connection style) | ISO 15519-2:2015 (connection conventions) | `reference` | missing (signal lines must not become `Connection`) | connection-rendering gap |
| C07 | Line treatment — insulation, heating, tracing, as authored data | pid | `connection` (line treatment) | required as data; graphical decoration optional | not applicable | not applicable (connection style) | ISO 10628-1:2014 (diagram structure) | `reference` | missing (no authored carrier) | semantic-model gap (F5) |

C02 is deliberately **not** in this count: whether a labelled process boundary
connector is an annotation or a connection is unresolved, so it is counted in its
own [classification-unresolved capability class](#4-classification-unresolved-core-capability-1).
A connection style belongs to future presentation-profile architecture and is not a
`SymbolDefinition` notation profile today, so its target notation is `not
applicable (connection style)` rather than a fabricated profile.


### 4. Classification-unresolved Core capability (1)

Whether a labelled process boundary connector is an `annotation` or a `connection`
is representation-design question G10. The matrix records it in its own class
rather than forcing it into either one to preserve a total, keeping the
architectural truth: it is **not** equipment geometry, it is not a normal
standalone equipment `SymbolDefinition`, and its representation includes graphical
marker + label behaviour.

| # | Concept | Context | Classification | Requirement | Current profile | Target MVP notation | Standards relationship | Verification | Current support & representation | Gap type |
|---|---|---|---|---|---|---|---|---|---|---|
| C02 | Process boundary connector (battery limit, labelled) | pfd + pid | **unresolved** (annotation vs connection) | required | not applicable | unresolved pending representation design | — | — | missing; a marker plus a label associated with a boundary / stream endpoint, never equipment geometry | classification unresolved — which capability family owns a labelled boundary connector is representation-design question G10 |

### 5. Annotations (11)

| # | Concept | Context | Classification | Requirement | Current profile | Target MVP notation | Standards relationship | Verification | Current support | Gap type |
|---|---|---|---|---|---|---|---|---|---|---|
| D01 | Stream number label | pfd | `annotation` | required | not applicable | not applicable (authored text) | — | — | implemented — the renderer's label layer draws the process stream id | — |
| D02 | Stream property / composition data (medium, phase, flows, temperature, pressure, density, molecular weight, composition, duty) | pfd + pid | `annotation` | required as data; an automatic drawing table is optional | not applicable | not applicable (authored text) | — | — | missing | semantic-model gap (F1) |
| D03 | Equipment tag / name label (with the project equipment-code prefix) | pfd + pid | `annotation` | required | not applicable | not applicable (authored text) | — | — | partial — step id and name labels are drawn for process steps only | annotation gap |
| D04 | Duty / rating / set-point annotation (heat duty, relief set pressure) | pfd + pid | `annotation` | required | not applicable | not applicable (authored text) | — | — | missing | semantic-model gap (F6) |
| D05 | Nozzle designation | pid | `annotation` | required | not applicable | not applicable (authored text) | — | — | missing | annotation gap |
| D06 | Line tag (medium + sequence + nominal size + piping class) | pfd + pid | `annotation` | required | not applicable | not applicable (authored text) | — | — | missing (values are project conventions) | annotation gap |
| D07 | Instrument loop designation (function letters + loop number, with plant / location code) | pid | `annotation` | required | not applicable | not applicable (authored text) | ISO 15519-2:2015 (instrument identification) | `reference` | missing | semantic-model gap (F2) |
| D08 | Instrument alarm / limit annotation (high, high-high, low, low-low) | pid | `annotation` | required | not applicable | not applicable (authored text) | — | — | missing | annotation gap |
| D09 | Fail-state annotation (fail-closed / fail-open / fail-lock / normally-closed) | pfd + pid | `annotation` | required | not applicable | not applicable (authored text) | — | — | missing | annotation gap |
| D10 | Interlock / trip / permissive reference annotation | pid | `annotation` | required | not applicable | not applicable (authored text) | — | — | missing | annotation gap plus semantic-model gap (F3) |
| D11 | Drawing note / general note (authored text annotation) | pfd + pid | `annotation` | required | not applicable | not applicable (authored text) | — | — | missing | semantic-model gap (F4) |

An annotation is authored text, not a `SymbolDefinition`, so it carries no notation
profile today: its current profile is `not applicable` and its target notation is
`not applicable (authored text)`. A standards relationship is recorded only where
the earlier broad matrix already named one (`reference` direction only, never a
correspondence claim); every other annotation row carries `—` in the relationship
and verification columns, because no relationship is recorded for it.

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
| `fitting.restriction_orifice` | `symbol` | `deepplant-default` | `deepplant-original`, AGPL-3.0-only | — | — | `port_a` → west, process; `port_b` → east, process |

Everything else is reported per capability in
[MVP Core coverage](#mvp-core-coverage): each Core entry records its own support
state and gap type, and no identity-unresolved requirement family is counted as an
exact missing `SymbolDefinition`. See also the
[evidence document](../research/mvp-symbol-core-selection.md). No concept outside
these four is implemented, and no standards relationship is `human-verified`. All
four geometries are DeepPlant-authored project seed geometry
([symbol-seed-geometry.md](symbol-seed-geometry.md)), not derived from a standard's
artwork or from a company drawing. The three `generic-iso` representations are
recorded at `candidate-alignment` because the project intends them to correspond to
the named ISO family, with no human check claimed: because `generic-iso` *means*
that intended correspondence, a definition in that profile must record at least one
relationship at `candidate-alignment` or `human-verified`, and a bare `reference`
cannot carry the profile. The `deepplant-default` restriction orifice (A15)
records **no** standards relationship at all: `deepplant-default` makes no
ISO/ISA/PIP conformance claim, so none is required and none is invented
([symbol-library.md](symbol-library.md)).

The #127 profile classification for the three `generic-iso` definitions is
preserved unchanged, and keeps DeepPlant-default suitability apart from
standards-specific evidence:

```text
valve.gate
    current profile                  generic-iso
    deepplant-default                candidate; suitable on internal design grounds
    standards-specific               unresolved

pump.centrifugal
    current profile                  generic-iso
    deepplant-default                unresolved / insufficient evidence
    next                             focused review before migration

instrument.local
    current profile                  generic-iso
    deepplant-default                candidate; suitable
    standards-specific composition   unresolved under #124
```

## Unresolved questions

- Whether the three `generic-iso` DeepPlant-authored representations are close
  enough to the standards they name is open: those symbols are recorded at
  `candidate-alignment`, and any promotion to `human-verified` requires a human
  comparison against an authorized copy, recorded with the standard, the symbol,
  the date, and the verifier ([standards.md](../workflow/standards.md)).
  `candidate-alignment` itself requires no human check. The `deepplant-default`
  restriction orifice records no standards relationship at all, so no
  correspondence question is open for it.
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
- Whether each identity-unresolved requirement family — filter (A01), heat-transfer
  equipment (A03), vessel / tank / drum (A07), measurement sensor / primary element
  (A18) — maps to one stable `SymbolDefinition` or to several, whether a concept
  required in both the PFD and the P&ID has one cross-context identity or
  context-specific forms (A01, A03, A07), and which representation model gives the
  control-valve body a stable identity (B01), are unresolved; the specific
  questions are recorded as representation-design questions G1, G2, G4, G11 and G12
  in the [evidence document](../research/mvp-symbol-core-selection.md).
- Whether the labelled process boundary connector (C02) is an `annotation` or a
  `connection` is unresolved, so the row is counted in its own
  classification-unresolved capability class rather than in the connection total;
  the question is recorded as representation-design question G10 in the
  [evidence document](../research/mvp-symbol-core-selection.md).
- Whether an unimplemented Core concept's `Target MVP notation` should become a
  concrete `deepplant-default` representation — and how that profile is selected
  and persisted — is unresolved and owned by Issue #124; the matrix records the
  direction only, never an approved geometry.
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
  built-in geometries are authored from.
- [svg-symbols.md](svg-symbols.md) — the separate, DeepPlant-original process
  symbol-pack and anchor contract.
- [../workflow/standards.md](../workflow/standards.md) and
  [standards-registry.md](standards-registry.md) — standards usage policy and
  the project reference set.
- [../research/mvp-symbol-core-selection.md](../research/mvp-symbol-core-selection.md)
  — the evidence behind the MVP Core selection named above.
- [../research/standards-licensing-evidence.md](../research/standards-licensing-evidence.md)
  — the source and licence investigation behind those rules.

