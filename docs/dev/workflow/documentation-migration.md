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
  - docs/dev/workflow/conventions.md
  - docs/index.md
decision:
  - docs/dev/decisions/ADR-0015-documentation-architecture-v2-1.md
  - docs/dev/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# Documentation Migration Inventory

> **Question this document answers:** for every existing document, what audience
> does it serve, what authority does it own, where should it physically live
> under Documentation Architecture v2.1, and in what order should it move?

This is the evidence-backed inventory behind
[ADR-0015](../decisions/ADR-0015-documentation-architecture-v2-1.md) (v2.1) and the
operational rules in [conventions.md](conventions.md). It replaces the initial v2
inventory, which defaulted most root paths to `KEEP` because they already existed.
That is a migration-cost argument, not an ownership argument, and it is no longer
how an action is chosen.

## The v2.1 ownership boundary

```text
shared  = canonical documents genuinely needed across audiences;
          today, cross-audience contracts under docs/contracts/**
user    = how to use DeepPlant
dev     = how DeepPlant works, why it works that way, how to change it,
          evidence, planning, and development history
```

Two rules decide ownership:

1. **`canonical != shared-directory`.** A document is canonical when it is the
   single authoritative home for its knowledge type. Canonical content may be
   developer-owned (`docs/dev/**`) or user-owned (`docs/user/**`). Only content
   genuinely needed by more than one audience belongs in the shared layer.
2. **`audience != knowledge authority`.** Authority decides what kind of truth
   the document owns (current / contract / decision / evidence / history /
   governance / navigation); audience decides who primarily needs it. Physical
   location follows audience ownership unless the content is genuinely
   cross-audience.

The shared documentation layer is therefore deliberately narrow. Today,
`docs/contracts/**` is reserved for genuinely cross-audience contracts. A document
does **not** enter that directory merely because its authority is `contract`, and
does not stay at the root merely because it has many links; path stability is a
migration cost to weigh, not proof of shared ownership.

## How to read this inventory

- **Audience** — the primary reader: `user`, `dev`/`agent`, or `shared` for the
  genuinely cross-audience contract layer.
- **Authority** — the knowledge kind the document owns.
- **Action** — `KEEP` (path and owner are already right), `MOVE` (relocate under
  its audience layer), `SPLIT` (divide by responsibility, then move the parts),
  or `ADD` (new, owned by this architecture but not created by this decision).
- **Link cost** — measured inbound references across the repository (files
  referencing the document), a proxy for migration effort. `high` ≥ 30, `medium`
  10–29, `low` < 10.

```text
KEEP does not mean "the path already exists".
MOVE does not mean "a cleaner taxonomy is prettier".
```

Each `MOVE`/`SPLIT` is a separate bounded change that reconciles inbound links
in one pass (see the move procedure in [conventions.md](conventions.md)).

## Target tree

Directional target for v2.1. It is not permission to create empty directories: a
folder appears only when a real document moves into it. Exact basenames inside a
folder may be finalized in that folder's migration slice.

```text
docs/
├── index.md
├── user/
│   ├── index.md
│   ├── getting-started.md
│   ├── concepts/
│   │   └── what-is-deepplant.md
│   ├── how-to/
│   │   ├── author-plant-yaml.md
│   │   ├── validate-a-model.md
│   │   ├── diagnose-validation-errors.md
│   │   └── render-process-svg.md
│   └── reference/
│       └── index.md
├── dev/
│   ├── index.md
│   ├── architecture/
│   ├── workflow/
│   ├── planning/
│   ├── reference/
│   ├── decisions/
│   ├── research/
│   └── history/
└── contracts/
    ├── index.md
    ├── plant-model.md
    ├── process-model.md
    ├── physical-piping.md
    ├── yaml-format.md
    ├── cli.md
    └── rendering.md
```

## Repository-role exceptions and global navigation

