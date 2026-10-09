---
type: evidence
status: active
canonical_for:
  - notation-profile-classification-evidence
read_when:
  - symbol-asset-work
  - standards-alignment-claim
  - notation-profile-change
update_when:
  - new-source-inspection
  - classification-change
  - symbol-redesign
depends_on:
  - docs/dev/reference/symbol-library.md
  - docs/dev/reference/mvp-symbol-coverage.md
  - docs/dev/reference/symbol-seed-geometry.md
  - docs/dev/workflow/standards.md
  - docs/dev/reference/standards-registry.md
decision:
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0007-standards-and-symbol-provenance.md
  - docs/dev/decisions/ADR-0017-machine-rendered-symbol-definitions.md
evidence: []
superseded_by: null
---

# Current `generic-iso` notation classification

## Outcome card

- **Question investigated:** Which notation profiles, if any, should the three
  currently implemented `generic-iso` representations (`valve.gate`,
  `pump.centrifugal`, `instrument.local`) migrate to, based on the evidence
  currently available?
- **Status:** open evidence — the public sources establish the notation
  landscape and the standards *families*, but not the concrete normative
  geometry of any symbol. The result is a classification and a set of bounded
  next slices, not a migration.
- **Scope of investigation:** public sources only, retrieved on **2026-10-09**.
  No private, licensed, or restricted standards material (ISO/IEC/ISA figures,
  the private reference bundle, company drawings, or any local private-reference
  directory) was opened, searched, or read. No third-party artwork was copied.
