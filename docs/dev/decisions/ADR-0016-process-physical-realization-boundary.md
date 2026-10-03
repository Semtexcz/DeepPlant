# ADR-0016: Process ↔ Physical Realization Boundary

> Status: Accepted
> Date: 2026-10-03

## Context

DeepPlant has three independently valid model layers today: the process graph
(`ProcessModel`), the physical topology (`Equipment` / `Port` / `Connection`), and
the physical piping-realization submodel (`PipingModel` → `PipingLine` →
`PipingSegment` → `PipingRealization`). No layer references another across the
process/physical boundary, and no process object needs a physical object to
validate (or vice versa).

The realistic fragment proves the graphs genuinely differ in granularity rather
than being two views of one graph:

- `PS-mix` and `PS-split` are valid process functions with no standalone
  `Equipment`, and `PS-consumer` is a boundary beyond the fragment;
- `FV-101` is physical equipment with no `ProcessStep` (transparent at the PFD
  abstraction);
- one process intent `S-004` spans two physical adjacencies (`C-001`, `C-002`) and
  two `PipingRealization`s inside one line/segment;
- four other process streams have no authored physical route at all, and that
  absence is valid.

The full evidence, candidate analysis, cardinality matrix, and target comparison
are in
[process-physical-realization-boundary.md](../research/process-physical-realization-boundary.md)
(Issue #39). The question this ADR answers is narrow — **where a future process ↔
physical realization statement belongs** — not whether a mapping implementation is
needed now.

## Options

- **A — process-owned forward references.** `ProcessStep.realized_by`,
  `ProcessStream.realized_by`, and similar fields on process objects.
- **B — physical-owned reverse references.** `Equipment.realizes`,
  `PipingRealization.realizes_process_stream`, and similar fields on physical
  objects.
- **C — a separate cross-layer realization layer.** Realization relationships live
  where the two independently valid layers meet, not on either endpoint.
- **D — no canonical ownership decision yet.** Keep the boundary explicitly
  unresolved.

## Decision

**C is accepted as a durable architectural boundary, on these explicit terms:**

1. **Future process ↔ physical realization relationships are owned in a separate
   cross-layer realization layer, not on `ProcessStep`, `ProcessStream`,
   `ProcessPort`, `Equipment`, `Port`, `Connection`, `PipingRealization`,
   `PipingSegment`, or `PipingLine`.**
2. **The endpoint models remain independently valid.** The process model neither
   requires physical realization nor becomes invalid when it is absent; physical
   topology and piping neither require process references nor become invalid when
   they are absent.
3. **The architecture must permit zero relationship participation in both endpoint
   directions.** The fragment proves zero equipment for valid process steps and zero
   process steps for physical equipment. It must also not preclude future `1:N`,
   `N:1`, or `N:M` cases, but this ADR neither encodes nor validates them.
4. **A `ProcessStream` realization targets a physical route / collection of existing
   physical realization facts, not one `Connection`, `PipingRealization`,
   `PipingSegment`, or `PipingLine`.** It must tolerate no authored route while
   physical engineering is incomplete.
5. **Step/equipment and stream/route are domain-specific relation kinds.** They are
   not forced into one symmetric generic mapping schema merely because both cross
   the same layer boundary.
6. **No relation identity, metadata, schema, field, YAML shape, validator, or
   runtime behavior is decided or introduced.** A future implementation must earn
   each of those from a concrete workflow and evidence.
7. **Cross-layer referential validation, if implemented, belongs at the narrowest
   future realization container with enough `PlantModel` context.** It must not be
   pushed into either endpoint layer.

### Architectural decision versus implementation shape

This ADR decides only the **ownership boundary** and the **independence
invariant**. It deliberately does not decide:

```text
architectural decision (this ADR)     implementation shape (a later slice)
----------------------------------    -------------------------------------
ownership lives in a separate layer   class names, fields, YAML section
endpoint models stay independent      local rules, cardinality limits
route, not single object, is the      route representation, ordering, continuity
  semantic stream target
zero participation must be valid      optionality/requiredness encoding
no identity/metadata today            relation ids, status, provenance
```

A later implementation Issue must establish its own evidence for the shape above;
this ADR authorizes none of it.

## Rejected alternatives

| Alternative | Why rejected |
|---|---|
| **A — process-owned forward references** | Puts a cross-layer fact on process objects. A change to physical routing would edit process intent records, and full reference resolution still needs `PlantModel`. It also treats the physical side as an attribute of the process side, which the fragment's `FV-101` and unrealized streams contradict. |
| **B — physical-owned reverse references** | Puts the PFD abstraction on physical objects, so refining the physical model forces process-facing edits. A `ProcessStream` realization is a route over several facts, which does not fit one physical object's field. Bidirectional A+B references would duplicate one engineering assertion. |
| **Forcing one symmetric mapping schema for step/equipment and stream/route** | The two relationships differ in kind: step/equipment is an object/function correspondence, stream/route is a relationship to an aggregate path. A single symmetric shape would misrepresent one of them. |
| **D — no canonical decision** | The ownership boundary is durable on current evidence even though the schema is not; leaving it undecided would keep a recurring ambiguity open without cause. |

## Consequences

### Positive

- One relationship fact has one authoritative authored location, improving Git
  diffs, review, merge behaviour, and renames without mirrored endpoint lists.
- Process intent stays distinct from physical topology and from physical
  piping properties and groupings.
- The architecture accommodates incomplete model maturity honestly: neither layer
  becomes invalid while the other is incomplete.
- The durable question ("who owns the relationship?") is answered without
  prematurely freezing a schema.

### Negative

- No user can author or validate a mapping yet; the current contracts remain
  implementation-free on that point.
- A future slice must still determine the representation, local rules, route
  semantics, cardinality limits, and whether a refined physical boundary is needed
  for `ProcessPort` mappings.

## Explicitly not decided

- Any `realized_by`, reverse-reference, mapping, route, relation-id, metadata, or
  new `PlantModel` field.
- `Nozzle`, `PipingNode`, port kinds, a `ProcessPort` redesign, and process-port
  mapping.
- Line routing, pipe identity, DEXPI Plant/P&ID import/export, GUI behaviour, and
  any DEXPI 2.0.1 review.

## Revisit When

- A concrete DeepPlant-native authoring, review, rendering, or validation workflow
  needs cross-layer realization.
- Evidence needs relation identity, status, provenance, revision, or alternatives.
- A physical route cannot be described by existing realization/topology facts.
- Junction-adjacent `ProcessPort`s require a physical boundary more precise than
  `Port`.

## Related

- [process-physical-realization-boundary.md](../research/process-physical-realization-boundary.md)
  — the evidence, cardinality analysis, target comparison, and candidates.
- [ADR-0011](ADR-0011-canonical-physical-piping-realization.md) — physical piping
  realization; remains independent and does not decide this relationship.
- [ADR-0010](ADR-0010-dexpi-plant-pid-semantic-boundary.md) — the `Port` /
  `Connection` boundary and the collapsed `Nozzle`/`PipingNode` abstraction.
- [ADR-0012](ADR-0012-process-step-single-classification-axis.md) and
  [ADR-0013](ADR-0013-qualified-engineering-quantity-boundary.md) — sibling
  "decide a boundary, implement nothing" decisions.
- [contracts/process-model.md](../../contracts/process-model.md),
  [contracts/plant-model.md](../../contracts/plant-model.md), and
  [contracts/physical-piping.md](../../contracts/physical-piping.md) — current
  contracts that still state no mapping is implemented.
- [process-fragment-prototype.md](../research/process-fragment-prototype.md) —
  the preserved open junction/exchanger mapping questions.