These paths keep their current location because of their **repository or tooling**
role, not because root placement makes them shared. `README.md` and `VISION.md`
serve a broad public/repository audience; `AGENTS.md` and `project/brief.md` are
developer/agent-oriented repository-role exceptions. `docs/index.md` is global
navigation between audiences, not shared documentation.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `README.md` | shared | navigation | KEEP | — | GitHub/product front door; external inbound links | high |
| `VISION.md` | shared | governance (vision) | KEEP | — | Durable product vision; anchor of the planning hierarchy | high |
| `AGENTS.md` | dev/agent | navigation | KEEP | — | Root agent bootstrap and invariants | high |
| `project/brief.md` | dev/agent | current (project) | KEEP | — | `project/` role; project brief | medium |
| `docs/index.md` | shared | navigation | KEEP | — | Global navigation between audiences; not part of the shared documentation layer | high |
| `docs/dev/index.md` | dev/agent | navigation | KEEP | — | Developer map; task → context routing | medium |
| `docs/user/index.md` | user | navigation | KEEP | — | User map; now a real task router over the user pages | low |
| `.agents/context-map.yaml` | dev/agent | navigation | KEEP | — | Machine-readable agent routing | medium |

## Shared documentation layer — cross-audience `docs/contracts/`

The only genuinely shared documentation layer. Each entry is independently
justified as needed by more than one audience; contract authority alone is not
sufficient for placement here.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `docs/contracts/index.md` | shared | navigation | KEEP | — | Contract index; cross-audience | medium |
| `docs/contracts/cli.md` | shared | contract | KEEP | — | Users run the CLI; developers implement it | medium |
| `docs/contracts/yaml-format.md` | shared | contract | KEEP | — | Users author YAML; developers load/save it | medium |
| `docs/contracts/plant-model.md` | shared | contract | KEEP | — | Canonical model semantics for both audiences | medium |
| `docs/contracts/process-model.md` | shared | contract | KEEP | — | Canonical model semantics for both audiences | medium |
| `docs/contracts/physical-piping.md` | shared | contract | KEEP | — | Canonical model semantics for both audiences | medium |
| `docs/contracts/rendering.md` | shared | contract | KEEP | — | Public renderer API and output behaviour are needed by callers/users and implementers | medium (17) |

## Developer reference layer — `docs/dev/reference/`

Developer-only canonical reference belongs here when it is neither workflow or
governance, an ADR, research/evidence, history, nor a genuinely cross-audience
contract. It is a narrow ownership category, not a generic dumping ground.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `docs/dev/reference/dexpi-process-adapter.md` | dev/agent | contract | KEEP | — | Adapter implementers/integrators need its supported-subset and fail-closed contract; users do not need it to use DeepPlant | medium |
| `docs/dev/reference/svg-symbols.md` | dev/agent | contract | KEEP | — | Renderer/symbol developers need the packaged asset and anchor contract; it is not user-facing reference | medium (20) |

`rendering.md`, `svg-symbols.md`, and `dexpi-process-adapter.md` are classified
independently. The public renderer API is cross-audience; the SVG asset/anchor and
DEXPI adapter contracts are developer-only.

## Developer authority layer — architecture, governance, planning

