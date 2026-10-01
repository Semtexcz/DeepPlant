---
type: evidence
status: active
canonical_for:
  - next-slice-re-evaluation
read_when:
  - next-task-selection
  - roadmap-change
update_when:
  - new-evidence
depends_on:
  - docs/roadmap.md
  - docs/contracts/index.md
decision: []
evidence:
  - docs/research/qualified-engineering-quantities.md
superseded_by: null
---

# Next-Slice Re-Evaluation After Issue #32

## Outcome card

- **Question investigated:** what is the best evidence-backed next executable
  DeepPlant slice now that Issue #20 (DEXPI 2.0.0 Process subset contract) and
  Issue #32 (qualified-engineering-quantity boundary, ADR-0013) have both
  delivered?
- **Status:** active planning evidence; it selects one bounded next slice and
  authorizes no implementation.
- **Inspection scope and date:** `main` after merged PR #38
  (`684b9845e2cae7b6f6baec2ae4bad642b0140d7e`), the current contracts,
  architecture, direction, roadmap, ADR-0002/0009/0010/0011/0012/0013, the
  realistic fragment, and the GitHub Issue/milestone state, inspected 2026-10-01.
- **Conclusions:**
  1. Exactly one slice is Ready: a process ↔ physical realization
     evidence/decision slice (Issue #39).
  2. Quantity implementation has no DeepPlant-native consumer; port/flow kinds
     and the DEXPI 2.0.1 review advance only the adapter or the core indirectly.
  3. View/editor and rules/diff work stay downstream of semantics and have no
     current unmet use case.
- **Resulting ADRs:** none; a later slice may produce one.
- **Current contracts operationalizing the result:** none; the selection is
  recorded in [roadmap.md](../roadmap.md).
- **Conditions for revisiting:** Issue #39's evidence closes (then re-evaluate),
  or a deferred candidate gains a concrete DeepPlant-native consumer or a
  decisive upstream change.

## Current state

Two implemented, deliberately separate graphs exist and remain independently
valid:

```text
ProcessModel (steps / process ports / streams)
!=
physical topology + PipingModel (equipment / ports / connections /
line -> segment -> realization)
```

No process ↔ physical mapping, no canonical quantity, no port kind, and no PFD/
P&ID view beyond the one read-only process renderer exist. Issue #20 published
the DEXPI subset contract; Issue #32 decided the quantity boundary but
implemented nothing, so every model-level blocker from Issue #22 remains at
runtime.

## Candidate set

```text
A. Process ↔ physical realization boundary — evidence/decision slice
B. Implement the first canonical engineering quantity
C. DEXPI 2.0.1 compatibility review
D. Port-kind / non-material flow semantics
E. Extend PFD / engineering views
F. Engineering rules / semantic diff
```

## Evaluation criteria

Each candidate is rated `high` / `medium` / `low` on: evidence maturity, core
architectural importance, dependency leverage, boundedness, current consumer,
risk of speculative abstraction, reversibility, adapter bias (lower is better),
view/editor leverage, and Git-native engineering leverage. No numeric total is
computed.

## Candidate comparison

| Candidate | Evidence | Core | Leverage | Bounded | Consumer | Speculation risk | Adapter bias | Verdict |
|---|---|---|---|---|---|---|---|---|
| A process ↔ physical | high | high | high | high | high | medium | low | **select** |
| B quantity implementation | split | medium | medium | low | low | high | medium | defer |
| C DEXPI 2.0.1 review | medium | low–medium | medium | high | adapter only | low | high | defer |
| D port / flow kinds | medium | medium | medium | medium | low | high | high | defer |
| E PFD / views | medium | medium | medium | medium | partial | medium–high | low | defer |
| F rules / semantic diff | low | medium | medium | low | low | medium–high | low | defer |

A wins because the missing relationship now sits directly between two implemented
layers, is repeatedly named as unresolved by canonical documents, is demonstrable
on the existing fragment without inventing data, and can end as a bounded
evidence/decision without any production change. B lacks a real owning property
and would create an abstraction ahead of a consumer (AGENTS.md, ADR-0001). C is
useful maintenance but adapter-centric. D has no DeepPlant-native non-material
flow workflow. E and F are downstream of semantics and have no current unmet use
case beyond existing validation.

## Selected next slice

```text
Model: decide process ↔ physical realization boundary   (Issue #39)
```

An evidence-first decision slice that investigates `ProcessStep ↔ Equipment` and
`ProcessStream ↔ physical piping realization`, evaluates cardinality across
0:1 / 1:1 / 1:N / N:1 / N:M, and compares candidate shapes A–D (references on
process objects, reverse references on physical objects, a separate mapping
layer, or no canonical mapping yet). It must not implement any candidate.

## Why alternatives stay deferred

- **Quantity implementation:** no canonical object needs a value yet; the
  boundary is decided, so this waits for a DeepPlant-native consumer.
- **DEXPI 2.0.1 review:** keep the pin; review only when it changes the
  implemented subset, and do not grow canonical semantics for adapter ease.
- **Port / flow kinds:** no non-material DeepPlant workflow exists; DEXPI alone
  is weak evidence.
- **Views / editor and rules / diff:** presentation and checks remain downstream
  of semantics; add them only when a concrete use case appears.

## Issue created

- [#39 — Model: decide process ↔ physical realization boundary](https://github.com/Semtexcz/DeepPlant/issues/39)
  (no milestone; Project Horizon `Now`).

## Roadmap consequence

The operational sequence moves from `#32 → re-evaluate` to
`#39 → re-evaluate from its evidence`, and Issue #39 is the sole explicit
executable `Now` item. No successor task is preselected.

## Revisit condition

Re-evaluate after Issue #39's evidence concludes, or earlier if a deferred
candidate gains an evidence-backed DeepPlant-native consumer.
