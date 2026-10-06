---
type: history
status: historical
canonical_for:
  - retired-planning-gate-decisions
read_when:
  - roadmap-history
  - planning-evidence-review
depends_on:
  - docs/dev/planning/roadmap.md
  - docs/dev/history/implementation-slices.md
decision: []
evidence:
  - docs/dev/research/next-slice-re-evaluation.md
superseded_by: null
---

# Retired Planning-Gate Decisions

## Outcome card

- **Question investigated:** which reusable slices did the previously mandatory
  issue-driven **re-evaluation gates** select, and what decision evidence did
  those gates produce?
- **Status:** historical record. The gate mechanism is retired; the current
  roadmap is milestone-driven ([roadmap.md](../planning/roadmap.md)).
- **Inspection scope and date:** the retired `roadmap.md` gate narratives
  (post-#82, post-#85, post-#97), reviewed 2026-10-06.
- **Conclusions:** the gates selected a sequence of foundation and product
  slices; their unique reasoning is preserved here so it stays traceable without
  remaining operational governance.
- **Resulting ADRs:** none introduced by the gates themselves.
- **Current contracts operationalizing the result:** none; delivered outcomes are
  in the [contracts](../../contracts/index.md) and the
  [implementation-slice history](implementation-slices.md).
- **Conditions for revisiting:** this record is complete; it is not revived.

> **Status:** historical record, preserved when the mandatory re-evaluation gate
> mechanism was retired. It answers *what the gates decided and why*, not *what
> must hold now*.

## Why this record exists

The former roadmap organized work around `Now`/`Next` horizons and a mandatory
**re-evaluation gate** that ran after a small number of Issues completed. Each
gate produced a selection whose reasoning was more detailed than the milestone
structure that replaced it. That unique evidence is preserved here so retiring
the mechanism does not lose it.

## Gate after #39 / #69 / #70

Selected [#75 — Engineering Editor: first interactive Process/PFD vertical
slice](https://github.com/Semtexcz/DeepPlant/issues/75) as the smallest
executable slice. Process/PFD had the strongest complete executable substrate:
`ProcessModel`, structural validation, the realistic process example, the
deterministic headless renderer, the Process/PFD SVG symbol/anchor contract, and
the completed UX (#69) and reuse-first GUI (#70) architectures. The physical/
P&ID side had no equivalent presentation/symbol contract, so the first GUI slice
remained Process/PFD-only. The preceding cross-layer evidence is
[process-physical-realization-boundary.md](../research/process-physical-realization-boundary.md)
and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md).

The re-evaluation from the #75 implementation evidence found the read-only slice
needed foundation hardening before more product capability was layered on it,
and selected [#79](https://github.com/Semtexcz/DeepPlant/issues/79) followed by
the dependency-ordered frontend work #80 → #81 → #82.

## Gate after #82

Selected exactly one product capability: [#85 — Establish independent DeepPlant
Core and standalone editor distribution](https://github.com/Semtexcz/DeepPlant/issues/85).

The published gate corrected an earlier draft of itself. That draft had selected
#89 (project format + portable package) and classified #85 as a strategic later
capability. Review found this deferred #85 despite #85's explicit requirement
that standalone distribution be proven before the editor grows further. The
decision was re-evaluated against Issue #85 and the then-current
checkout-dependent editor runtime: the delivered editor ran only from a
development checkout and resolved built SPA assets from `apps/editor/dist`. The
strongest missing evidence was therefore standalone distributability, not
project persistence. Reasoning: the read path had been proven, and the next
architectural claim to test was whether the application could be shipped to an
engineering user without a development checkout — a test cheaper to run while the
application was still small and read-only.

#85 was decomposed into two child slices, both delivered: the self-contained
distribution foundation (PR #92) and the native desktop host (Issue #93, merged
through PR #95). #85 is complete.

Dependencies recorded by this gate (not a fabricated serial chain): `#88 → #85`
and `#89 → #85` are **not** hard dependencies; the repository already carried an
application version sufficient for versioned development artifacts, and today's
`plant.yaml` input was sufficient to verify the standalone application
architecture. `#77` and `#84` remained independent governance/maintenance work.

## Gate after #85

Selected the empty shared Editor workspace / optional active project as the sole
next product capability (after packaged-smoke parity hardening): Issue #97. It is
**delivered** — the standalone Editor launches directly into the ordinary shared
Vue workspace with `active project = none`.

## Gate after #97 — never executed

The post-#97 gate was marked "ready to execute" but was not executed before the
gate mechanism was retired. Its unselected candidate set was recorded as a strong
candidate, not a commitment:

```text
#89  project format and portable package
     first semantic mutation + Save
     presentation-state persistence
#99  semantic-validity vs view-availability UX
#88  release/version infrastructure
     P&ID
     process ↔ physical realization
```

#89 was noted as especially strong because the workspace had gained a
first-class notion of what document it opens and future Save/Open needs a
persistence contract. Retirement of the gate means this list is historical; the
current milestone selection lives in [roadmap.md](../planning/roadmap.md) and
future Issues are selected through ordinary refinement
([planning/index.md](../planning/index.md)).

## Related

- [implementation-slices.md](implementation-slices.md) — delivered work.
- [roadmap.md](../planning/roadmap.md) — current milestone structure.
- [planning/index.md](../planning/index.md) — current selection workflow.
- [next-slice-re-evaluation.md](../research/next-slice-re-evaluation.md) — the
  earlier post-#32 gate record.