Canonical developer/agent content. It is authoritative without being shared; it
moved out of the shared root into `docs/dev/**`. The Phase 3A slice relocated the
architecture and workflow/governance rows, the Phase 3B slice relocated the
planning rows, and the Phase 3C slice relocated the decision, evidence, and
history rows (the two inventories below); all of them are now `KEEP` at their
v2.1 paths.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `docs/dev/architecture/index.md` | dev/agent | current | KEEP | — | Boundary map; developer/agent-only reading (relocated in Phase 3A) | high (41) |
| `docs/dev/workflow/index.md` | dev/agent | governance | KEEP | — | Change loop; developer/agent process (relocated in Phase 3A) | medium (16) |
| `docs/dev/workflow/quality.md` | dev/agent | governance | KEEP | — | Quality gates; developer/agent process (relocated in Phase 3A) | medium (15) |
| `docs/dev/workflow/conventions.md` | dev/agent | governance | KEEP | — | Documentation governance; a change-process rule (relocated in Phase 3A) | medium (16) |
| `docs/dev/workflow/documentation-migration.md` | dev/agent | governance | KEEP | — | This inventory; relocated in Phase 3A | medium (10) |
| `docs/dev/planning/index.md` | dev/agent | governance | KEEP | — | Planning governance; relocated in Phase 3B (was `docs/planning.md`) | medium (12) |
| `docs/dev/planning/roadmap.md` | dev/agent | current | KEEP | — | Current execution state and next direction; relocated in Phase 3B (was `docs/roadmap.md`) | high (34) |
| `docs/dev/planning/direction.md` | dev/agent | current | KEEP | — | Long-term capability progression; relocated in Phase 3B (was `docs/direction.md`) | medium (18) |
| `docs/dev/planning/product.md` | dev/agent | current | KEEP | — | Internal product/planning thesis; relocated in Phase 3B (was `docs/product.md`); its user link is transitional and will be replaced by `docs/user/concepts/what-is-deepplant.md` | medium (11) |
| `docs/dev/workflow/standards.md` | dev/agent | governance | KEEP | — | Active standards usage and symbol-provenance policy; created by the Phase 6 split of `docs/standards.md` | medium (20) |
| `docs/dev/reference/standards-registry.md` | dev/agent | reference | KEEP | — | Current standards/specification lookup data; created by the Phase 6 split of `docs/standards.md` | medium (12) |
| `docs/dev/research/standards-licensing-evidence.md` | dev/agent | evidence | KEEP | — | Source, licence, and provenance investigation; created by the Phase 6 split of `docs/standards.md` | medium (10) |

`product.md` and `VISION.md` need a deliberate distinction: `README.md` remains
the concise product/repository front door; `VISION.md` remains the durable
public-facing long-term thesis; `product.md` is internal product/planning reasoning
and belongs with planning. Until user concepts exist, `docs/user/index.md` labels
its link to `product.md` as transitional. A future
`docs/user/concepts/what-is-deepplant.md` will own the user-facing explanation;
this correction does not create it.

## Developer authority layer — decisions, evidence, history

The Phase 3C slice relocated the existing decision, research/evidence, and
history authority directories into `docs/dev/**`. Their paths are now canonical
and each is `KEEP`; the decision, evidence, and history responsibilities remain
separate authority classes and are not merged.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `docs/dev/decisions/**` | dev/agent | decision | KEEP | — | Canonical decision records; developer-owned (relocated in Phase 3C; was `docs/decisions/**`) | high |
| `docs/dev/decisions/index.md` | dev/agent | navigation | KEEP | — | Decision index (relocated in Phase 3C; was `docs/decisions/index.md`) | high |
| `docs/dev/research/**` | dev/agent | evidence | KEEP | — | Canonical evidence; developer-owned (relocated in Phase 3C; was `docs/research/**`) | medium |
| `docs/dev/research/index.md` | dev/agent | navigation | KEEP | — | Evidence index (relocated in Phase 3C; was `docs/research/index.md`) | medium |
| `docs/dev/history/implementation-slices.md` | dev/agent | history | KEEP | — | Completion history; developer-owned (relocated in Phase 3C; was `docs/history/implementation-slices.md`) | medium |

Phase 3C moved only the documents that already lived under `docs/research/**`.
The remaining root-level evidence and prototype documents were relocated into
`docs/dev/research/` by Phase 5 (5A for the DEXPI cluster, 5B for the five
remaining documents).

## Root evidence and prototypes → `docs/dev/research/`