- **Conclusions:**
  - `valve.gate` — suitable for `deepplant-default`; the ISO equipment-symbol
    family is relevant, but the exact ISO geometry is **unresolved**.
  - `pump.centrifugal` — the current internal construction is an idiosyncratic
    simplification; recommend **redesign before migration**, then
    `deepplant-default`. Exact ISO geometry is **unresolved**.
  - `instrument.local` — suitable for `deepplant-default`; its standards-specific
    family is **instrumentation** (ISO 15519-2 / ISA-5.1), **not** `iso-10628`.
  - The planned `deepplant-default + iso-10628` model is **too coarse for the
    current three symbols**: it is sufficient for mechanical/equipment symbols
    but not for instrumentation. Profile family naming should be reconsidered
    (section [Profile-architecture implications](#profile-architecture-implications)).
  - The existing `candidate-alignment` records remain **well-supported as intent
    records** and require no change; they are **not** evidence of conformance.
- **Resulting decision:** none. This is evidence supporting a future
  architecture/implementation decision under Issue #124; it does not itself
  change any production state.
- **Conditions for revisiting:** a `deepplant-default` migration is scheduled; a
  standards-specific profile is introduced; a human verification against an
  authorized standard copy is recorded; or the catalogue changes materially.

**This document does not own current rules and does not authorize a migration.**
It records what was investigated and found. Which profile a representation
belongs to is decided by [profiles.py](../../../src/deepplant/symbols/profiles.py)
and the migration authorized by Issue #124; the symbol contract is
[symbol-library.md](../reference/symbol-library.md).

## Research question

> Which notation profiles, if any, should the three currently implemented
> `generic-iso` representations migrate to, based on the evidence currently
> available?

This is answered independently for each symbol as two separate questions
(Issue #127):

```text
1. Is the current geometry a good representation for DeepPlant's own default
   practical notation (deepplant-default)?
2. Is there sufficient evidence to recommend this exact geometry for a
   standards-specific profile (e.g. a future iso-10628)?
```

The two answers are deliberately not collapsed. A representation may be a good
DeepPlant default while its standards correspondence stays unresolved.

## Scope

In scope: the three built-in representations merged into `main`:

```text
valve.gate
pump.centrifugal
instrument.local
```

Out of scope: every other concept, and specifically the representations that
exist only in the frozen PR #123:

```text
valve.ball
valve.check
fitting.reducer
```

PR #123 was treated as read-only and its geometry was **not** used as evidence
for the merged catalogue. This document performs **no** migration: no production
Python symbol code, no profile assignment, no anchor, no geometry, no SVG, and
no standards-verification state was changed.

## Architectural baseline

Issue #125 established the notation-profile architecture this classification is
written against:

```text
symbol_id              stable, notation-independent identity (valve.gate)
notation_profile       presentation-layer notation selection
representation         (notation_profile, symbol_id)
```

The recognised profiles are exactly two
([profiles.py](../../../src/deepplant/symbols/profiles.py)):

| Profile | Meaning | Standards relationship |
|---|---|---|
| `deepplant-default` | DeepPlant-owned practical notation, the future product default (Issue #124) | **optional** — no ISO/ISA/PIP conformance claim is made |
| `generic-iso` | the transitional profile the current catalogue was authored in | **required** — the profile *means* intended standards correspondence, so at least one `StandardsReference` at `candidate-alignment`/`human-verified` is mandatory |

All three built-in representations remain `generic-iso` by design. That label is
transitional, and it currently **conflates two questions that must be separated**:
is this geometry a good DeepPlant default, and is there evidence for standards
correspondence. The current metadata does not answer either question by itself:

```text
StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment")
    records    an intended relationship
    does not   prove any graphical correspondence
    does not   mean human-verified or conformant
```

`candidate-alignment` means only *the project intends correspondence*. It is not
independent evidence of graphical correspondence, and this document does not
treat it as such.

## Evidence method and confidence

Claims are graded by the kind of source behind them, not by a single score, so
that "the standard is relevant" is never confused with "the exact geometry
matches".

| Tier | Source kind | May support |
|---|---|---|
| 1 | public **primary** sources (ISO/ISA catalogue and scope pages, official vendor documentation, the PIP organisation) | the scope of a standard, terminology, which notation standards a product exposes, whether multiple symbol standards/profiles are normal |
| 2 | reputable public **engineering references** (standards resellers reproducing official abstracts; engineering reference sites) | "this is a common P&ID representation"; a secondary relationship between standards |
| 3 | **community/tertiary** sources (encyclopaedias) | general context only; never the basis of a standards classification |

Two architectural limits shaped the method:

- **Primary scope pages do not expose normative geometry.** An official catalogue
  entry says what a standard *covers*; it never shows the exact glyph. Public
  primary sources therefore cannot verify that DeepPlant's primitives match a
  standard, and this document never claims that they do.
- **The restricted copies must not be read by an agent.** ISO/IEC/ISA content is
  restricted; ISA's own current policy page states that ISA prohibits entering
  ISA intellectual property into AI tools. No restricted figure, table, or text
  was inspected. Where the exact geometry would require an authorized copy, the
  result is recorded as `unresolved` / `insufficient evidence`.

Confidence is reported **separately** for three distinct questions:

```text
common-industry evidence        is the broad form a recognisable industry convention?
standards-family evidence       is the target standards family correct?
exact standards-geometry        is this exact geometry evidenced for that standard?
```

The third is answered `low` for every symbol here, because the normative
geometry is not public and must not be read from a restricted copy by an agent.
That is a result, not a failure.

`iso.org` blocks automated retrieval (the catalogue pages returned HTTP 403 on
every attempt on 2026-10-09), which matches the standing note in the
[standards registry](../reference/standards-registry.md). The official abstract
text below was therefore taken from the catalogue entry as reproduced by several
independent resellers, and the identifiers must be re-verified by a human on the
official catalogue before any compliance-sensitive claim.

## Standards / notation landscape

The current three symbols cannot be classified against a single standard,
because the process-diagram standards layer rather than compete: one family
governs the diagram and its equipment/piping glyphs, another governs
instrumentation, measurement, and control.

| Family | Document(s) | Scope (public abstract) | Relevance here |
|---|---|---|---|
| Process-diagram structure | ISO 10628-1:2014 | "specifies the classification, content, and representation of flow diagrams" plus drafting rules; an application standard of ISO 15519; not for electrical diagrams | diagram structure, not symbol geometry |
| Process/equipment graphical symbols | ISO 10628-2:2012 | "defines graphical symbols for the preparation of diagrams for the chemical and petrochemical industry"; a "collective application standard of the ISO 14617 series"; not for electrotechnical diagrams (→ IEC 60617) | the family behind `valve.gate` and `pump.centrifugal` |
| Base graphic-symbol library | ISO 14617 series (e.g. -1:2025 General rules; -2:2025 Graphical symbols) | base library of graphical symbols for diagrams related to industrial components, products and processing; the 2025 revision notes that letter codes moved to ISO 15519-2 | the "library" ISO 10628-2 applies |
| Process-industry diagram rules | ISO 15519-1:2010 (General rules) | general rules for process-industry diagrams | diagram-level rules |
| Measurement, control, actuation | ISO 15519-2:2015 | "provides rules and guidelines for representation of measurement, control, and actuation in diagrams for process industry"; covers PFD/P&ID/PCD/TYD; carries the letter codes for process control information (moved from ISO 14617-6) | the family behind `instrument.local` |
| Instrumentation symbols and identification | ANSI/ISA-5.1-2024 | "a uniform means of designating instruments and instrumentation systems used for measurement and control … includes symbols and an identification code"; the 2024 title added "*and Control*"; companion technical reports ISA-TR5.1.02/-.03-2024 | the instrumentation identification system (letters, bubbles, lines) |
| Practical EPC/owner practice | Process Industry Practices (PIP) | a consortium "dedicated to harmonizing internal company standards and practices" — 600+ practices across 14 disciplines | the project/company conventions layer, not a base notation |
| Commercial CAD libraries | Autodesk, Siemens, AVEVA | project/configurable symbol libraries (see next section) | proof that symbol appearance is configuration, not one universal notation |

**Correction to the working assumption.** The prompt's initial grouping — ISO
10628/14617 (equipment/piping), ISO 15519 (process-industry diagram rules *and*
instrumentation), ISA-5.1 (instrumentation), PIP (practical documentation),
commercial libraries (configurable profiles) — is broadly correct with one
material refinement: **ISO 10628-2 excludes instrumentation itself and applies
ISO 14617 as its library, while measurement/control representation is owned by
ISO 15519-2** (with the ISA-5.1 / IEC 62424 family in practice). Instrumentation
therefore does **not** naturally belong under an `iso-10628` profile.

## Industry and CAD implementation evidence

This evidence is architectural and contextual: it shows that treating symbol
appearance as a selectable notation/profile is normal industry practice. It does
**not** establish that DeepPlant's geometry matches any standard.

- **Autodesk (AutoCAD P&ID / Plant 3D)** — the official *AutoCAD P&ID 2011
  Getting Started* guide states that a P&ID workspace "displays interface
  elements that are particular to both that **symbol standard** and to the P&ID
  program", names the **PIP** workspace as the default, and refers to the
  **DIN** and **P&ID JIS/ISO** workspaces. Read together with the standard
  Plant 3D project/workspace setup this supports: *the P&ID symbol standard is a
  project-selectable configuration, and several standards coexist.*
- **Siemens (COMOS Process P&ID)** — the official COMOS P&ID documentation states
  that "COMOS is supplied with a comprehensive library of preconfigured P&ID
  objects" and includes document/object libraries "acc. to IEC 61355". Supports:
  *P&ID appearance comes from a configurable object library, not a single fixed
  notation.*
- **Process Industry Practices (PIP)** — the official site describes PIP as a
  consortium "dedicated to harmonizing internal company standards and practices"
  with 600+ practices across 14 engineering disciplines. Supports: *PIP is a
  practical project/company convention set layered on top of base standards, not
  itself a base symbol notation.*
- **Relationship between the families (secondary)** — an engineering reference
  states that ISO 10628 and ISA-5.1 "layer rather than compete": ISO 10628
  governs the diagram and its equipment symbols while ISA-5.1 governs the
  instrument tags and symbols on it, and ISO 10628 defines no tagging method of
  its own. This is a **secondary** characterisation (retrieved as a
  search-result summary; the page returned 404 on direct fetch), consistent with
  the primary scope pages above, and is treated as corroboration, not proof.

The convergent finding is:

```text
one diagram can combine an equipment/piping notation family
with a separate instrumentation/control notation family,
and a project selects its symbol library/standard
```

which is exactly why a single `iso-10628` profile cannot honestly hold all three
current symbols.

## `valve.gate`

### Existing DeepPlant geometry

Described from DeepPlant's own sources only
([symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) seed A and
[catalogue.py](../../../src/deepplant/symbols/catalogue.py)):

- a **horizontal process axis** at the vertical centre;
- two **opposed triangular halves meeting apex-to-apex** (a "bow-tie"/butterfly
  body) forming the valve body — left triangle points right, right triangle
  points left, tips meeting at the centre;
- **no centre mark**, no stem, no handwheel, and no gate line;
- two short **stubs** to the view-box edges, which are DeepPlant's connection
  representation of the adjacent pipeline (a presentation choice, not the body);
- anchors `port_a` (west, process) and `port_b` (east, process).

### Public evidence

- The process-diagram standards list `valve`/`gate valve` among the equipment
  symbols represented under **ISO 10628-2 / ISO 14617** (tertiary encyclopaedic
  listing under those families; the ISO scope page confirms the family covers
  chemical/petrochemical diagram symbols).
- The **opposed-triangle/valve body** is a long-recognised generic valve glyph in
  process-industry references. This is **common-industry** evidence (Tier 2/3),
  not normative evidence of the concrete DeepPlant primitives.
- No **public primary** source exposes the standard's normative gate-valve
  geometry, so exact construction cannot be verified publicly, and it must not
  be read from a restricted copy.

### DeepPlant-default suitability

**Suitable — high confidence.** The glyph is recognisable, simple, fully
machine-renderable from the existing primitives, composition-friendly, DeepPlant-
owned (`deepplant-original`, AGPL-3.0-only), and needs no standards-conformance
claim to justify its existence. It satisfies every DeepPlant-default criterion in
Issue #127 §16.

### Standards-specific suitability

```text
standards family relevant        YES (ISO 10628-2 / ISO 14617)
exact current geometry supported NO — unresolved
```

The family is correct, but there is **no public evidence** that these exact
primitives correspond to the standard's gate-valve figure. The absence of a
centre line/stem is a **legitimate convention**, not an error: public references
show both "plain" valve bodies and bodies with a stem/handwheel or a centre
marker, and the standard's exact requirement is not public. The neutral
`port_a`/`port_b` names are notation-independent (the anchor contract records
orientation and connection class only, never flow/inlet-outlet semantics).

### Confidence

```text
common-industry evidence     HIGH   (well-known generic valve form)
standards-family evidence    MEDIUM (ISO 10628-2 scope confirmed; valve class listed)
exact standards-geometry     LOW    (normative geometry not public)
```

### Recommendation

```text
DEEPPLANT_DEFAULT
standards-specific: family relevant; exact representation unresolved
    → a future iso-10628 candidate only after evidence/human verification,
      not established now
```

No change in this task.

## `pump.centrifugal`

### Existing DeepPlant geometry

Described from DeepPlant's own sources only
([symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) seed B and
[catalogue.py](../../../src/deepplant/symbols/catalogue.py)):

- a **circle** centred in the box (radius roughly a quarter of the box) as the
  casing;
- a **single full horizontal line across the whole box**, passing straight
  through the circle and touching both edges;
- **two internal lines** from the top and the bottom of the casing that converge
  on the circle's **right-hand point** where it meets the horizontal line —
  forming a right-pointing internal wedge;
- anchors `suction` (west, process) and `discharge` (east, process).

### Public evidence

- **ISO 10628-2 / ISO 14617** cover equipment graphical symbols, and
  `centrifugal pump` is listed among the equipment symbols represented under
  those families (tertiary encyclopaedic listing; primary source confirms the
  family's scope only).
- In common P&ID references a centrifugal pump is normally drawn as a **circle
  (casing) with a tangential outlet/discharge nozzle** and a straight
  inlet/suction, sometimes with a small internal impeller/flow-direction mark.
  This is **common-industry** evidence (Tier 2/3).
- No **public primary** source exposes the standard's normative pump geometry.

Critically, the current construction differs from that common convention in two
ways: the process line passes **straight through the whole casing** (rather than
ending at an inlet and leaving from a tangential outlet), and the internal
geometry is **two converging lines meeting at the casing's right edge**, which is
an idiosyncratic simplification rather than the usual impeller/nozzle treatment.
The `candidate-alignment` metadata says nothing about this and was **not** treated
as evidence.

### DeepPlant-default suitability

**Borderline — medium confidence.** The circle is recognisable as rotational
equipment and the symbol renders and composes cleanly, so it is usable as
DeepPlant's own default glyph. But the through-line reads like a continuous pipe
rather than suction/discharge nozzles, and the internal wedge is not a
recognised public convention, so a reader may not confidently read "centrifugal
pump" specifically. It is acceptable *as DeepPlant-owned practical notation*; it
is weak as a representation that claims to stand for a standard pump figure.

### Standards-specific suitability

```text
standards family relevant        YES (ISO 10628-2 / ISO 14617)
exact current geometry supported NO — likely differs; insufficient evidence
```

The exact geometry is the **weakest** of the three symbols for any
standards-specific claim: public evidence indicates the common/standard form is
built on a tangential outlet and nozzle treatment, which this geometry does not
use. A standards-specific representation would plausibly have to differ.

### Confidence

```text
common-industry evidence     MEDIUM (circle-as-casing widely recognised; internal
                                     construction not a common convention)
standards-family evidence    MEDIUM (ISO 10628-2 scope confirmed; pump class listed)
exact standards-geometry     LOW    (geometry likely differs; not public)
```

### Recommendation

```text
REDESIGN before migration
    → revisit the internal construction and the through-line/nozzle treatment
      first; then treat as deepplant-default
standards-specific: not recommended yet
```

This is the one symbol where "redesign before migration" is the evidence-supported
result. No change is made in this task.

## `instrument.local`

This symbol is evaluated against the **instrumentation** standards landscape, not
the mechanical equipment family used for the valve and pump.

### Existing DeepPlant geometry

Described from DeepPlant's own sources only
([symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) seed C and
[catalogue.py](../../../src/deepplant/symbols/catalogue.py)):

- a **circle** (the base instrument graphic), centred above the box centre — the
  reusable "bubble";
- one **vertical line (stem/process tap)** from the bottom of the circle to the
  south edge — the process attachment;
- **no function letters**, no tag text, no reference designation;
- **no signal anchor** and no signal lines;
- anchor `tap` (south, process).

Base graphic, text/function composition, and signal connections are three
separate concerns here: the definition is only the base graphic plus its process
tap.

### Public evidence

- **ISA (ISA5.1)** — the official ISA5.1 page gives purpose: "a uniform means of
  designating instruments and instrumentation systems used for measurement and
  control … includes symbols and an identification code", and scope "suitable
  whenever any reference to an instrument is required in the chemical, petroleum,
  power generation, air conditioning, metal refining, and numerous other
  industries". It explicitly recognises "alternative symbolism methods" and
  "options … for adding information or simplifying the symbolism". The current
  edition's title added "*and Control*".
- **ISO (ISO 15519-2:2015)** — "rules and guidelines for representation of
  measurement, control, and actuation in diagrams for process industry", covering
  PFD/P&ID/PCD/TYD, and it now carries the letter codes for process control
  information (moved from ISO 14617-6).
- **Tertiary corroboration** — a process-industry overview notes that instrument
  symbols in P&IDs "are generally based on" ISA S5.1, and lists ISO 15519-1/-2
  and ISO 10628-1/-2 as the governing standards for the diagram.
- The **circle/bubble with an identification code** is the base instrument
  function graphic in these systems (common-industry evidence); a field-mounted
  instrument is attached to the process by a short connecting line.

### DeepPlant-default suitability

**Suitable — high confidence.** A plain instrument circle is recognisable, simple,
machine-renderable, composition-friendly, DeepPlant-owned, and deliberately
carries **no** function letters or mandatory signal anchor. Withholding the
letters is *correct* for a reusable base graphic (the letters are part of the
ISA/ISO identification system and are composed per concrete instrument);
withholding a mandatory signal anchor is also *correct* (a local indicator may
have no outgoing signal while a transmitter does, so the signal belongs to the
later function composition). The one nuance is that the included process
**stem/tap** is a connection/attachment convention rather than part of the bare
bubble — a defensible DeepPlant presentation choice, but worth remembering when a
standards-specific composition is designed.

### Standards-specific suitability

```text
standards family relevant        YES — but the INSTRUMENTATION family, not iso-10628
exact current geometry supported NO — unresolved
```

`instrument.local` records `StandardsReference(standard="ISO 15519-2:2015")`,
which is the correct **family** (measurement/control representation), and this is
consistent with reality: instrumentation belongs to the ISO 15519-2 / ISA-5.1 /
IEC 62424 landscape, **not** to an `iso-10628` equipment-symbol profile. The
exact base-graphic geometry (circle + tap, no letters) is not publicly verifiable
as normative, so the exact representation stays unresolved.

### Confidence

```text
common-industry evidence     HIGH   (circle/bubble base graphic is standard practice)
standards-family evidence    HIGH   (instrumentation family, not equipment symbols)
exact standards-geometry     LOW    (normative geometry not public)
```

### Recommendation

```text
DEEPPLANT_DEFAULT
standards-specific: instrumentation profile required; profile identity unresolved
    (ISO 15519-2 / ISA-5.1 family) — NOT iso-10628
```

No change in this task.

## Cross-symbol findings

1. **`generic-iso` conflates two notation families.** The three symbols record
   *different* intended standards already: `valve.gate` and `pump.centrifugal`
   cite ISO 10628-2 (equipment/process symbols), while `instrument.local` cites
   ISO 15519-2 (measurement/control). A single `generic-iso` label hides this, so
   the label is too coarse to drive a standards-specific migration.
2. **DeepPlant-default and standards-specific pull apart.** All three are
   reasonable DeepPlant-owned glyphs, but that is a *different* question from
   whether the exact geometry matches a standard. For all three the exact
   standards geometry is unresolved, so "good default" must not be read as
   "standards-ready".
3. **The pump is the weak link.** It is the only symbol whose *form* (not just its
   verification) is questioned by the evidence; a redesign is the evidence-backed
   next step before any migration.
4. **Anchors are notation-independent.** `port_a`/`port_b`, `suction`/`discharge`,
   and `tap` record geometry and connection class, never flow or inlet/outlet
   semantics, so they survive any profile migration unchanged. No anchor change is
   implied by this research.
5. **Instrumentation is a separate axis.** `instrument.local` shows that
   "standards-specific" is not one bucket: a P&ID legitimately mixes an
   equipment/piping notation family with an instrumentation/control family.

### Required classification summary

| Symbol | Current profile | DeepPlant-default suitability | Standards-specific finding | Confidence | Recommended next action |
|---|---|---|---|---|---|
| `valve.gate` | `generic-iso` | Suitable | Family relevant (ISO 10628-2 / ISO 14617); exact presentation unresolved | Default high; exact geometry low | Migrate to `deepplant-default` (geometry unchanged); defer `iso-10628` candidate pending verification |
| `pump.centrifugal` | `generic-iso` | Borderline | Family relevant (ISO 10628-2 / ISO 14617); exact geometry likely differs | Default medium; exact geometry low | Redesign geometry first, then `deepplant-default`; no standards profile yet |
| `instrument.local` | `generic-iso` | Suitable | Instrumentation family required (ISO 15519-2 / ISA-5.1); **not** `iso-10628`; profile identity unresolved | Default high; exact geometry low | Migrate to `deepplant-default`; later an instrumentation standards profile |

### Evidence-strength distinction (not compressed into one score)

| Symbol | common-industry evidence | standards-family evidence | exact standards-geometry evidence |
|---|---|---|---|
| `valve.gate` | HIGH | MEDIUM | LOW (insufficient) |
| `pump.centrifugal` | MEDIUM | MEDIUM | LOW (insufficient / likely differs) |
| `instrument.local` | HIGH | HIGH | LOW (insufficient) |

```text
"the family is relevant"   ≠   "the exact geometry is supported"
```

Not one symbol clears the higher threshold in Issue #127 §17 for placing its
**exact current geometry** into a standards-specific profile. That is the central
result: standards profiles are relevant, exact representations stay unresolved.

## Profile-architecture implications

**Is the planned `deepplant-default + iso-10628` direction sufficient?**

```text
sufficient for the current three symbols?               NO
sufficient for mechanical/equipment symbols            YES (valve; pump after redesign)
sufficient for instrumentation                          NO
too coarse                                              YES — for the three symbols together
profile family naming should be reconsidered            YES
```

Reasoning:

- `iso-10628` is the **chemical/petrochemical equipment and piping symbol family**
  (an application of ISO 14617). It is the right family for `valve.gate` and
  (after redesign) `pump.centrifugal`.
- Instrumentation/measurement-control representation is owned by a **different**
  family — ISO 15519-2, with the ISA-5.1 (and IEC 62424) identification system in
  practice. Forcing `instrument.local` under an `iso-10628` profile would make a
  standards claim the evidence does not support.
- Therefore the profile model needs to be able to express **two standards axes**
  within one drawing: an equipment/piping notation profile and an
  instrumentation/control notation profile. A single `iso-10628` profile cannot.

This is recorded as an **architectural implication only**. No profile is added,
`profiles.py` is not edited, and no `iso-10628` is created in this task (§22 of
the Issue #127 task). The concrete decision belongs to Issue #124 (§24).

**Recommended shape (for the future issue, not implemented here):**

```text
deepplant-default            product default, no standards claim (unchanged)
future profile families      e.g. an equipment/process symbols profile
                                  and a separate instrumentation/control profile
do NOT force                 instrumentation into an iso-10628 profile
```

## Migration recommendation

The evidence supports this migration intent for the three current `generic-iso`
representations. **None of it is performed here.**

```text
valve.gate
    current:        generic-iso
    recommendation: deepplant-default   (retain geometry unchanged)
    ISO-specific:   family relevant (ISO 10628-2 / ISO 14617);
                    exact representation unresolved pending normative/human verification;
                    not recommended as an iso-10628 representation yet

pump.centrifugal
    current:        generic-iso
    recommendation: REDESIGN before migration, then deepplant-default
    ISO-specific:   family relevant; exact geometry likely differs;
                    not recommended for any standards profile yet

instrument.local
    current:        generic-iso
    recommendation: deepplant-default   (retain geometry unchanged)
    standards family: instrumentation profile (ISO 15519-2 / ISA-5.1);
                      profile identity unresolved; NOT iso-10628
```

Sequence implied by the evidence:

```text
1. redesign pump.centrifugal geometry            (symbol slice)
2. migrate valve.gate + instrument.local
   to deepplant-default (no geometry change)     (profile-migration slice)
3. define notation-family-aware standards
   profiles under Issue #124                     (architecture slice)
4. obtain human verification for any future
   iso-10628 / instrumentation representation    (verification slice)
```

## Assessment of the current `candidate-alignment` records

The three definitions currently record
`verification="candidate-alignment"`. The dedicated conclusion is:

```text
retain `candidate-alignment`   (well-supported as an intent record; no change needed)
downgrade?                     no — `candidate-alignment` already claims no conformance
promote to `human-verified`?   NO — never in this task, and not supported by evidence
```

Why this is the honest result:

- `candidate-alignment` means only *"the project intends correspondence; no human
  has compared it against an authorized copy"*. It does **not** assert
  conformance, so public evidence that cannot show the normative geometry does not
  falsify it, and it remains a correct, conservative description of intent.
- The **family intent** is coherent for all three: equipment symbols → ISO
  10628-2, instrumentation → ISO 15519-2 (see
  [Standards / notation landscape](#standards--notation-landscape)).
- The **weakest record is `pump.centrifugal`**: the intent is still plausible, but
  the exact geometry is the least likely to correspond, so it should be revisited
  during the redesign. Even so, this is a *redesign* concern, not a reason to
  change the verification state.
- No record may be promoted to `human-verified`: that requires a named human
  comparison against an authorized copy, with locator, verifier, and date, and it
  is out of scope and unsupported here.

**No production verification state is changed by this document.**

## Coverage-matrix discrepancy (documented, not rewritten)

The current implementation-status block in
[mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md) records all three
symbols as profile `generic-iso` with per-symbol standard references. That is
factually correct today and is **not** materially misleading, so it is **not
rewritten** here (Issue #127 §25).

The one nuance worth a future, separately-scoped change: the matrix presents a
single "Profile" column and a single "Standard reference" column, which reads as
one standards family per catalogue. The research shows the catalogue already
spans **two** standards families (equipment vs instrumentation). Making the
matrix profile-family-aware is a **follow-up documentation/implementation
change**, not part of this research.

## Evidence gaps

- **Normative geometry is not public.** ISO/ISA scope pages confirm *what* the
  standards cover, never the exact glyphs. Exact-geometry correspondence is
  therefore `low` for every symbol and can only be closed by a human against an
  authorized copy — which must not be an AI task.
- **`iso.org` blocked automated retrieval** (HTTP 403 on every attempt on
  2026-10-09), so the scope text used is the official abstract as reproduced by
  resellers; identifiers/editions must be re-verified by a human (consistent with
  the standing note in the [standards registry](../reference/standards-registry.md)).
- **No reputable secondary source for the specific glyph forms was retrievable**
  in this session (search engines were rate-limited/blocked). The
  common-industry claims for the concrete bow-tie valve and the pump's internal
  wedge therefore rest on general engineering knowledge plus tertiary listings,
  and are marked MEDIUM at best.
- **AVEVA official documentation was not retrieved** (site pages returned 404/429
  in this session). The vendor evidence for "symbol libraries are configurable"
  therefore rests on Autodesk and Siemens primary documentation only.
- **PIP `PIC001` was not independently confirmed** from `pip.org`; only the
  organisation, its harmonisation role, and its practice counts were confirmed.
- **Whether a gate valve glyph requires a centre line/stem/handwheel** is not
  settled by public evidence.
- **No private material was usable to close any gap**, by design: restricted
  standards were not inspected.

## Recommended follow-up slices

These are recommendations, not created Issues. The smallest next bounded slices,
in dependency order:

| # | Slice | Category | Depends on |
|---|---|---|---|
| 1 | Redesign `pump.centrifugal` geometry (nozzle/through-line/internal treatment), keeping the same `symbol_id` and anchors | B — redesign before migration | — |
| 2 | Migrate `valve.gate` and `instrument.local` to `deepplant-default` with **no geometry change**; keep the existing (optional) standards relationship as an intent record | A — migrate to default | #124 authorizes the migration |
| 3 | Define notation-family-aware standards profiles (equipment/process vs instrumentation/control) rather than one `iso-10628` | C — profile architecture | #124; this evidence |
| 4 | Obtain human verification against authorized copies before any `human-verified` / standards-profile representation | D — human verification | 1–3 |
| 5 | Make the coverage matrix (and gallery) profile-aware | E — matrix/gallery | 3 |
| 6 | Apply this same method to the PR #123 concepts (`valve.ball`, `valve.check`, `fitting.reducer`) | F — classify stranded concepts | method proven here; #123 unblocked |

Explicitly **not** recommended: creating any of these Issues automatically, or
retiring `generic-iso` before 1–3 land (Issue #127 §32).

## Sources

All sources were public and were accessed on **2026-10-09**. No standards figure,
table, or normative text was downloaded, copied, or committed; external graphical
material, where seen, informed only high-level textual conclusions.

### Tier 1 — public primary sources

| Publisher | Document / page | URL | Type | Claim supported |
|---|---|---|---|---|
| ISO | ISO 10628-2:2012 — Part 2: Graphical symbols | https://www.iso.org/standard/51841.html | primary (catalogue entry; body blocked, HTTP 403) | covers graphical symbols for chemical/petrochemical diagrams; an application standard of ISO 14617; excludes electrotechnical diagrams |
| ISO | ISO 10628-1:2014 — Part 1: Specification of diagrams | https://www.iso.org/standard/51840.html | primary (catalogue entry) | covers classification/content/representation of flow diagrams; an application standard of ISO 15519 |
| ISO | ISO 15519-2:2015 — Part 2: Measurement and control | https://www.iso.org/standard/54916.html | primary (catalogue entry) | rules for representing measurement, control, and actuation; covers PFD/P&ID/PCD/TYD; carries PCI letter codes |
| ISO | ISO 14617-1:2025 — Part 1: General rules | https://www.iso.org/standard/85641.html | primary (catalogue entry) | general rules for preparing/presenting diagram symbols for industrial components/products/processing |
| ISO | ISO 14617-2:2025 — Part 2: Graphical symbols | https://www.iso.org/standard/83364.html | primary (catalogue entry) | a symbol library for industrial components/products/processing; letter codes moved to ISO 15519-2 |
| ISA | ISA5.1 — Instrumentation Symbols and Identification (committee page) | https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa5-1 | primary | ISA5.1 purpose (uniform designation system incl. symbols + identification code) and scope (instrumentation across many industries); 2024 title added "and Control"; ISA prohibits entering ISA IP into AI tools |
| ISA | ANSI/ISA-5.1-2024 product page | https://www.isa.org/products/ansi-isa-5-1-2024-instrumentation-and-control-symb | primary | current edition "Instrumentation and Control – Symbols and Identification" |
| Autodesk | AutoCAD P&ID 2011 — Getting Started (PDF) | https://images.autodesk.com/adsk/files/adskpid_gs.pdf | primary (vendor doc) | a P&ID workspace reflects a chosen *symbol standard* (PIP default; DIN; JIS/ISO) — symbol standards are project-selectable |
| Siemens | COMOS Process P&ID documentation (Operation manual, PDF) | https://support.industry.siemens.com/cs/attachments/109796146/PID_Operation_enUS_en-US.pdf | primary (vendor doc) | COMOS ships a comprehensive library of preconfigured P&ID objects; document libraries per IEC 61355 |
| Process Industry Practices (PIP) | pip.org — organization/practices overview | https://www.pip.org/ | primary (organisation) | PIP harmonizes internal company standards/practices; 600+ practices across 14 disciplines |

The Autodesk PDF body is not text-extractable by the tool used; its statement is
taken from the document's indexed snippet, with the primary document retained by
URL. ISO catalogue pages returned HTTP 403 to automated retrieval; the abstract
text is the official abstract as reproduced by the Tier 2 resellers below and is
flagged for human re-verification.

### Tier 2 — public engineering references (secondary)

| Publisher | Document / page | URL | Type | Claim supported |
|---|---|---|---|---|
| en-standard.eu, iTeh Standards, SIS, genorma, EVS, etc. | Reseller catalogue pages reproducing official ISO abstracts (ISO 10628-1/-2, ISO 15519-2, ISO 14617) | e.g. https://en-standard.eu/, https://standards.iteh.ai/, https://www.sis.se/ | secondary (official abstract reproduced) | the scope sentences quoted above; used only because the ISO catalogue body blocked automated retrieval |
| PharmaDiagrams | "ISA-5.1 instrument symbols and P&ID tags" | https://pharmadiagrams.com/standards/isa-5.1 | secondary | ISO 10628 and ISA-5.1 "layer rather than compete"; ISO 10628 governs the diagram/equipment symbols, ISA-5.1 the instrument tags/symbols; European practice uses IEC 62424 (retrieved as a search-result summary; direct fetch returned 404) |
| ANSI (blog) | "ANSI/ISA 5.1-2024: Instrumentation Symbols & Identification" | https://blog.ansi.org/ | secondary | the 2024 revision updated the title to include "*and Control*" |

### Tier 3 — community / tertiary context

| Publisher | Document / page | URL | Type | Claim supported |
|---|---|---|---|---|
| Wikipedia | "Piping and instrumentation diagram" | https://en.wikipedia.org/wiki/Piping_and_instrumentation_diagram | tertiary | instrument symbols in P&IDs are "generally based on" ISA S5.1; equipment symbols are listed "according to ISO 10628 and ISO 14617" (context only) |
| Wikipedia | "Process flow diagram" | https://en.wikipedia.org/wiki/Process_flow_diagram | tertiary | standards list (ISO 15519-1/-2, ISO 10628-1/-2) and that PFD rules/symbols come from standardization bodies (context only) |

### Related, in-repository

- [standards-registry.md](../reference/standards-registry.md) — current reference
  set and the standing human re-verification rule.
- [standards-licensing-evidence.md](standards-licensing-evidence.md) — source,
  licence, and provenance investigation behind the standards policy.
- [symbol-library.md](../reference/symbol-library.md),
  [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md),
  [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) — the symbol
  contract, coverage matrix, and the DeepPlant-owned seed geometry described
  above.
- [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md),
  [ADR-0017](../decisions/ADR-0017-machine-rendered-symbol-definitions.md).
