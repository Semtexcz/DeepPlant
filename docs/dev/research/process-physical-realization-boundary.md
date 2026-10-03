---
type: evidence
status: historical
canonical_for:
  - process-physical-realization-boundary
read_when:
  - process-physical-model-growth
  - process-physical-realization-implementation
  - pfd-pid-modeling
update_when:
  - cross-layer-realization-boundary-change
depends_on:
  - docs/contracts/process-model.md
  - docs/contracts/plant-model.md
  - docs/contracts/physical-piping.md
  - docs/dev/research/process-fragment-prototype.md
  - docs/dev/research/physical-piping-model.md
  - docs/dev/research/next-slice-re-evaluation.md
  - docs/dev/research/dexpi/plant-pid-semantic-boundary.md
decision:
  - docs/dev/decisions/ADR-0016-process-physical-realization-boundary.md
evidence: []
superseded_by: null
---

# Process ↔ Physical Realization Boundary

## Outcome card

- **Question investigated:** how should DeepPlant represent the relationship between
  process intent and its physical realization while keeping
  `ProcessModel` / physical topology / `PipingModel` separate — and where should a
  future realization relationship be owned?
- **Status:** historical evidence. Its durable ownership boundary is accepted in
  [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md); no
  mapping schema or runtime behavior is implemented.
- **Inspection scope and date:** the current contracts and accepted ADRs, the
  loadable [realistic fragment](../../../examples/realistic-process-fragment/plant.yaml),
  and the prior evidence listed in the front matter, inspected 2026-10-03 on
  `main` at `68196a745d9fb6da63e07fc7e24a215b54089b31`.
- **Conclusions:**
  1. `ProcessModel` stays independently valid. Physical topology and its dependent
     `PipingModel` form the separate physical side: `PipingModel` is structurally
     valid for local rules, but resolves `Connection` references against
     `PlantModel`. A realization relationship is a cross-layer engineering
     statement, not an intrinsic field of either domain.
  2. A future `ProcessStep` ↔ `Equipment` relationship must permit **zero**
     equipment for a step and **zero** process steps for equipment. The fragment
     proves both; the apparent 1:1 pairs prove no universal cardinality.
  3. A `ProcessStream` realization is semantically a **route / collection of
     existing physical realization facts**, not a synonym for `Connection`,
     `PipingRealization`, `PipingSegment`, or `PipingLine`. `S-004` proves one
     stream can span two `Connection`s and two `PipingRealization`s; its single
     line and segment do not establish either as the universal target.
  4. Candidate **C** (a separate cross-layer realization layer) is the durable
     ownership boundary. It authorizes **no** class, field, YAML, validator,
     relation identity, metadata, or route object.
  5. No independent relationship identity or metadata is currently evidenced.
     Anonymous relationship membership suffices if a later concrete slice
     implements the boundary; identity/status/provenance need their own evidence.
  6. `ProcessPort` ↔ a physical connection-point/boundary is constrained by the
     same layer boundary, but its exact target remains unresolved:
     equipment-adjacent ports can correspond naturally to current physical `Port`s,
     whereas junction ports need a physical boundary the current model does not
     represent honestly.
- **Resulting ADR:** [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md).
- **Current contracts operationalizing the result:** none yet. The current
  contracts continue to state that no process ↔ physical mapping is implemented.
- **Revisit conditions:** a concrete realization-authoring or validation workflow;
  evidenced multiple items realizing one function; a route crossing line or
  property boundaries; or a physical `Nozzle`/`PipingNode`-like boundary required
  for honest process-port correspondence.

## Method and evidence labels

Evidence comes from three sources and is labelled as one of:

```text
proven by the fragment    observable directly in the loadable realistic fragment
domain-plausible          a real engineering case, not yet exercised by a fragment
unsupported speculation   imaginable, but no evidence in this repository
```

The fragment is **intentionally incomplete** on the physical side. Absence of
authored physical topology is evidence of model maturity, never proof that no real
piping exists. Nothing below invents physical data the fragment withholds.

## Current canonical boundaries

These are current contract facts, not proposed implementation shapes:

```text
ProcessStep   != Equipment
ProcessPort   != Port
ProcessStream != Connection

Connection          = directed, property-free physical adjacency
PipingRealization   = statement about one existing Connection
PipingSegment       = physical-property boundary over realizations
PipingLine          = higher-level piping identity/grouping
ProcessStream       = process/PFD intent between ProcessPorts
```

No process object needs a physical object to validate, and no physical object needs
one from the process graph. `PipingModel` is dependent on physical topology (P3
resolves `Connection` references), but it is **not** dependent on `ProcessModel`.
Both directions of the independence invariant are currently enforced by the
absence of any cross-layer field.

## Evidence from the realistic-process-fragment