Evidence and prototype documents relocated from the `docs/` root into
`docs/dev/research/`. They are not shared: only developers, agents, and
decision-makers read them.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `docs/dev/research/dexpi/process-adapter-spike.md` | dev/agent | evidence | KEEP | — | DEXPI Process interoperability evidence; relocated in Phase 5A; was `docs/dexpi-process-spike.md` | medium (16) |
| `docs/dev/research/dexpi/exchanging-thermal-energy.md` | dev/agent | evidence | KEEP | — | `ExchangingThermalEnergy` mapping evidence; relocated in Phase 5A; was `docs/dexpi-exchanging-thermal-energy-evidence.md` | medium (14) |
| `docs/dev/research/dexpi/plant-pid-semantic-boundary.md` | dev/agent | evidence | KEEP | — | Physical topology / piping boundary evidence; from the Phase 5A split of `docs/dexpi-plant-pid-spike.md` | medium |
| `docs/dev/research/dexpi/plant-pid-instrumentation.md` | dev/agent | evidence | KEEP | — | Instrumentation / signal evidence; from the Phase 5A split of `docs/dexpi-plant-pid-spike.md` | medium |
| `docs/dev/research/dexpi/plant-pid-presentation.md` | dev/agent | evidence | KEEP | — | Presentation / graphics evidence; from the Phase 5A split of `docs/dexpi-plant-pid-spike.md` | medium |
| `docs/dev/research/physical-piping-model.md` | dev/agent | evidence | KEEP | — | Design evidence behind a contract (relocated in Phase 5B; was `docs/physical-piping-model.md`) | low (8) |
| `docs/dev/research/process-topology.md` | dev/agent | evidence | KEEP | — | Process-topology evidence behind a contract (relocated in Phase 5B; was `docs/process-topology.md`) | low (8) |
| `docs/dev/research/process-fragment-prototype.md` | dev/agent | evidence | KEEP | — | Prototype modelling evidence (relocated in Phase 5B; was `docs/process-fragment-prototype.md`) | low (5) |
| `docs/dev/research/process-step-classification.md` | dev/agent | evidence | KEEP | — | Evidence behind ADR-0012 (relocated in Phase 5B; was `docs/process-step-classification.md`) | low (8) |
| `docs/dev/research/reference-products.md` | dev/agent | evidence | KEEP | — | Reference/reuse landscape research (relocated in Phase 5B; was `docs/reference-products.md`) | low (4) |

## Evidence and prototype cleanup — the Phase 5 slices

Phase 5 decomposes into an independently reviewable DEXPI cluster slice and a
remaining root-evidence slice, both now complete:

```text
5. Evidence and prototype cleanup — DONE

   5A. DEXPI evidence cluster — DONE
       docs/dexpi-process-spike.md
           → docs/dev/research/dexpi/process-adapter-spike.md

       docs/dexpi-exchanging-thermal-energy-evidence.md
           → docs/dev/research/dexpi/exchanging-thermal-energy.md

       docs/dexpi-plant-pid-spike.md
           → SPLIT into:
             docs/dev/research/dexpi/plant-pid-semantic-boundary.md
             docs/dev/research/dexpi/plant-pid-instrumentation.md
             docs/dev/research/dexpi/plant-pid-presentation.md

   5B. remaining root evidence/prototypes — DONE
       docs/physical-piping-model.md
           → docs/dev/research/physical-piping-model.md

       docs/process-topology.md
           → docs/dev/research/process-topology.md

       docs/process-fragment-prototype.md
           → docs/dev/research/process-fragment-prototype.md

       docs/process-step-classification.md
           → docs/dev/research/process-step-classification.md

       docs/reference-products.md
           → docs/dev/research/reference-products.md

Phase 5 — COMPLETE
Phase 6 — COMPLETE (the `standards.md` authority split)

Phases 1–6 — COMPLETE
Structural migration: COMPLETE
Phase 7 — OPTIONAL (documentation renderer/search integration only if a real
           need appears)
```

The `dexpi/` cluster therefore exists now, with one canonical home per evidence
responsibility, and the historical monolithic Plant/P&ID spike no longer exists
as a single active evidence document. Phase 5B relocated the five remaining root
evidence/prototype documents into `docs/dev/research/` with no split or content
redesign, so Phase 5 is **complete**. Phase 6 then split the last substantive
root document by authority, so no substantive document remains in the `docs/`
root and the Documentation Architecture v2.1 structural migration is complete.

