---
type: evidence
status: historical
canonical_for:
  - next-slice-re-evaluation-after-issue-32
read_when:
  - planning-evidence-review
  - roadmap-history
depends_on:
  - docs/dev/planning/roadmap.md
  - docs/contracts/index.md
decision: []
evidence:
  - docs/dev/research/qualified-engineering-quantities.md
superseded_by: null
---

# Next-Slice Re-Evaluation After Issue #32

## Outcome card

- **Question investigated:** what next executable DeepPlant slice was selected
  after Issue #20 (DEXPI 2.0.0 Process subset contract) and Issue #32
  (qualified-engineering-quantity boundary, ADR-0013) delivered?
- **Status:** historical planning evidence recording the selection made after
  Issue #32. Current execution state is owned by [roadmap.md](../planning/roadmap.md).
- **Inspection scope and date:** `main` after merged PR #38
  (`684b9845e2cae7b6f6baec2ae4bad642b0140d7e`), the current contracts,
  architecture, direction, roadmap, ADR-0002/0009/0010/0011/0012/0013, the
  realistic fragment, and the GitHub Issue/milestone state, inspected 2026-10-01.
- **Conclusions:**
  1. Issue #39 was selected as the one bounded next evidence/decision slice.
  2. The process ↔ physical relationship has strong architectural evidence but a
     medium current consumer: the existing fragment exposes the unresolved
     boundary, while neither implemented graph requires a mapping to be valid.
  3. Quantity implementation, port/flow kinds, the DEXPI 2.0.1 review,
     view/editor work, and rules/diff work remained deferred.
- **Resulting ADRs:** none; Issue #39 may produce one.
- **Current contracts operationalizing the result:** none; the current planning
  state is maintained in [roadmap.md](../planning/roadmap.md).
- **Conditions for revisiting:** historical only. The mandatory re-evaluation
  gate mechanism was retired in favor of milestone-driven planning
  ([planning/index.md](../planning/index.md)); this record is not revived.

## Current state at inspection

Two implemented, deliberately separate graphs existed and remained independently
valid:

```text
ProcessModel (steps / process ports / streams)
!=
physical topology + PipingModel (equipment / ports / connections /
line -> segment -> realization)
```

No process ↔ physical mapping, no canonical quantity, no port kind, and no PFD/
P&ID view beyond the one read-only process renderer existed. Issue #20 published
the DEXPI subset contract; Issue #32 decided the quantity boundary but
implemented nothing, so every model-level blocker from Issue #22 remained at
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

Each candidate is rated only `high`, `medium`, or `low` across all ten criteria:
evidence maturity, core architectural importance, dependency leverage,
boundedness, current consumer, speculation risk, reversibility, adapter bias,
view/editor leverage, and Git-native engineering leverage. Except where noted,
`high` is more favourable. **Speculation risk** and **adapter bias** are inverted:
`low` is more favourable. No numeric total is computed; the selection remains a
qualitative judgement explained below.

## Candidate comparison

| Candidate | Evidence maturity | Core architectural importance | Dependency leverage | Boundedness | Current consumer | Speculation risk | Reversibility | Adapter bias | View/editor leverage | Git-native engineering leverage | Qualitative outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A process ↔ physical realization | high | high | high | high | medium | medium | high | low | high | high | **select** |
| B quantity implementation | medium | medium | medium | low | low | high | medium | low | medium | medium | defer |
| C DEXPI 2.0.1 review | medium | low | medium | high | low | low | high | high | low | medium | defer |
| D port / flow kinds | medium | medium | medium | medium | low | high | medium | high | medium | medium | defer |
| E PFD / views | medium | medium | medium | medium | low | medium | high | low | high | low | defer |
| F rules / semantic diff | low | medium | medium | low | low | medium | high | low | medium | high | defer |

Candidate A remains the strongest next slice without arithmetic. The missing
relationship sits directly between two implemented layers, canonical documents
repeatedly name it as unresolved, and the realistic fragment demonstrates
plausible correspondences and non-1:1 cases without invented data. Its current
consumer is **medium**, not high: this is architectural evidence for a decision,
not a runtime workflow that presently requires a canonical mapping. The process
and physical/piping layers remain intentionally valid and useful without one.
The work can still end as a bounded, reversible evidence/decision slice with no
production change.

B lacks a real owning property and would create an abstraction ahead of a
consumer (AGENTS.md, ADR-0001). C is useful maintenance but adapter-biased. D
has no DeepPlant-native non-material-flow workflow. E and F are downstream of
semantics and have no current unmet use case beyond existing validation.

## Selected next slice

```text
Model: decide process ↔ physical realization boundary   (Issue #39)
```

An evidence-first decision slice that investigates `ProcessStep ↔ Equipment` and
`ProcessStream ↔ physical piping realization`, evaluates cardinality across
0:1 / 1:1 / 1:N / N:1 / N:M, and compares candidate shapes A–D (references on
process objects, reverse references on physical objects, a separate mapping
layer, or no canonical mapping yet). It must not implement any candidate.

## Why alternatives stayed deferred

- **Quantity implementation:** no canonical object needs a value yet; the
  boundary is decided, so this waits for a DeepPlant-native consumer.
- **DEXPI 2.0.1 review:** keep the pin; review only when it changes the
  implemented subset, and do not grow canonical semantics for adapter ease.
- **Port / flow kinds:** no non-material DeepPlant workflow exists; DEXPI alone
  is weak evidence.
- **Views / editor and rules / diff:** presentation and checks remain downstream
  of semantics; add them only when a concrete use case appears.

## Issue state at inspection

- [#39 — Model: decide process ↔ physical realization boundary](https://github.com/Semtexcz/DeepPlant/issues/39)
  was open and had no milestone. Project V2 Horizon update could not be
  independently verified with the available repository tooling;
  [roadmap.md](../planning/roadmap.md) and Issue #39 are authoritative for this record.

## Roadmap consequence at selection

The operational sequence moved from `#32 → re-evaluate` to
`#39 → re-evaluate from its evidence`, with Issue #39 as the sole explicit
executable `Now` item. No successor task was preselected. Current execution state
remains maintained in [roadmap.md](../planning/roadmap.md), not in this historical record.

## Revisit condition

Historical record. The mandatory re-evaluation gate that produced this record was
retired; further next-slice selection happens through milestone-driven planning
([planning/index.md](../planning/index.md)), not by creating another gate record.