The only authored physical run is `P-101 → C-001 → FV-101 → C-002 → E-101`,
grouped as `PL-P101-DISCHARGE` / `SEG-1` with two `PipingRealization`s. It is the
physical evidence behind the single process intent `S-004`
(`PS-pump.discharge → PS-hx.in_side_A`).

The same fragment prevents a false graph isomorphism:

- `PS-mix` and `PS-split` are valid process functions with no standalone
  `Equipment`.
- `FV-101` is physical equipment with no `ProcessStep`: it is transparent at this
  PFD abstraction.
- `PS-pump ↔ P-101` and `PS-vessel ↔ V-101` are apparent correspondences only.
- `PS-hx ↔ E-101` describes one selected process side; the physical exchanger has
  another side outside the process graph.
- `PS-consumer` reaches beyond the represented physical fragment.
- `S-001`, `S-002`, `S-003`, and `S-005`–`S-007` have no authored physical route;
  that records incomplete physical authoring, not absent piping.

## ProcessStep ↔ Equipment analysis

A step is a process function; equipment is physical inventory. The fragment proves:

- a step may have **0** standalone equipment (`PS-mix`, `PS-split`, `PS-consumer`);
- equipment may have **0** process steps (`FV-101`).

Requiring exactly one in either direction is therefore already falsified.
`PS-pump ↔ P-101` and `PS-vessel ↔ V-101` prove a selected pair can be 1:1 in one
fragment; they do not prove a rule. `PS-hx ↔ E-101` proves a selected process-side
correspondence but not that all exchanger process functions are represented — the
physical item has a second side outside the process graph, which is a concrete
reason to preserve, not encode, a possible N:1.

Duty/standby pumps, parallel trains, jointly realized packaged systems, columns,
reactors, and multi-function packages make 1:N, N:1, and N:M domain-plausible. They
are **not** evidence to implement multiplicities now: the fragment evidences only
the zero cases and selected 1:1 correspondences.

### Zero physical equipment (proven)

A valid process function may have no standalone equipment. Mixing, splitting, and a
process-boundary/black-box consumer are real PFD functions with no equipment tag at
this abstraction. Any model requiring `ProcessStep → exactly one Equipment` is
already falsified by `PS-mix`, `PS-split`, and `PS-consumer`.

### Multiple items realizing one function (domain-plausible, not evidenced)

Duty/standby pumps, parallel trains, and packaged systems are real engineering
cases where several physical items jointly realize one process function. This is
domain-plausible but the fragment does not exercise it, so it is **not** grounds to
implement 1:N now; it is grounds for an architecture that must not forbid it.

### One item participating in several functions (evidence-adjacent, not encoded)

The `PS-hx` model describes only one selected side of `E-101`. A full multi-side
exchanger, column, reactor, or multi-function package can participate in more than
one process function. This establishes a reason to **preserve** possible N:1
without implementing it.

## ProcessStream ↔ physical realization analysis

`S-004` is one directed process intent. Its authored physical evidence is not one
object: it traverses `C-001` and `C-002`, each with a `PipingRealization`, through a
transparent physical valve. This is the decisive negative evidence against each
single-object target:

- `Connection` is topology-only and too small (it is one adjacency of the run).
- `PipingRealization` states how one adjacency is realized and is equally too small.
- `PipingSegment` is a property boundary; `SEG-1` contains the run only because no
  property change splits it today.
- `PipingLine` is a grouping identity; it may change under regrouping or
  renumbering without the process intent changing.

Therefore a `ProcessStream` realization is a **route / collection of existing
physical realization facts**, normally expressed through existing topology and
piping objects rather than duplicated endpoints. This is a semantic target
boundary, not a new `Route` class.

The hard cases, evaluated explicitly:

| Case | Verdict |
|---|---|
| one `ProcessStream` → zero authored physical realization | Required. `S-001`, `S-002`, `S-003`, `S-005`–`S-007` have none; the fragment stays valid. |
| one `ProcessStream` → one physical realization | Possible, but not general. A single-adjacency run could be one realization. |
| one `ProcessStream` → multiple `Connection`s / `PipingRealization`s | **Proven** by `S-004` (`C-001` + `C-002`). |
| one `ProcessStream` → multiple `PipingSegment`s | Domain-plausible; not evidenced here (property changes across the run are absent). |
| one `ProcessStream` → one or multiple `PipingLine`s | Domain-plausible; not evidenced here. |
| physical piping with no `ProcessStream` | Possible. `FV-101` and future physical detail; no converse coverage rule is evidenced. |

## ProcessPort constraint analysis

The prototype evidence (preserved in
[process-fragment-prototype.md](process-fragment-prototype.md)) shows two port
situations:

- **equipment-adjacent ProcessPorts** often correspond naturally 1:1 to a physical
  `Port` (`PS-pump.discharge`, `PS-pump.suction`);