## `standards.md` — authority split (Phase 6, complete)

`docs/standards.md` mixed three independently maintained responsibilities with
different lifecycles. Phase 6 split it by authority; all three results are
developer/agent-owned:

```text
docs/standards.md
    → SPLIT into:

active policy        restricted-standards rules, symbol-provenance
                     policy, verification vocabulary
                     -> docs/dev/workflow/standards.md          (governance)

registry / reference the standards registry and the DEXPI entry
                     -> docs/dev/reference/standards-registry.md (reference)

evidence             source and licensing assessments, with
                     inspection dates
                     -> docs/dev/research/standards-licensing-evidence.md
                                                                (evidence)
```

Phase 6 — COMPLETE. The original `docs/standards.md` no longer exists; the three
files above are the current canonical homes, and the `reference` front-matter
type was introduced for the registry. `docs/dev/reference/` stays reserved for
internal reference material that is neither workflow governance nor
investigation evidence.

## User layer — the Phase 4 foundation

`docs/user/**` answers how to use DeepPlant. Phase 4 created a bounded foundation;
later capabilities add pages to it as they ship.

| Path | Authority | Action | Reason |
|---|---|---|---|
| `docs/user/index.md` | navigation | DONE | User map; now routes to real user pages instead of the developer root |
| `docs/user/getting-started.md` | guidance | DONE | Checkout through first successful validation run |
| `docs/user/concepts/what-is-deepplant.md` | guidance | DONE | User-facing explanation of what DeepPlant is; replaced the transitional `product.md` link |
| `docs/user/how-to/author-plant-yaml.md` | guidance | DONE | Author a model as YAML |
| `docs/user/how-to/validate-a-model.md` | guidance | DONE | Run and read `deepplant validate` |
| `docs/user/how-to/diagnose-validation-errors.md` | guidance | DONE | Read and fix loader/model errors |
| `docs/user/how-to/render-process-svg.md` | guidance | DONE | Render a `ProcessModel` to SVG through the Python API |
| `docs/user/reference/index.md` | navigation | DONE | Thin router to the canonical `docs/contracts/` documents |

The **foundation** is complete; the user layer as a whole is not finished. Future
capabilities will require new user pages, so "Phase 4 done" means this bounded
slice exists and is wired into navigation and validation — not that no user
documentation will ever be added again.

User pages link to `docs/contracts/**` as the authoritative reference; they do not
duplicate contract facts, and they must not require architecture, ADRs, planning
governance, or historical spikes to be read.

## Current → target summary

**Stays genuinely shared (unchanged or co-located):**

- Cross-audience contracts: `docs/contracts/plant-model.md`, `process-model.md`,
  `physical-piping.md`, `yaml-format.md`, `cli.md`, and `rendering.md`.

**Repository-role exceptions and navigation (not shared ownership):**

- `README.md` and `VISION.md` remain broad public/repository entry documents;
  `AGENTS.md` and `project/brief.md` remain developer/agent-oriented despite root
  or `project/` placement.
- `docs/index.md` remains global navigation; `docs/dev/index.md` and
  `docs/user/index.md` remain audience navigation.

**Developer-only canonical reference (relocated in Phase 2):**

- `docs/dev/reference/dexpi-process-adapter.md`
  (was `docs/contracts/dexpi-process-adapter.md`).
- `docs/dev/reference/svg-symbols.md` (was `docs/svg-symbols.md`).

**Developer-owned architecture and workflow/governance (relocated in Phase 3A):**

- `docs/dev/architecture/index.md` (was `docs/architecture.md`).
- `docs/dev/workflow/index.md` (was `docs/workflow.md`).
- `docs/dev/workflow/quality.md` (was `docs/quality.md`).
- `docs/dev/workflow/conventions.md` (was `docs/conventions.md`).
- `docs/dev/workflow/documentation-migration.md` (was
  `docs/documentation-migration.md`; this inventory moved with the slice).

