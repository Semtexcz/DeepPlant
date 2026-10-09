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
  - DeepPlant MVP drawing support profile v0.1 (private reference bundle)
superseded_by: null
---

# MVP Core graphical vocabulary selection

## Outcome card

- **Question investigated:** which concrete graphical vocabulary — base symbols,
  composites, connections, annotations, and project conventions — must the MVP be
  able to draw, given the operator-authored MVP drawing profile and the private
  reference set it was derived from?
- **Status:** closed evidence. The selection is bounded and reproducible from
  material already recorded in the repository plus one operator-selected private
  reference set; it establishes *what is in the MVP Core*, not how any of it is
  drawn.
- **Scope of investigation:** the DeepPlant-authored MVP drawing profile v0.1,
  the operator-selected private MVP reference set (one PFD sheet, one P&ID sheet,
  its two legend sheets, and the stretch P&ID sheet), and the DeepPlant-authored
  repository material listed under [Sources](#sources). Assessed on **2026-10-09**.
  No restricted ISO/ISA/IEC content was inspected, and no standards locator,
  figure, table, or item number is recorded.
- **Conclusions:**
  - The MVP Core is a **vocabulary subset, not a standards implementation**: the
    profile deliberately selects "the smallest semantically correct drawing subset"
    for the two golden scenes, and everything else in the reference set is
    *evidenced but deliberately outside the Core*.
  - The Core spans **five partitions** — base symbols, composites, connections,
    annotations, and project conventions — and each entry carries exactly one
    [coverage-matrix](../reference/mvp-symbol-coverage.md) classification.
  - **28 selected Core entries** are recorded below; **three** exist as
    `SymbolDefinition`s today (`valve.gate`, `pump.centrifugal`,
    `instrument.local`). The remaining 25 are `planned`, `deferred`, or
    deliberately `out of the base library`.
  - The reference set is **richer than the Core in every partition** (duty/standby
    pumps, interlocks and trip diamonds, voting, specialty valves, alarm states,
    title block and revision table). That gap is the scoping decision, and it is
    recorded as *excluded*, not as an oversight.
  - The three implemented representations keep the classification given them by
    [notation-profile-classification.md](notation-profile-classification.md):
    `valve.gate` and `instrument.local` are `deepplant-default` candidates;
    `pump.centrifugal` stays `REVIEW_BEFORE_MIGRATION / INSUFFICIENT_EVIDENCE`.
    **This document changes neither the profile assignment nor the geometry.**
- **Resulting decision:** none in production code. The selection is scope
  evidence for the [coverage matrix](../reference/mvp-symbol-coverage.md), which
  now names the MVP Core explicitly.
- **Conditions for revisiting:** the profile is approved or revised
  (its status is currently `proposed`); the active milestone changes; a Core
  concept's implementation changes; or a new reference set is supplied.

**This document owns no current rule and implements no symbol.** It records what
was selected and why. The rendering contract stays
[symbol-library.md](../reference/symbol-library.md); per-concept status stays
[mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md).

## Research question

> Which concrete graphical vocabulary must the MVP be able to draw, and which
> parts of the inspected reference set are deliberately outside it?

This is the scoping half of Issue #119. The coverage matrix answers *how far each
concept has been implemented*; this document answers *which concepts the MVP Core
contains at all*.

```text
reference set            what the operator's production drawings contain
MVP drawing profile      the deliberate subset selected from them  (authoritative)
MVP Core (this document) the vocabulary that subset needs
coverage matrix          per-concept classification and status
catalogue.py             the three representations implemented so far
```

## Scope and method

Two inputs, with deliberately unequal authority:

| Input | Authority | Used for |
|---|---|---|
| *DeepPlant MVP drawing support profile v0.1* (operator-authored, `proposed`) | **authoritative scope** | what the MVP Core contains |
| Operator-selected private MVP reference set | **usage evidence only** | confirming that each selected concept is actually used in production drawings, and bounding what is excluded |

The profile is the scoping instrument. The reference set is never used to *add* a
concept to the Core; it may only confirm a Core entry or evidence an exclusion.
Where the reference set contains more than the profile requires, the profile
wins and the extra content is recorded as out of scope.

```text
profile says "required"          → Core entry
profile says "nice-to-have"      → Core entry, after the golden scene
profile says "out of scope"      → excluded, with the reference-set usage noted
profile is silent, set uses it   → excluded, recorded as an evidence gap
```

## Reference material handling

The reference set is a private company bundle, selected by the operator for MVP
scoping. It is **never a source of geometry**, and it is not redistributed:

- Nothing from it is committed, quoted, traced, vectorised, or measured. No
  symbol artwork, layout, title block, revision table, equipment data block, note
  text, tag value, line-tag value, or symbol-sheet item is reproduced here or in
  the repository.
- Only **concept-level vocabulary** is recorded: generic engineering concepts
  ("gate valve", "centrifugal pump", "off-page connector") that the repository
  already names. The sheets name standard families; **no standard locator, figure
  reference, table number, or item number observed on them is recorded**, because
  only a permitted source or a recorded human verification may supply that
  ([standards.md](../workflow/standards.md), ADR-0007).
- The three implemented geometries remain DeepPlant-authored project seed
  geometry ([symbol-seed-geometry.md](../reference/symbol-seed-geometry.md)). No
  geometry was derived from this bundle before or after this inspection.

```text
used as      scoping and usage evidence (does the concept occur in production?)
not used as  geometry, locator, naming, layout, or compliance evidence
```

## Inspected evidence

| Source | Role | Inspected for |
|---|---|---|
| *DeepPlant MVP drawing support profile v0.1* | authoritative scope | required / optional / out-of-scope vocabulary per section 1–5 |
| PFD reference sheet (`AMMONIA BURNING`) | usage evidence | PFD step kinds, boundaries, stream labels, tag presentation |
| P&ID reference sheet (`PROCESS WATER`) | usage evidence | equipment, inline components, nozzles, loop topology, line tags |
| P&ID legend sheet (piping elements) | usage evidence | the piping-component and line-treatment vocabulary actually used |
| P&ID legend sheet (instrumentation and control) | usage evidence | instrument functions, signal lines, control-system participation |
| Stretch P&ID sheet (`AMMONIA EVAPORATION I`) | usage evidence | the complexity gate's vocabulary, at concept level only |
| [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md), [symbol-library.md](../reference/symbol-library.md), [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md), [notation-profile-classification.md](notation-profile-classification.md) | repository evidence | classification vocabulary, per-concept status, the three implemented definitions, the current profile classification |

Read-only inspection also covered
[catalogue.py](../../../src/deepplant/symbols/catalogue.py) and
[profiles.py](../../../src/deepplant/symbols/profiles.py) to confirm that exactly
three representations exist and that their `notation_profile` is `generic-iso`.

## Observed reference-set vocabulary (concept level)

Recorded so the Core selection can be read against real production usage. This is
a *superset* of the Core; nothing here is added to the Core by being observed.

| Partition | Observed in the reference set |
|---|---|
| PFD process representations | filter, compressor, air heater / heat exchanger, mixer, reactor / burner, pump, tank / hold-up, boundary connectors, stream labels, equipment data blocks |
| P&ID equipment | vertical vessel / tank with lettered nozzles, centrifugal pumps in parallel, filters / strainers, heat exchangers, separator, ejector, scrubber, expansion joint |
| P&ID inline components | gate valve, globe valve, ball valve, check valve, control valve with actuator, restriction orifice, pressure / temperature relief valve, relief and vacuum / breath valves, steam trap, automatic vent valve, flame arrestor, sight glass, spectacles / blinds, caps / plugs, flanges, funnel / drain |
| Instrumentation | pressure, temperature, level, and flow indicators, transmitters, controllers, and control-valve functions; primary flow element; level gauges; panel and DCS instruments; alarms (high / high-high / low / low-low); trip and interlock references; voting |
| Connections | process piping lines with authored line tags, branches and junctions, off-page connectors between sheets, electrical signal lines, instrument functional taps, line treatment (insulation, heat conservation, tracing) |
| Annotations | equipment tags with type letters, lettered nozzle designations, line tags, instrument loop designations, notes, drawing frames, title block and revision table |

Two findings matter for scoping:

```text
1. the reference set contains control and safety functions the MVP does not
   require (PIC/TIC-style loops, relief-device philosophy, voting, interlocks)
2. the reference set contains layout, tag, and code data that is project-owned
   and that the MVP must not embed in symbol geometry
```

Both are consistent with the profile's own exclusions (section 1.4, 2.6, 3, 5)
and with the coverage matrix's rule that company conventions are recorded as
`project-convention`.

## The MVP Core vocabulary

Five partitions, one table each. Column meanings:

```text
Core        core            the profile requires it for MVP acceptance
            core-optional   the profile allows it "if already cheap" / nice-to-have
            excluded        the profile or an evidence gap keeps it out of the Core
Observed    yes / partial / —   whether the inspected reference set uses the concept
Implemented the current DeepPlant implementation state, from mvp-symbol-coverage.md
```

Classification values are exactly the coverage matrix's vocabulary; every row
below also has (or gains) a row there.

### 1. Base symbols — PFD process representations

| Concept | Classification | Core | Observed | Implemented |
|---|---|---|---|---|
| Filter | `symbol` | core | yes | planned |
| Compressor | `symbol` | core | yes | planned |
| Heater / heat exchanger (PFD step form) | `symbol` | core | yes | planned |
| Mixer, two or more inlets | `symbol` | core | yes | planned |
| Reactor / burner | `symbol` | core | yes | planned |
| Pump (PFD step form) | `symbol` | core-optional | yes | planned — not the same representation as `pump.centrifugal` |
| Storage / hold-up tank (PFD step form) | `symbol` | core-optional | yes | planned |

### 2. Base symbols — P&ID equipment and inline components

| Concept | Classification | Core | Observed | Implemented |
|---|---|---|---|---|
| Vertical vessel / tank with nozzles | `symbol` | core | yes | planned |
| Centrifugal pump | `symbol` | core | yes | **implemented** (`pump.centrifugal`) |
| Gate valve | `symbol` | core | yes | **implemented** (`valve.gate`) |
| Globe valve | `symbol` | core | yes | planned |
| Check valve | `symbol` | core | yes | planned |
| Restriction orifice | `symbol` | core | yes | planned |
| Pressure / relief valve | `symbol` | core | yes | planned |
| Filter / strainer | `symbol` | core-optional (after the golden scene) | yes | planned |
| Heat exchanger | `symbol` | core-optional (after the golden scene) | yes | planned |
| Ball / needle / other specialty valve | `symbol` | excluded (profile requires only the five above) | yes | deferred — PR #123 concepts stay unmerged |

### 3. Composed symbols

| Concept | Classification | Core | Observed | Implemented |
|---|---|---|---|---|
| Control valve with actuator | `composed-symbol` | core | yes | planned — composition framework deferred |
| Local / field instrument base graphic | `symbol` | core | yes | **implemented** (`instrument.local`) |
| Instrument function letter code composed onto the base graphic | `annotation` | core | yes | planned — text, never one symbol per code |
| Measurement sensor / primary element | `symbol` | core | yes | planned |
| Panel / central instrument | `symbol` | core-optional (after the golden scene) | yes | planned |
| Instrument with integrated display, multifunction instrument | `composed-symbol` | excluded (profile: optional) | yes | deferred |
| Alarm, trip, voting and fail-state indication | `annotation` | excluded (stretch profile only) | yes | deferred |
| DCS / SIS participation | `project-convention` | excluded from the base library | yes | out of the base library |

### 4. Connections

| Concept | Classification | Core | Observed | Implemented |
|---|---|---|---|---|
| Directional process stream | `connection` | core | yes | already drawn by the process renderer as output |
| Process boundary connector | `annotation` (boundary) | core | yes | planned — marker plus label, never equipment geometry |
| Piping line with orthogonal routing, branch / junction, direction | `connection` | core | yes | planned |
| Off-page connector | `connection` | core | yes | planned |
| Signal / instrument connection line (electric) | `connection` | core | yes | planned |
| Instrument process connection (functional tap) | `connection` | core | yes | implemented as the `tap` anchor of `instrument.local`; the line convention is planned |
| Insulation / heat-tracing line treatment | `connection` (line treatment) | core as authored property, excluded as graphical decoration | yes | planned as data |

### 5. Annotations

| Concept | Classification | Core | Observed | Implemented |
|---|---|---|---|---|
| Stream number label | `annotation` | core | yes | planned — text, never geometry |
| Stream property values (medium, phase, flow, T, P) | `annotation` | core — rendered in the Properties panel, not as a drawing table | yes | planned |
| Equipment tag / label | `annotation` | core | yes | planned — text, never geometry |
| Nozzle designation | `annotation` | core | yes | planned — text, never geometry |
| Line tag (medium + sequence + nominal size + piping class) | `annotation` | core — stored semantically | yes | planned |
| Instrument loop designation | `annotation` | core | yes | planned — text, never geometry |
| Automatic stream property table | `annotation` | excluded for v0.1 | yes | deferred |
| General notes block | `annotation` | excluded (not required by the profile) | yes | deferred — an evidence gap, see below |
| Corporate title block, revision table, drawing frame | `annotation` | excluded for v0.1 | yes | deferred |

### Project conventions (deliberately not a symbol library)

| Convention | Classification | Handling |
|---|---|---|
| Equipment and valve tag prefix rules | `project-convention` | Tag text is composed by the project; never embedded in base geometry. |
| Fluid / medium code list | `project-convention` | Values are authored data; the code list itself is not a DeepPlant vocabulary. |
| Line-number and line-designation rules | `project-convention` | Authoring and validation concern outside the symbol library. |
| Insulation, tracing and piping-class codes | `project-convention` | Values are authored data; geometry carries only the decoration. |
| DCS / SIS conventions, interlock / trip / SIF numbering | `project-convention` | Company-specific; excluded from the base library. |
| Composite project typicals | `composite-typical` | Resolution of a typical reference is deferred entirely. |
| Corporate title block, revision table and drawing frames | `project-convention` | Out of scope for v0.1; not a symbol-library concern. |

Every partition shows the same pattern: the Core keeps **one representation per
engineering concept**, and every project-specific code, tag, or numbering scheme
stays *data*, exactly as the coverage matrix already requires.

## Selection summary

```text
28 Core entries across five partitions
    5  PFD process representations
    7  P&ID base symbols            (2 equipment + 5 inline)
    4  composed / instrument entries
    6  connections                  (+1 Core-as-property line treatment)
    6  annotations
   --  project conventions          not Core entries (7 recorded)

recorded but outside the Core
    5  core-optional entries        (2 PFD, 2 P&ID equipment, 1 instrument)
    7  excluded entries             (1 specialty valve, 3 composite/instrument,
                                     3 annotation)
    7  project conventions           never base-library assets

 3 implemented as SymbolDefinitions
    valve.gate, pump.centrifugal, instrument.local
25 Core entries planned / deferred / out of the base library
```

The Core is closed for MVP acceptance purposes: adding a concept to it requires a
profile change, not a symbol implementation.

## Relationship to the three implemented representations

| Symbol | Keeps the classification from #127 | MVP Core role |
|---|---|---|
| `valve.gate` | `deepplant-default` candidate (internal design grounds) | the Core's on/off isolation base symbol |
| `pump.centrifugal` | `REVIEW_BEFORE_MIGRATION / INSUFFICIENT_EVIDENCE` | the Core's pumping equipment base symbol |
| `instrument.local` | `deepplant-default` candidate | the Core's reusable instrument base graphic |

Three properties of these definitions are load-bearing for the Core and are not
reopened here:

- the valve's anchors are notation-independent (`port_a` / `port_b`), so the same
  definition serves isolation, throttling, and check-duty bodies as variants
  rather than new symbols;
- the pump's `suction` / `discharge` anchors are engineering names for a pump,
  with anchor geometry recording only where a line leaves the symbol;
- the instrument base graphic deliberately carries **no** function letters, tag,
  and no mandatory signal anchor, because letter composition and signal
  connections belong to composition, not to the base graphic.

```text
this document    selects vocabulary        no production change
#127             classifies profiles       no production change
#124 / #125      own profile architecture  separate scope
```

## Explicit non-goals

- No symbol is implemented, redesigned, or re-anchored by this document.
- No `notation_profile` assignment changes; `generic-iso` stays the transitional
  profile for all three definitions.
- No geometry is authored, adjusted, or measured — and none is taken from the
  reference set.
- No standard is claimed, no locator recorded, and no compliance inferred from
  visual similarity ([standards.md](../workflow/standards.md)).
- No project-specific value (tag, line number, note, code, title block field)
  becomes part of DeepPlant's vocabulary; those stay authored data.

## Evidence gaps and unresolved questions

- **The profile is `proposed`, not approved.** The MVP Core in this document
  inherits that status: it is the selection the profile implies, and a profile
  revision changes it. Nothing here approves the profile.
- **The general notes block is a scoping gap.** The reference sheets carry general
  notes and the profile neither requires nor excludes them; they are recorded as
  excluded-not-required rather than silently dropped.
- **Construction details are a deliberate gap.** Weld, flange, cap/plug, funnel
  and drain symbols occur in the reference set but appear in neither the MVP
  requirements nor the stretch list. Their exclusion is recorded, not decided.
- **Whether a driver / energy anchor belongs on the pump symbol** stays open
  (same question as the coverage matrix's unresolved list).
- **How a control valve's actuator composition is modelled** (variant of a valve
  body, or a separate actuator graphic composed at render time) is not settled by
  this selection; the profile requires only that the semantic subtype remain
  explicit.
- **Which annotation family the boundary connector belongs to** is recorded here
  as `annotation` per the coverage matrix, while it is arguably a connection
  convention. The matrix stays authoritative.
- **The stretch vocabulary is scoped, not designed.** Section 3 of the profile
  lists the complexity gate's capabilities; this document confirms that they are
  outside the Core and does not decide their representation.

## Recommended follow-up slices

Research recommendations, **not** created Issues, and **not** implementation
authorization. Each requires its own separately scoped and Ready Issue.

| # | Slice | Category | Depends on |
|---|---|---|---|
| 1 | Approve or revise the MVP drawing profile so the Core stops being `proposed` | A — scope | operator decision |
| 2 | Implement the P&ID golden-scene base symbols from the Core (vessel/tank with nozzles, gate/globe/check valve, restriction orifice, relief valve), one small slice each | B — Core implementation | 1; existing symbol contract |
| 3 | Implement the PFD step representations the process model needs, keeping `ProcessStep` distinct from `Equipment` | C — Core implementation | 1; [contracts/process-model.md](../../contracts/process-model.md) |
| 4 | Deliver composition machinery (letter-code composition, signal anchors, control valve with actuator) | D — composition | 2, 3 |
| 5 | Focused review of `pump.centrifugal` geometry, per the [notation-profile classification](notation-profile-classification.md) | E — review before migration | — |
| 6 | Make the coverage matrix profile-aware and tag each row with its MVP Core status | F — matrix | 1; #124 |

Explicitly not recommended: creating these Issues automatically, or expanding the
Core by observing the reference set.

## Sources

### Repository-authored evidence actually used

- [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md) — classification
  vocabulary, per-concept status, and the reference-material handling rules.
- [symbol-library.md](../reference/symbol-library.md) — the symbol contract and
  the three implemented representations.
- [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) — the
  DeepPlant-owned geometry spec the three definitions are authored from.
- [notation-profile-classification.md](notation-profile-classification.md) — the
  current profile classification, preserved unchanged.
- [standards.md](../workflow/standards.md),
  [standards-registry.md](../reference/standards-registry.md) — standards usage
  and provenance policy.
- [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md),
  [ADR-0017](../decisions/ADR-0017-machine-rendered-symbol-definitions.md).
- [catalogue.py](../../../src/deepplant/symbols/catalogue.py) and
  [profiles.py](../../../src/deepplant/symbols/profiles.py) — read-only
  confirmation of the implemented catalogue and profile vocabulary.
- Issues #119, #123, #124, #127 — scoping context.

### Private reference set actually inspected (usage evidence only)

Listed by role, not by content. The bundle is not committed, and no artwork,
locator, item number, layout, tag, code, or note text from it is reproduced here.

```text
DeepPlant MVP drawing support profile v0.1     operator-authored scope
PFD reference (one sheet)                      process-side usage
P&ID reference (one sheet + two legend sheets) physical + instrumentation usage
P&ID stretch reference (one sheet)             complexity-gate usage
```

### External AI-usable material actually inspected

None. No external source was used as evidence: no restricted ISO/ISA/IEC content
was inspected, and the reference set is company-private material used only for
scoping and usage confirmation.

## Related

- [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md) — the per-concept
  matrix; the MVP Core named there is derived from this document.
- [symbol-library.md](../reference/symbol-library.md) — the rendering contract and
  the three implemented definitions.
- [notation-profile-classification.md](notation-profile-classification.md) — the
  profile classification this selection preserves.
- [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) — the geometry
  spec for the three implemented representations.
- [standards-licensing-evidence.md](standards-licensing-evidence.md) — why the
  reference set may inform scope but never supply geometry or standard detail.