- **junction-adjacent ProcessPorts** do not map honestly to the nearest equipment
  `Port`. Forcing the nearest port invents a tee/node boundary and can collide with
  the adjacent step's legitimate mapping (`PS-mix.out_mixed`, splitting ports).

The current `Port` abstraction intentionally collapses physical nozzle and node
concerns (ADR-0010), so it is insufficient to decide all process-port
correspondence. What is **established** is that any process-port mapping is also a
cross-layer relationship and therefore belongs to the same separate realization
layer, not to either endpoint model. What **remains unresolved** is whether an
honest universal mapping needs a refined physical boundary such as `Nozzle`,
`PipingNode`, or another piping-location concept. This slice introduces none of
them and does not design `ProcessPort`.

## Cardinality matrix

`0:1` means zero-or-one **relationship instances in this fragment/selected case**,
not a future multiplicity declaration. The evidence establishes no canonical
maximum, inverse uniqueness, or obligation to author every real-world relation.

| Relation direction | Proven by fragment | Domain possible | Plausible but not yet evidenced | Not encoded / unsupported |
|---|---|---|---|---|
| `ProcessStep → Equipment` | `0:1` (`PS-mix`, `PS-split`, `PS-consumer`); `1:1` selected pairs | `0:1`, `1:1` | `1:N` jointly realized function, parallel/duty-standby/package | exactly 1; a fixed upper bound; a chosen field shape |
| `Equipment → ProcessStep` | `0:1` (`FV-101`); `1:1` selected pairs | `0:1`, `1:1` | `1:N` multi-side exchanger, column/reactor/package; `N:M` when both directions combine | exactly 1; a fixed inverse list |
| `ProcessStream → physical realization route` | `0:1` streams with no authored facts; `1:N` for `S-004` to two elementary facts | `0:1`, `1:N` | `1:N` across segments/lines; alternative routes | exactly one `Connection`/realization/segment/line; any route schema |
| physical realization route → `ProcessStream` | no universal inverse proven; the `S-004` route serves one stream here | `0:1`, `1:1` | `N:1`/`N:M` where the process abstraction groups or shares physical routing | mandatory inverse coverage or a unique owner |

## Physical-target comparison

| Candidate target | Semantic meaning | `S-004` honestly? | Incomplete authoring? | Cardinality / stability / identity | Result |
|---|---|---|---|---|---|
| `Connection` | one directed physical adjacency | No — only half the run each | zero refs possible, but route lost | too fine; topology id stable; duplicates route selection | Reject as stream target |
| `PipingRealization` | statement that one adjacency has a realization | No alone — both are needed | zero refs possible | too fine; tied to one connection; no independent id | Reject as sole target |
| `PipingSegment` | property boundary | Only accidentally — `SEG-1` holds both facts today | zero refs possible | changes when properties/breaks change; owner-local id | Reject as canonical target |
| `PipingLine` | higher-level grouping/identity | Only accidentally — the line holds the run today | zero refs possible | changes under regrouping/renumbering; may hold unrelated portions | Reject as canonical target |
| collection/path of physical realizations | route realizing one process intent | **Yes** — `C-001` + `C-002` facts | **Yes** — empty/unavailable route stays valid | permits `1:N`; follows topology without restating it; no new identity required now | **Select as semantic boundary** |
| new explicit route concept | would name/own route identity | Could | Could | adds identity/lifecycle not evidenced; risks duplicating topology | Defer |

The candidate comparison is deliberately separate from the decision: the physical
target is a **route of existing realization facts**, not one physical object, and
this is a semantic statement rather than a new class.

## Candidate A–D comparison

| Candidate | Ownership and validation | Partial authoring / evolution | Git-native behavior | Result |
|---|---|---|---|---|
| **A — process-owned forward references** | puts a cross-layer fact on process objects; validation needs `PlantModel` | empty lists valid, but process diffs mix intent with realization | convenient beside intent, yet physical routing changes edit process records | Reject: wrong authoritative owner; asymmetric with physical detail |
| **B — physical-owned reverse references** | puts PFD abstraction on physical objects; validation still spans models | physical refinement forces process-facing edits | physical changes carry process references; duplicate inverse references invite drift | Reject: wrong owner for a route; poor abstraction fit |
| **C — separate realization mapping layer** | relation owned where the separately authored process and physical domains meet; full reference validation belongs at `PlantModel`/future relation submodel | relation may be absent while both domains stay valid with respect to the relationship; endpoints evolve independently | one authored relationship fact in one place; focused add/remove/rename diff | **Accept as architectural boundary** |
| **D — no canonical mapping yet** | preserves independence, leaves ownership unresolved | safe, but repeats a boundary question already foreclosing on evidence | avoids premature schema but gives no durable location | Reject as final outcome: ownership is durable even though schema is not |