**Developer-owned planning (relocated in Phase 3B):**

- `docs/dev/planning/index.md` (was `docs/planning.md`) — planning governance.
- `docs/dev/planning/roadmap.md` (was `docs/roadmap.md`) — current operational
  state.
- `docs/dev/planning/direction.md` (was `docs/direction.md`) — long-term
  capability progression.
- `docs/dev/planning/product.md` (was `docs/product.md`) — internal
  product/planning thesis.

**Developer-owned decisions, evidence, and history (relocated in Phase 3C):**

- `docs/dev/decisions/**` (was `docs/decisions/**`) — canonical decision records.
- `docs/dev/research/**` (was `docs/research/**`) — canonical evidence documents.
- `docs/dev/history/implementation-slices.md` (was
  `docs/history/implementation-slices.md`) — completion history.

**User-owned foundation (created in Phase 4):**

- `docs/user/index.md` (rebuilt as a task router), `docs/user/getting-started.md`,
  `docs/user/concepts/what-is-deepplant.md`,
  `docs/user/how-to/author-plant-yaml.md`,
  `docs/user/how-to/validate-a-model.md`,
  `docs/user/how-to/diagnose-validation-errors.md`,
  `docs/user/how-to/render-process-svg.md`, and
  `docs/user/reference/index.md` — new user-owned pages, not relocations.

**Nothing remains to leave the `docs/` root:**

- `docs/standards.md` → SPLIT into `docs/dev/workflow/standards.md`,
  `docs/dev/reference/standards-registry.md`, and
  `docs/dev/research/standards-licensing-evidence.md` (Phase 6, complete)

The Phase 5 evidence/prototype relocation is complete: the DEXPI documents left
the root in Phase 5A, and the five remaining documents
(`docs/physical-piping-model.md`, `docs/process-topology.md`,
`docs/process-fragment-prototype.md`, `docs/process-step-classification.md`,
`docs/reference-products.md`) left it in Phase 5B. Phase 6 then split the last
substantive root document. No substantive document remains at the `docs/` root.

After full migration the `docs/` root holds only `index.md` plus the three
audience/authority trees (`user/`, `dev/`, `contracts/`); that is the current
state after Phase 6. Every other current
root document is covered by a `MOVE`/`SPLIT` row above, so no root page is left
unassigned; this inventory itself relocated to
`docs/dev/workflow/documentation-migration.md` in Phase 3A. `docs/index.md`
remains global navigation, not part of the shared documentation layer.

**Splits:**

- `docs/dexpi-plant-pid-spike.md` — split by research question (physical
  topology, instrumentation, presentation). **Done in Phase 5A:** the parts are
  `docs/dev/research/dexpi/plant-pid-semantic-boundary.md`,
  `…/plant-pid-instrumentation.md`, and `…/plant-pid-presentation.md`.
- `docs/standards.md` — split by authority into policy
  (`docs/dev/workflow/standards.md`), registry
  (`docs/dev/reference/standards-registry.md`), and licence/provenance evidence
  (`docs/dev/research/standards-licensing-evidence.md`). **Done in Phase 6.**

## Migration sequence

Directional and incremental. Each step is its own bounded, independently
reviewable change; the sequence does not pre-create Issues for later steps, and a
later slice may reorder these steps if repository evidence supports it.

