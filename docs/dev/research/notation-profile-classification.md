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
- **Status:** open evidence — the evidence admissible under repository policy
  (DeepPlant-authored summaries, plus any external material whose terms permit
  AI use) establishes the standards *families* that are relevant, but not the
  concrete normative geometry of any symbol. The result is a bounded
  classification and a set of next slices, not a migration.
- **Scope of investigation:** the basis is DeepPlant-authored repository material
  plus any external material whose applicable terms permit AI use, assessed on
  **2026-10-09**. No restricted ISO/ISA/IEC content was ingested, and no
  public-but-not-AI-permitted page was used as evidence. No private, licensed, or
  restricted standards material (ISO/IEC/ISA figures, the private reference
  bundle, company drawings, or any local private-reference directory) was opened,
  searched, or read. No third-party artwork was copied.
- **Conclusions:**
  - `valve.gate` — a **candidate** for `deepplant-default` on DeepPlant's own
    internal design criteria; external/common-industry recognizability is
    **insufficiently evidenced** under current AI-use policy; the
    equipment-symbol family is relevant per the repository standards registry,
    but the exact standards geometry is **unresolved**.
  - `pump.centrifugal` — DeepPlant-default suitability is **unresolved /
    insufficient evidence**; recommend a **focused review before migration**
    (a redesign is possible but not established). Exact standards geometry is
    **unresolved**.
  - `instrument.local` — a **candidate** for `deepplant-default`;
    instrumentation-specific standards context is **clearly relevant**
    (ISO 15519-2 / ISA-5.1 in the current DeepPlant standards registry), while
    the role of ISO 10628-2 and the final profile composition remain
    **unresolved**.
  - The evidence is sufficient to **question** whether one standards-specific
    profile identity can represent both equipment/process and
    instrumentation/control concerns; it is **not** sufficient to choose the
    final composition model, which belongs to Issue #124 (section
    [Profile-architecture implications](#profile-architecture-implications)).
  - The existing `candidate-alignment` records are **left unchanged** because
    this issue does not modify production metadata and because that state records
    project-declared *intent*, not verified correspondence. **No conclusion in
    this research upgrades that intent to evidence of alignment.**
- **Resulting decision:** none. This is evidence supporting a future
  architecture/implementation decision under Issue #124; it does not itself
  change any production state.
- **Conditions for revisiting:** a `deepplant-default` migration is scheduled; a
  standards-specific profile is introduced; a human verification against an
  authorized standard copy is recorded; permitted AI-usable evidence becomes
  available; or the catalogue changes materially.

**This document does not own current rules and does not authorize a migration.**
It records what was investigated and found. Issue #124 defines the governing
notation-profile architecture; any concrete migration requires a separately
scoped and authorized implementation Issue that is consistent with #124.

```text
profiles.py
    which notation profiles exist
    what policy applies to them
SymbolDefinition
    which profile this representation belongs to
authorized migration
    changes that assignment
```

[profiles.py](../../../src/deepplant/symbols/profiles.py) defines the recognised
notation-profile vocabulary and profile policy. A concrete representation's
`notation_profile` is carried by its `SymbolDefinition`; changing that assignment
is a production migration and requires a separately scoped and authorized
implementation Issue. The symbol contract is
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

The admissible evidence base is set by repository policy
([standards.md](../workflow/standards.md),
[ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md)):

```text
allowed     DeepPlant-authored summaries and role notes
            openly licensed material (DEXPI, CC BY 4.0)
            public material whose applicable terms explicitly permit AI use
forbidden   restricted ISO / ISA / IEC content, including AI ingestion of
            hosted catalogue or web pages merely because they are public
```

The primary basis is therefore the DeepPlant-authored material already in the
repository:

- [standards-registry.md](../reference/standards-registry.md) — each standard's
  recorded role in DeepPlant;
- [standards-licensing-evidence.md](standards-licensing-evidence.md) — the
  licence/source/provenance investigation;
- [standards.md](../workflow/standards.md) — the usage policy;
- [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md) and
  [ADR-0017](../decisions/ADR-0017-machine-rendered-symbol-definitions.md);
- [symbol-library.md](../reference/symbol-library.md),
  [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md), and
  [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md).

Standards-family context is taken from the **DeepPlant-authored role summaries**
already recorded in the registry — not from ISO, ISA, or IEC pages. Official
source URLs appear later in this document as **reference metadata for human
navigation**; a listed URL is not an AI-inspected source.

Two limits shaped the method:

- **A role summary is not geometry.** A registry role note says *why* a standard
  is relevant; it never shows a glyph. Repository-authored material therefore
  cannot establish that DeepPlant's primitives match a standard's figure.
- **Restricted copies must not be read by an agent.** ISO/IEC/ISA content is
  restricted, and ISA's published notice prohibits entering ISA intellectual
  property into AI tools. No restricted figure, table, or text was inspected.

Confidence is reported **separately** for distinct questions:

```text
internal default suitability      does the glyph meet DeepPlant's own design goals?
external recognizability          is the broad form an evidenced industry convention?
standards-family relevance        is the target family relevant (repository summary)?
exact standards-geometry          is this exact geometry evidenced?
```

Under the admissible evidence base above, **exact standards-geometry is answered
`low` / `insufficient` for every symbol**: the normative geometry is not in the
repository-authored material and must not be read from a restricted copy by an
agent. That is a result, not a failure.

## Standards / notation landscape

The current DeepPlant standards registry records different standards-family
references for the three symbols: equipment/process-symbol references for
`valve.gate` and `pump.centrifugal`, and an instrumentation/measurement-control
reference for `instrument.local`. This is sufficient to **question** whether one
standards-specific profile identity can represent all three concerns, but not to
determine the final composition model: whether these standards families overlap,
compose, or require distinct profile representation remains **unresolved** under
Issue #124. This section quotes no ISO/ISA/IEC source text; it restates only what
the **DeepPlant standards registry** already records as each standard's role.

| Family (as recorded by DeepPlant) | Document(s) | Registry role summary | Relevance here |
|---|---|---|---|
| Process-diagram structure | ISO 10628-1:2014 | "Diagram structure and drafting reference for the diagrams DeepPlant derives (PFD/P&ID structure, layout logic)." | diagram structure, not symbol geometry |
| Process/equipment graphical symbols | ISO 10628-2:2012 | "Normative graphical-symbol reference for the chemical and petrochemical process industry. Reference for future equipment symbols such as pump, heat exchanger, vessel." | the family behind `valve.gate` and `pump.centrifugal` |
| General symbol library | ISO 14617-1:2025 / ISO 14617-2:2025 | -1: "General rules for graphical symbols for diagrams (preparation and presentation of symbols)." -2: "General industrial graphical-symbol reference. Broader scope than ISO 10628-2; secondary reference for generic component glyphs." | the library behind the equipment family |
| Measurement, control, instrumentation | ISO 15519-2:2015 | "Diagrams for the process industry; representation of measurement, control, and instrumentation, relevant to P&ID instrumentation symbols. Reference direction for the `instrument.local` base graphic." | the family behind `instrument.local` |
| Instrumentation symbols and identification | ANSI/ISA-5.1-2024 | "Instrumentation and control symbols and identification. Relevant to later P&ID instrumentation work, not the current PFD-level step glyphs." | the instrumentation identification system (letters, bubbles, lines) |
| P&ID ↔ PCE-CAE interoperability | IEC 62424:2016 | "Later interoperability reference for P&ID ↔ process-control-engineering (PCE-CAE) exchange and representation of process control requests in P&IDs." | later interoperability reference |
| Practical industry practice | Process Industry Practices (PIP) | not recorded as a normative standard; a recognized industry-practice/reference family (see [Industry and CAD implementation evidence](#industry-and-cad-implementation-evidence)) | process and P&ID documentation practice |
| Commercial CAD libraries | Autodesk, Siemens, AVEVA | external vendor material **not used as evidence** (see below) | context only; not established here |

**Correction to the working assumption.** The prompt's initial grouping — ISO
10628/14617 (equipment/piping), ISO 15519 (process-industry diagram rules *and*
instrumentation), ISA-5.1 (instrumentation), PIP (practical documentation),
commercial libraries (configurable profiles) — is broadly consistent with the
repository registry. What the registry establishes is that
**instrumentation/measurement-control representation has its own standards
family** (ISO 15519-2, with ISA-5.1 for identification), described separately
from the equipment-symbol family. It does **not** establish that ISO 10628-2
plays no part in instrument representation; that question stays open (see
[`instrument.local`](#instrumentlocal)).

## Industry and CAD implementation evidence

This evidence is architectural and contextual. The specific vendor documents
(Autodesk, Siemens, AVEVA) and third-party secondary summaries that an earlier
draft relied on are **not** part of the repository's admissible evidence base:
their terms were not established to permit the AI use that was performed, so
their source-derived claims are removed here rather than merely disclaimed.

What can be stated without inadmissible sources:

```text
The general question of how commercial tools model multiple notation libraries
was not established from AI-usable evidence in this research.
```

Process Industry Practices (PIP):

```text
PIP is a recognized industry-practice/reference family relevant to process and
P&ID documentation.

Its exact role in DeepPlant's future notation-profile architecture was not
established from AI-usable evidence in this research.
```

PIP is **not** collapsed here into "project/company convention". Company or
project convention remains a separate DeepPlant concept; whether PIP is that, or
a distinct industry-practice layer, is unresolved.

The only repository-admissible architectural observation is interpretive, not
sourced from commercial tooling:

```text
one diagram can combine an equipment/piping notation family
with a separate instrumentation/control notation family
```

This is a reading of the DeepPlant registry's own family split (see the
[landscape](#standards--notation-landscape)), not evidence from vendor
documentation.

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

### Evidence

- **Repository-authored (admissible):** the standards registry records ISO
  10628-2 as the "Normative graphical-symbol reference for the chemical and
  petrochemical process industry … for future equipment symbols", and ISO
  14617-2 as a "secondary reference for generic component glyphs". That makes the
  equipment-symbol family **relevant** to a valve glyph; it does not describe
  this glyph.
- **External recognizability:** not independently established by admissible
  evidence. The earlier draft's claims that the opposed-triangle body is "a
  long-recognised generic valve glyph" and that "public references show both
  plain bodies and bodies with a stem/handwheel" rested on material whose AI use
  was not permitted, and they are removed.
- **Exact standards geometry:** unresolved. No repository-authored material
  describes the standard's gate-valve figure, and it must not be read from a
  restricted copy.

### Classification

```text
internal DeepPlant-default suitability   candidate / suitable
    simple, machine-renderable from the existing primitives, composition-friendly,
    DeepPlant-owned (deepplant-original, AGPL-3.0-only), conceptually clear within
    DeepPlant
external recognizability                 insufficiently evidenced
standards-family relevance               relevant (ISO 10628-2 / ISO 14617-2)
exact standards-geometry                 unresolved
```

The neutral `port_a`/`port_b` names are notation-independent (the anchor contract
records orientation and connection class only, never flow/inlet-outlet semantics).

### Recommendation

```text
DEEPPLANT_DEFAULT candidate (internal design grounds only)
standards-specific: family relevant; exact representation unresolved
    → a future standards-profile candidate only after admissible evidence or
      human verification, not established now
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

### Evidence

- **Repository-authored (admissible):** the standards registry records ISO
  10628-2 as the equipment-symbol family ("… for future equipment symbols such
  as pump, heat exchanger, vessel") and ISO 14617-2 as the general symbol
  library. That makes the equipment family **relevant** to a pump glyph; it does
  not describe this glyph.
- **External recognizability:** not established by admissible evidence. The
  earlier draft's claim that a centrifugal pump "is normally drawn as a circle
  with a tangential outlet/discharge nozzle" came from material whose AI use was
  not permitted and is removed. This research therefore has **no admissible
  external evidence** for how conventional or recognizable the exact
  construction is.
- **Exact standards geometry:** unresolved. No admissible source or
  repository-authored material describes the standard's pump figure.

### Classification

```text
internal DeepPlant-default suitability   unresolved / medium confidence
    the geometry is internally coherent and machine-renderable, but this
    research lacks sufficiently strong admissible external evidence to
    establish how recognizable or conventional the exact construction is
external recognizability                 insufficiently evidenced
standards-family relevance               relevant (ISO 10628-2 / ISO 14617-2)
exact standards-geometry                 unresolved
```

### Recommendation

```text
REVIEW_BEFORE_MIGRATION / INSUFFICIENT_EVIDENCE
    → a focused human/design review of the internal construction and the
      through-line/nozzle treatment
      redesign is a possibility, NOT a research-proven requirement
standards-specific: not recommended yet
```

The `candidate-alignment` intent recorded for `pump.centrifugal` should be
revisited during that focused review if appropriate. No change is made in this
task.

## `instrument.local`

This symbol is evaluated against the **instrumentation** standards landscape
recorded by DeepPlant, not the mechanical-equipment family used for the valve and
pump.

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

### Evidence

- **Repository-authored (admissible):** the standards registry records
  ISO 15519-2 as "Diagrams for the process industry; representation of
  measurement, control, and instrumentation, relevant to P&ID instrumentation
  symbols. Reference direction for the `instrument.local` base graphic", and
  ANSI/ISA-5.1 as "Instrumentation and control symbols and identification.
  Relevant to later P&ID instrumentation work, not the current PFD-level step
  glyphs." IEC 62424 is recorded as a "later interoperability reference for
  P&ID ↔ process-control-engineering (PCE-CAE) exchange".
- **No ISA or ISO source text is quoted or paraphrased here.** ISA prohibits
  entering ISA intellectual property into AI tools, and ISO catalogue/web content
  may not be AI-ingested merely because it is public; the earlier draft's ISA
  purpose/scope quotations and its ISO scope sentence are removed.
- **Exact standards geometry:** unresolved — no admissible material describes the
  normative instrument base graphic.
- The plain instrument circle is DeepPlant's own base graphic; whether it
  corresponds to any external convention is a separate, unresolved question.

### Classification

```text
internal DeepPlant-default suitability   candidate / suitable
    a plain circle is simple, machine-renderable, composition-friendly, and
    DeepPlant-owned; withholding function letters and a mandatory signal anchor
    is defensible for a reusable base graphic
standards-family relevance               instrumentation-specific context clearly
                                         relevant (ISO 15519-2 / ISA-5.1)
exact standards-geometry                 unresolved
role of ISO 10628-2 in the final model   unresolved without permitted or human
                                         verification
```

`instrument.local` records `StandardsReference(standard="ISO 15519-2:2015")`,
which is the correct **family** (measurement/control representation). This does
**not** establish that ISO 10628-2 plays no part in instrument representation;
that exclusivity is not supported by admissible evidence and is not claimed.

### Recommendation

```text
DEEPPLANT_DEFAULT candidate (internal design grounds only)
standards-specific: instrumentation-specific context clearly relevant
    → profile composition and the role of ISO 10628-2 remain unresolved
      (Issue #124); no standards profile established now
```

No change in this task.

## Cross-symbol findings

1. **`generic-iso` spans more than one standards family.** The three symbols
   record *different* intended standards: `valve.gate` and `pump.centrifugal`
   cite ISO 10628-2 (equipment/process symbols), while `instrument.local` cites
   ISO 15519-2 (measurement/control). A single `generic-iso` label hides this, so
   the label is too coarse to drive a standards-specific migration.
2. **DeepPlant-default and standards-specific pull apart.** All three are
   DeepPlant-owned glyphs whose DeepPlant-default status is an *internal design*
   question, while standards correspondence is a *separate evidence* question.
   For all three the exact standards geometry is unresolved, so "good default"
   must not be read as "standards-ready".
3. **The pump is the least evidenced symbol.** Its DeepPlant-default suitability
   is **unresolved / insufficient evidence**; the honest next step is a focused
   review before migration, in which a redesign is possible but not proven.
4. **Anchors are notation-independent.** `port_a`/`port_b`, `suction`/`discharge`,
   and `tap` record geometry and connection class, never flow or inlet/outlet
   semantics, so they survive any profile migration unchanged. No anchor change is
   implied by this research.
5. **Equipment and instrumentation may need distinct representation.** The
   registry's own family split shows that "standards-specific" may not be one
   bucket: a P&ID can mix an equipment/piping notation family with an
   instrumentation/control family. How that composes is unresolved (Issue #124).

### Required classification summary

| Symbol | Current profile | DeepPlant-default (internal criteria) | Standards-specific finding | Recommended next action |
|---|---|---|---|---|
| `valve.gate` | `generic-iso` | Candidate / suitable | Family relevant (ISO 10628-2 / ISO 14617-2); exact geometry unresolved; external recognizability insufficiently evidenced | Migrate to `deepplant-default` (geometry unchanged); defer any standards profile pending evidence/verification |
| `pump.centrifugal` | `generic-iso` | Unresolved / insufficient evidence | Family relevant; exact geometry unresolved | Focused review before migration; redesign possible but not established; no standards profile yet |
| `instrument.local` | `generic-iso` | Candidate / suitable | Instrumentation-specific context clearly relevant (ISO 15519-2 / ISA-5.1); exact geometry unresolved; role of ISO 10628-2 unresolved | Migrate to `deepplant-default`; later an instrumentation standards profile |

### Evidence-strength distinction (not compressed into one score)

| Symbol | internal default suitability | external recognizability | standards-family relevance | exact standards-geometry |
|---|---|---|---|---|
| `valve.gate` | candidate / suitable | insufficient | relevant | unresolved (low) |
| `pump.centrifugal` | unresolved | insufficient | relevant | unresolved (low) |
| `instrument.local` | candidate / suitable | insufficient | relevant (instrumentation) | unresolved (low) |

```text
"the family is relevant"   ≠   "the exact geometry is supported"
```

No symbol clears the threshold for placing its **exact current geometry** into a
standards-specific profile. That is the central result: relevant families are
recorded, exact representations stay unresolved, and external recognizability is
not independently evidenced under current AI-use policy.

## Profile-architecture implications

**Is one standards-specific profile identity enough for the current three
symbols?**

```text
one standards-specific identity sufficient?    questioned, not decided
equipment vs instrumentation concerns          may need distinct representation
final composition model                        unresolved — belongs to Issue #124
```

Reasoning (from repository-authored context only):

- The registry records the equipment/process-symbol family (ISO 10628-2 /
  ISO 14617) separately from the instrumentation/measurement-control family
  (ISO 15519-2, with ISA-5.1 for identification).
- The evidence indicates that equipment/process-symbol concerns and
  instrumentation/control concerns **may need to be represented distinctly** in
  the future standards-profile architecture.
- The evidence is **not** sufficient to choose the composition model. It does not
  decide between two independent profile axes, a composite profile, one broader
  profile identity, separate symbol-library dimensions, per-domain subprofiles,
  or another mechanism.

```text
The current evidence is sufficient to question whether one standards-specific
profile identity can represent all concerns across equipment and instrumentation.

It is NOT sufficient to choose the final composition model.

#124 should explicitly decide how equipment/process-symbol standards and
instrumentation/control standards compose in one drawing.
```

This is recorded as an **architectural implication only**. No profile is added,
`profiles.py` is not edited, and no standards profile is created in this task.
The concrete decision belongs to Issue #124.

## Migration recommendation

The evidence supports this migration intent for the three current `generic-iso`
representations. **None of it is performed here.**

```text
valve.gate
    current:        generic-iso
    recommendation: deepplant-default candidate   (retain geometry unchanged)
    standards-specific:
                    family relevant (ISO 10628-2 / ISO 14617-2);
                    exact representation unresolved pending admissible
                    evidence / human verification

pump.centrifugal
    current:        generic-iso
    recommendation: focused review before migration
                    (redesign possible but not established)
    standards-specific:
                    family relevant; exact geometry unresolved;
                    not recommended for any standards profile yet

instrument.local
    current:        generic-iso
    recommendation: deepplant-default candidate   (retain geometry unchanged)
    standards-specific:
                    instrumentation-specific context clearly relevant
                    (ISO 15519-2 / ISA-5.1); profile composition and the role
                    of ISO 10628-2 unresolved
```

Sequence implied by the evidence:

```text
1. focused review of pump.centrifugal geometry      (symbol slice)
2. migrate valve.gate + instrument.local
   to deepplant-default (no geometry change)        (profile-migration slice)
3. decide how equipment and instrumentation
   standards compose under Issue #124               (architecture slice)
4. obtain human verification for any future
   standards-specific representation                (verification slice)
```

## Assessment of the current `candidate-alignment` records

The three definitions currently record
`verification="candidate-alignment"`. The dedicated conclusion is:

```text
candidate-alignment
    project-declared intent to correspond
    not human-verified
    not conformance evidence

retain `candidate-alignment`   (unchanged)
downgrade?                     no — the state already claims no conformance
promote to `human-verified`?   NO — never in this task, and not supported by evidence
```

Precise wording for this research:

- This research provides **no new exact-geometry verification**.
- The existing `candidate-alignment` state is **left unchanged** because the issue
  does not modify production metadata and because that state records project
  *intent*, not verified correspondence.
- **No conclusion in this research upgrades that intent to evidence of
  alignment.**
- The **weakest record is `pump.centrifugal`**: the intent is still plausible, but
  its exact geometry is the least evidenced, so its intent should be **revisited
  during the future focused review** if appropriate. That is not a reason to
  change the verification state here.
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

- **Admissible evidence is deliberately narrow.** The primary basis is
  DeepPlant-authored repository material; restricted ISO/ISA/IEC content was not
  ingested, and public-but-not-AI-permitted material was not used. Several
  questions therefore stay open rather than being answered from inadmissible
  sources.
- **Normative geometry is not in repository-authored material.** The registry
  role summaries describe *why* a standard is relevant, never a glyph.
  Exact-geometry correspondence is therefore `low`/`unresolved` for every symbol
  and can only be closed by a human against an authorized copy — which must not
  be an AI task.
- **External industry recognizability is not established.** The earlier draft's
  common-industry claims (the bow-tie valve body, the centrifugal-pump tangential
  outlet, the instrument bubble convention) came from material whose AI use was
  not permitted; they are removed and the questions are left open.
- **Commercial-CAD behaviour was not established from AI-usable evidence.** The
  general question of how vendor tools model multiple notation libraries is
  explicitly **not** answered here.
- **PIP's exact role is unresolved.** PIP is retained only as a recognized
  industry-practice/reference family relevant to process and P&ID documentation;
  its role in DeepPlant's notation-profile architecture was not established.
- **Whether a gate-valve glyph requires a centre line/stem/handwheel** is not
  settled by admissible evidence.
- **No private material was usable to close any gap**, by design: restricted
  standards were not inspected and no private reference path was accessed.

## Recommended follow-up slices

These are recommendations, not created Issues. The smallest next bounded slices,
in dependency order:

These are a **research recommendation (YES)** with **implementation
authorization: NO**. They are not authorized by this research document and not
authorized merely by #124 (which is architecture/planning only); each slice
requires its own separately scoped and **Ready** implementation Issue.

| # | Slice | Category | Depends on |
|---|---|---|---|
| 1 | Focused review of `pump.centrifugal` geometry (nozzle/through-line/internal treatment), keeping the same `symbol_id` and anchors; redesign only if the review concludes it is warranted | B — review before migration | — |
| 2 | Migrate `valve.gate` and `instrument.local` to `deepplant-default` with **no geometry change**; keep the existing (optional) standards relationship as an intent record | A — migrate to default | #124 architecture; separate Ready implementation Issue required |
| 3 | Under #124, decide how equipment/process-symbol standards and instrumentation/control standards compose in one drawing | C — profile architecture | #124; this evidence |
| 4 | Obtain human verification against authorized copies before any `human-verified` / standards-profile representation | D — human verification | 1–3 |
| 5 | Make the coverage matrix (and gallery) profile-aware | E — matrix/gallery | 3 |
| 6 | Apply this same method to the PR #123 concepts (`valve.ball`, `valve.check`, `fitting.reducer`) | F — classify stranded concepts | method proven here; #123 unblocked |

Explicitly **not** recommended: creating any of these Issues automatically, or
retiring `generic-iso` before 1–3 land.

## Sources

### Repository-authored evidence actually used

- [standards-registry.md](../reference/standards-registry.md) — the recorded
  role of each standard in DeepPlant (the standards-family context used above).
- [standards-licensing-evidence.md](standards-licensing-evidence.md) — the
  licence/source/provenance investigation behind the policy.
- [standards.md](../workflow/standards.md) — the standards-usage and
  symbol-provenance policy (including the AI-use rule).
- [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md) and
  [ADR-0017](../decisions/ADR-0017-machine-rendered-symbol-definitions.md) —
  the durable decisions constraining standards use and the symbol model.
- [symbol-library.md](../reference/symbol-library.md),
  [mvp-symbol-coverage.md](../reference/mvp-symbol-coverage.md),
  [symbol-seed-geometry.md](../reference/symbol-seed-geometry.md) — the symbol
  contract, coverage matrix, and DeepPlant-owned seed geometry.
- [profiles.py](../../../src/deepplant/symbols/profiles.py) and
  [catalogue.py](../../../src/deepplant/symbols/catalogue.py) — the notation
  vocabulary and the current definitions (read for description only; not
  modified).
- Issues #119, #124, #125, #127 — scoping and architecture context.

### External reference identifiers / official URLs (reference metadata only)

These are the standards *identifiers* and *official source URLs* already recorded
by DeepPlant. They are listed **for human/reference navigation** and are **not**
AI-inspected evidence in this research:

```text
ISO 10628-1:2014     ISO catalogue / ISO Store (search "ISO 10628-1:2014")
ISO 10628-2:2012     ISO catalogue / ISO Store (search "ISO 10628-2:2012")
ISO 14617-1:2025     ISO catalogue / ISO Store (search "ISO 14617-1:2025")
ISO 14617-2:2025     ISO catalogue / ISO Store (search "ISO 14617-2:2025")
ISO 15519-2:2015     ISO catalogue / ISO Store (search "ISO 15519-2:2015")
ANSI/ISA-5.1-2024    ISA-5.1 committee page
                     https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa5-1
IEC 62424:2016       IEC Webstore (search "IEC 62424:2016")
```

These identifiers and URLs are drawn from the
[standards registry](../reference/standards-registry.md). Adding a URL here does
not make it AI-usable evidence.

### External AI-usable material actually inspected

None. No external source was used as evidence in this research: the applicable
terms/licence of the ISO, ISA, IEC, and vendor pages did not establish that the
AI use performed was permitted, so no source-derived claim is retained from them.

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