## Relation identity / metadata analysis

An anonymous relationship / list membership is enough for every currently evidenced
case. `S-004` needs a relationship to multiple elementary physical facts, but no
current workflow must address, revise, annotate, compare, or reference that
relationship itself. Existing physical identities already identify the
`Connection`, line, and segment facts.

```text
Does a realization relationship need canonical identity?   No, not evidenced.
Does it need metadata?                                     No, not evidenced.
```

Relation kind, status, confidence, engineering maturity, provenance, and revision
are conceivable but are **not** evidenced as required canonical facts. A future need
is not a reason to reserve an `id` field or choose an identified relation object
now. If a later slice needs identity or metadata, that is its own decision.

## Ownership and validation analysis

A future realization layer is a cross-layer submodel — comparable in validation
scope to `PipingModel`, but distinct in semantic role:

```text
local structural rules        -> narrowest future relation container
cross-layer id resolution,    -> PlantModel context, because it holds the process
route eligibility/continuity        and physical domains
inverse consistency
```

`ProcessModel`, `Equipment`/`Port`/`Connection`, and `PipingModel` must not gain a
validity dependency on it. This preserves the current rule that validation belongs
at the narrowest layer with enough context. No validator is implemented here.

## Git-native diff and review analysis

One relationship fact in one separate location keeps a reviewed change legible:

- adding a physical realization to a previously abstract stream changes the physical
  facts and one relationship statement, not both endpoint objects;
- renaming a process or physical id changes its authoritative object plus the
  relationship reference — no mirrored lists to keep in sync;
- removing an alternative route is a local removal.

Bidirectional A+B references would duplicate one engineering assertion, create merge
conflicts around unrelated endpoint edits, and require inverse validation. Line
renumbering or segment regrouping must not change a process relationship that
targets route facts rather than line/segment labels.

## Decision threshold

**Can a durable invariant be stated before implementation? Yes.** The evidence
supports deciding the ownership boundary and the preserved independence, but not a
class name, YAML shape, relation identity, metadata, cardinality limits, route
algorithm, or port refinement. ADR-0016 records only that durable level.

## Conclusion

DeepPlant should own future process ↔ physical realization relationships in a
separate cross-layer realization layer. `ProcessStep` ↔ `Equipment` and
`ProcessStream` ↔ physical route are **different relation kinds** and must not be
forced into one symmetric endpoint-reference pattern. The latter targets a
route/collection of existing physical realization facts, not a single physical
object. No mapping is implemented by this conclusion.

This outcome is consistent with the uncertainty preserved in the prior evidence:
[physical-piping-model.md](physical-piping-model.md) explicitly left Process ↔
physical mapping out of scope, [process-fragment-prototype.md](process-fragment-prototype.md)
kept its junction/exchanger mapping questions open, and
[dexpi/plant-pid-semantic-boundary.md](dexpi/plant-pid-semantic-boundary.md)
established no `ProcessStep` ↔ equipment or `ProcessStream` ↔ piping mapping. This
document synthesizes them; it does not rewrite them.

## Unresolved questions

- The exact future relation classes, authored serialization, and cardinality rules.
- Whether an implemented route relation needs ordered traversal, alternatives, or
  continuity validation.
- Concrete evidence for `1:N`, `N:1`, and `N:M` step/equipment cases.
- The physical boundary required for honest junction-adjacent process ports.
- Any need for relation identity, metadata, provenance, status, or revision.

## Revisit conditions

Revisit only when a scoped DeepPlant-native authoring, review, rendering, validation,
or adapter requirement needs a mapping implementation; when a second fragment proves
a nontrivial step/equipment cardinality; when a stream crosses multiple line/property
boundaries; or when a junction/process-port mapping demonstrably requires a refined
physical boundary. Do not reopen merely for adapter convenience or a class name.

## Related

- [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md) — the
  durable ownership boundary this evidence produced.
- [process-fragment-prototype.md](process-fragment-prototype.md) — the realistic
  fragment and its preserved open mapping questions.
- [physical-piping-model.md](physical-piping-model.md) — physical piping shape
  (ADR-0011); Process ↔ physical remains out of scope there.
- [dexpi/plant-pid-semantic-boundary.md](dexpi/plant-pid-semantic-boundary.md) —
  DEXPI `V2.0.0` physical-boundary evidence; establishes no cross-layer mapping.
- [next-slice-re-evaluation.md](next-slice-re-evaluation.md) — the planning evidence
  that selected this investigation (Issue #39).
- [contracts/process-model.md](../../contracts/process-model.md),
  [contracts/plant-model.md](../../contracts/plant-model.md), and
  [contracts/physical-piping.md](../../contracts/physical-piping.md) — the current
  contracts that still state no mapping is implemented.