```text
1. Documentation Architecture v2.1 target-tree correction — DONE
   (ADR-0015 + this inventory + navigation/convention updates)

2. Contract / reference ownership migration — DONE
   docs/rendering.md → docs/contracts/rendering.md
   docs/contracts/dexpi-process-adapter.md
       → docs/dev/reference/dexpi-process-adapter.md
   docs/svg-symbols.md → docs/dev/reference/svg-symbols.md
   reconciled inbound links, navigation, metadata, and agent routing

3. Developer authority-layer migration — DONE
   3A. developer architecture + workflow/governance — DONE
       docs/architecture.md → docs/dev/architecture/index.md
       docs/workflow.md → docs/dev/workflow/index.md
       docs/quality.md → docs/dev/workflow/quality.md
       docs/conventions.md → docs/dev/workflow/conventions.md
       docs/documentation-migration.md
           → docs/dev/workflow/documentation-migration.md
   3B. developer planning — DONE
       docs/planning.md → docs/dev/planning/index.md
       docs/roadmap.md → docs/dev/planning/roadmap.md
       docs/direction.md → docs/dev/planning/direction.md
       docs/product.md → docs/dev/planning/product.md
   3C. developer authority layer — DONE
       docs/decisions/** → docs/dev/decisions/**
       docs/research/** → docs/dev/research/**
       docs/history/** → docs/dev/history/**
   Phase 3 — COMPLETE

4. User documentation foundation — DONE
   docs/user/index.md rebuilt as a task router; getting-started; concepts/
   what-is-deepplant; how-to (author YAML, validate, diagnose, render SVG);
   reference/index; user pages link to cross-audience contracts instead of
   duplicating them

5. Evidence and prototype cleanup — DONE
   5A. DEXPI evidence cluster — DONE
       dexpi/ grouping; the monolithic Plant/P&ID spike split into
       physical-boundary, instrumentation, and presentation evidence
   5B. remaining root evidence/prototypes — DONE
       the five remaining root evidence/prototype documents
       (physical-piping-model, process-topology, process-fragment-prototype,
       process-step-classification, reference-products) → docs/dev/research/;
       no evidence/prototype document remains at the root
   Phase 5 — COMPLETE

6. Standards authority split — DONE
   docs/standards.md
       → SPLIT into:
         docs/dev/workflow/standards.md                    (governance policy)
         docs/dev/reference/standards-registry.md          (reference)
         docs/dev/research/standards-licensing-evidence.md (evidence)
   Phase 6 — COMPLETE

   Phases 1–6 — COMPLETE
   Documentation Architecture v2.1 structural migration: COMPLETE

7. Optional documentation renderer/search integration — OPTIONAL / NOT SCHEDULED
   only if a real need appears
```

This sequence covers every inventory action that changes or adds a document home:
step 2 covered the three contract/reference `MOVE` rows; step 3 (decomposed into
3A, 3B, and 3C) covered the architecture, workflow (including this inventory
itself), planning, decisions, research, and history `MOVE` rows; step 4 created
every user-owned page planned for the Phase 4 foundation; step 5 covers every
root research/prototype `MOVE` — phase 5A delivered the `MOVE` / `MOVE + SPLIT`
DEXPI cluster and phase 5B delivered the five remaining root documents, so step 5
is complete; and step 6 delivered the `standards.md` `SPLIT`, so the
Documentation Architecture v2.1 structural migration is complete. Each move/split
slice reconciled its affected inbound links, navigation, metadata, and agent
routing in the same pass.

Step 2 established the contract/reference homes before developer or user pages
link to them. Step 3 preceded step 4 so the audience layers were already
separated before user content was added. Step 5 followed step 4 so evidence moves
reuse links already reconciled once. Steps 1, 2, 3 (3A, 3B, 3C), 4, 5 (5A and
5B), and 6 are complete. Documentation Architecture v2.1 structural migration is
complete; step 7 (renderer/search integration) remains optional and unscheduled.

## Agent context consequences

Agent routing is updated with each migration slice; this is routing
configuration, not a routing engine. Phase 2 updated
[.agents/context-map.yaml](../../../.agents/context-map.yaml) `change_patterns` so
developer-reference work resolves to the new v2.1 locations:

- renderer changes route to `docs/contracts/rendering.md` and
  `docs/dev/reference/svg-symbols.md`;
