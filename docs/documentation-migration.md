---
type: governance
status: active
canonical_for:
  - documentation-migration-inventory
read_when:
  - documentation-change
  - documentation-structure-change
update_when:
  - document-moved
  - document-split
  - documentation-architecture-change
depends_on:
  - docs/conventions.md
  - docs/index.md
decision:
  - docs/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# Documentation Migration Inventory

> **Question this document answers:** which existing documents stay where they
> are, which should move, and which mix independent responsibilities and should be
> split — and in what order?

This is the evidence-backed inventory behind
[ADR-0014](decisions/ADR-0014-documentation-architecture-v2.md) and the
operational rules in [conventions.md](conventions.md). It is planning evidence
about **current** paths; it does not move anything itself. Update it as
migrations land, and keep exactly one canonical copy of every document.

## How to read this

- **Authority** — the knowledge kind the document owns (contract / decision /
  evidence / history / current / governance / navigation).
- **Audiences** — who reads it (`user`, `dev`, `agent`); **shared** means it is
  canonical for more than one audience and therefore stays in the shared layer.
- **Link stability** — how costly it is to break inbound links (`high` / `medium`
  / `low`).
- **Action** — `KEEP` (stay, in place), `MOVE` (relocate later), `SPLIT` (divide
  by responsibility later), or `ADD` (new in this slice).

`KEEP` is the default. A document moves only when the migration cost is
outweighed by a durable benefit and its inbound links can be reconciled in one
pass (see the move procedure in [conventions.md](conventions.md)).

## Entry points

| Current path | Responsibility | Authority | Audiences | Link stability | Action | Candidate target | Reason |
|---|---|---|---|---|---|---|---|
| `README.md` | Repository/product front door | navigation | user, dev | high | KEEP | — | External and internal inbound links; canonical GitHub entry point |
| `docs/index.md` | Top-level audience/authority router | navigation | user, dev, agent | high | KEEP | — | The single starting router |
| `docs/user/index.md` | User navigation map | navigation | user | n/a | ADD | — | Proves the audience layer exists |
| `docs/dev/index.md` | Developer/agent navigation and task routing | navigation | dev, agent | n/a | ADD | — | Proves the audience layer exists |
| `AGENTS.md` | Agent bootstrap and invariants | navigation | agent | high | KEEP | — | Root agent entry point |
| `.agents/context-map.yaml` | Machine-readable agent context routing | navigation | agent | medium | KEEP | — | Existing routing mechanism |

## Canonical contracts (shared)

| Current path | Responsibility | Authority | Audiences | Link stability | Action | Candidate target | Reason |
|---|---|---|---|---|---|---|---|
| `docs/contracts/cli.md` | CLI surface | contract | user, dev | medium | KEEP | — | Cross-audience canonical |
| `docs/contracts/yaml-format.md` | Authored YAML shape and load/save | contract | user, dev | medium | KEEP | — | Cross-audience canonical |
| `docs/contracts/plant-model.md` | Physical/plant model | contract | dev, agent | medium | KEEP | — | Canonical, stable |
| `docs/contracts/process-model.md` | Process graph model | contract | dev, agent | medium | KEEP | — | Canonical, stable |
| `docs/contracts/physical-piping.md` | Piping realization | contract | dev, agent | medium | KEEP | — | Canonical, stable |
| `docs/contracts/dexpi-process-adapter.md` | DEXPI Process adapter | contract | dev, agent | medium | KEEP | — | Canonical, stable |
| `docs/rendering.md` | Headless renderer contract | contract | dev, agent | medium | KEEP in place | `docs/contracts/rendering.md` | Canonical in place; co-location deferred, not an authority change |
| `docs/svg-symbols.md` | SVG symbol/anchor contract | contract | dev, agent | medium | KEEP in place | `docs/contracts/svg-symbols.md` | Same as `rendering.md` |

## Canonical current and governance documents (shared)

| Current path | Responsibility | Authority | Audiences | Link stability | Action | Candidate target | Reason |
|---|---|---|---|---|---|---|---|
| `docs/architecture.md` | Boundary map | current | dev, agent | high | KEEP | — | Widely linked; in `AGENTS.md` and `context-map.yaml` |
| `docs/workflow.md` | Change loop | governance | dev, agent | high | KEEP | — | Context-map `always` |
| `docs/quality.md` | Quality gates | governance | dev, agent | medium | KEEP | — | Context-map `always` |
| `docs/planning.md` | Planning governance | governance | dev, agent | medium | KEEP | — | Stable |
| `docs/roadmap.md` | Current state and next direction | current | dev, agent | high | KEEP | — | Context-map `always` |
| `docs/direction.md` | Capability progression | current | dev | medium | KEEP | — | Stable |
| `docs/product.md` | Product thesis and non-goals | current | user, dev | medium | KEEP | — | Cross-audience canonical |
| `docs/conventions.md` | Documentation conventions | governance | dev, agent | medium | KEEP | — | Canonical governance; Makefile-validated path |
| `docs/standards.md` | Standards policy + registry + licensing evidence | governance (mixed) | dev, agent | medium | SPLIT (future) | `standards.md` (policy) + registry + evidence doc | Mixes three independently maintained responsibilities |
| `docs/documentation-migration.md` | This migration inventory | governance | dev, agent | low | ADD | — | The inventory itself |