- symbol-pack changes route to `docs/dev/reference/svg-symbols.md`;
- DEXPI adapter changes route to `docs/dev/reference/dexpi-process-adapter.md`.

Phase 3A repointed the architecture and workflow/governance routes to the actual
v2.1 paths, including the pattern keys:

- the architecture pattern key is now `docs/dev/architecture/index.md`, and the
  generic `src/**/*.py`, `tests/**/*.py`, `backend/**`, `apps/editor/**`, and
  `**/Dockerfile` patterns route to `docs/dev/architecture/index.md` and
  `docs/dev/workflow/quality.md`;
- the workflow and quality pattern keys are now `docs/dev/workflow/index.md` and
  `docs/dev/workflow/quality.md`;
- `docs/**` routes to `docs/index.md`, `docs/dev/index.md`,
  `docs/dev/workflow/conventions.md`, and
  `docs/dev/workflow/documentation-migration.md`.

Phase 3B repointed the planning routes to the actual v2.1 paths, including the
pattern key:

- the planning pattern key is now `docs/dev/planning/roadmap.md`, which routes to
  `docs/dev/architecture/index.md`, `docs/dev/planning/index.md`, and
  `docs/dev/planning/direction.md`;
- `project/**` routes to `project/brief.md`, `docs/dev/planning/roadmap.md`, and
  `docs/dev/planning/index.md`;
- the `docs/dev/workflow/index.md` pattern routes to
  `docs/dev/planning/index.md` for planning governance.

Routing stays task-scoped: no pattern loads all four planning documents, so
ordinary developer work does not eagerly read them.

Phase 3C repointed the decision-route pattern key and its routed context files to
the actual v2.1 paths, and updated the developer skills that read the decision
index:

- the decision pattern key is now `docs/dev/decisions/**`, routing to
  `docs/dev/architecture/index.md` and `docs/dev/decisions/index.md`;
- `create-adr`, `implement-change`, `orient-project`, `capture-learning`, and
  `update-documentation` read `docs/dev/decisions/` rather than the old root path;
- no pattern eagerly loads decision, evidence, or history documents: evidence and
  history are reached from the developer navigation map, not from ordinary
  implementation routing.

Phase 4 created the user-owned guidance pages and added one narrow route for
them:

- `docs/user/**` routes to `docs/user/index.md`,
  `docs/dev/workflow/conventions.md`, and `docs/contracts/index.md`;
- the generic `docs/**` route is deliberately unchanged and names no user guide,
  so ordinary documentation and implementation work does not eagerly load the
  user layer.

Phase 6 split the standards document but added no broad documentation route.
Standards-sensitive symbol-asset work is the only pattern that needs the new
authority files, so the existing narrow `src/deepplant/assets/symbols/**` route
now also resolves to the current policy (`docs/dev/workflow/standards.md`) and the
registry (`docs/dev/reference/standards-registry.md`). The licensing evidence is
deliberately **not** routed — it is loaded only when a task actually investigates
a source or licence — and no `docs/dev/**` catch-all route was introduced.

Every migrated path — both the pattern key and the routed context files — is now
named at its v2.1 location rather than its historical root path, and `AGENTS.md`
continues to point agents at `docs/dev/index.md` for the task → context table.

The goal is that `task + changed files + selected skill` resolves to a small
audience-appropriate context set without requiring knowledge of historical root
paths. The current routing already selects rather than eagerly loads; only the
paths change.

## Related

- [dev/decisions/ADR-0015-documentation-architecture-v2-1.md](../decisions/ADR-0015-documentation-architecture-v2-1.md)
  — the v2.1 decision behind this inventory.
- [dev/decisions/ADR-0014-documentation-architecture-v2.md](../decisions/ADR-0014-documentation-architecture-v2.md)
  — the preceding decision; its invariant is retained.
- [conventions.md](conventions.md) — KEEP / MOVE / SPLIT rules and the move
  procedure.
- [index.md](../../index.md) — the audience/authority router.
- [research/index.md](../research/index.md) — evidence index.