## Authority layers

| Current path | Responsibility | Authority | Audiences | Link stability | Action | Candidate target | Reason |
|---|---|---|---|---|---|---|---|
| `docs/decisions/` | Decision records | decision | user, dev, agent | medium | KEEP | — | Authority layer; stable URLs |
| `docs/research/` | Evidence index and evidence documents | evidence | dev, agent | medium | KEEP | — | Authority layer |
| `docs/history/` | Completion history | history | dev, agent | low | KEEP | — | Authority layer |

## Root-level evidence and prototype documents (migration candidates)

These are canonical evidence today but sit at the `docs/` root, mixing evidence
with the current-document layer. They are `MOVE` candidates into `docs/research/`
once their inbound links can be reconciled in one pass.

| Current path | Responsibility | Authority | Audiences | Link stability | Action | Candidate target | Reason |
|---|---|---|---|---|---|---|---|
| `docs/dexpi-process-spike.md` | DEXPI Process interoperability evidence | evidence | dev, agent | medium | MOVE (future) | `docs/research/dexpi/` | Evidence, not current truth |
| `docs/dexpi-plant-pid-spike.md` | DEXPI Plant/P&ID boundary evidence | evidence | dev, agent | medium | MOVE + SPLIT (future) | `docs/research/dexpi/` | Evidence; also mixes several research questions |
| `docs/dexpi-exchanging-thermal-energy-evidence.md` | `ExchangingThermalEnergy` evidence | evidence | dev, agent | medium | MOVE (future) | `docs/research/dexpi/` | Evidence, not current truth |
| `docs/physical-piping-model.md` | Piping design evidence | evidence | dev, agent | medium | MOVE (future) | `docs/research/` | Evidence behind a contract |
| `docs/process-topology.md` | Process-topology evidence | evidence | dev, agent | medium | MOVE (future) | `docs/research/` | Evidence behind a contract |
| `docs/process-fragment-prototype.md` | Prototype modelling evidence | evidence | dev, agent | medium | MOVE (future) | `docs/research/` | Prototype evidence |
| `docs/process-step-classification.md` | Step-classification evidence | evidence | dev, agent | medium | MOVE (future) | `docs/research/` | Evidence behind ADR-0012 |
| `docs/reference-products.md` | Reuse/reference landscape | evidence | dev, agent | low | MOVE (future) | `docs/research/` | Reference research |

The `MOVE` targets are directional. A move happens only after its inbound links
(including `docs/research/index.md`, contract front matter, and ADR links) are
updated in the same change.

## `standards.md` — explicit split assessment

`docs/standards.md` mixes three independently maintained responsibilities with
different lifecycles:

```text
active policy               restricted-standards rules, symbol-provenance
                            policy, verification vocabulary        -> current
registry / reference        the standards registry and DEXPI entry  -> current
evidence                    source and licensing assessments, with
                            inspection dates                       -> evidence
```

The document itself records this (its authority note points here as outstanding
migration work). Split is recorded as a **future** action, not performed in this
slice: a policy document, a registry/reference inventory, and a source/licence
evidence document. Until then, the policy sections are the active part and the
assessments are evidence with their own dates.

## Proposed incremental sequence

Directional, not a pre-approved backlog. Each step is its own bounded,
independently reviewable change; no Issues are created in advance.

```text
1. Documentation Architecture v2        (this slice — ADR-0014 + this inventory)
2. User documentation migration         (populate docs/user/ where genuinely needed)
3. Developer documentation migration    (populate docs/dev/ where genuinely needed)
4. Atomicity / duplication cleanup      (standards.md split; root-evidence moves;
                                         spike splits — no cosmetic reformatting)
5. Optional renderer/search integration (only if a real need appears)
```

## Related

- [decisions/ADR-0014-documentation-architecture-v2.md](decisions/ADR-0014-documentation-architecture-v2.md)
  — the decision behind this inventory.
- [conventions.md](conventions.md) — KEEP / MOVE / SPLIT rules and the move
  procedure.
- [index.md](index.md) — the audience/authority router.
- [research/index.md](research/index.md) — evidence index.

