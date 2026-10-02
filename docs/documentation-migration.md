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
  - docs/decisions/ADR-0015-documentation-architecture-v2-1.md
  - docs/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# Documentation Migration Inventory

> **Question this document answers:** for every existing document, what audience
> does it serve, what authority does it own, where should it physically live
> under Documentation Architecture v2.1, and in what order should it move?

This is the evidence-backed inventory behind
[ADR-0015](decisions/ADR-0015-documentation-architecture-v2-1.md) (v2.1) and the
operational rules in [conventions.md](conventions.md). It replaces the initial v2
inventory, which defaulted most root paths to `KEEP` because they already existed.
That is a migration-cost argument, not an ownership argument, and it is no longer
how an action is chosen.

## The v2.1 ownership boundary

```text
shared  = canonical contracts/reference genuinely needed across audiences
user    = how to use DeepPlant
dev     = how DeepPlant works, why it works that way, how to change it,
          evidence, planning, and development history
```

Two rules decide ownership:

1. **`canonical != shared-directory`.** A document is canonical when it is the
   single authoritative home for its knowledge type. Canonical content may be
   developer-owned (`docs/dev/**`) or user-owned (`docs/user/**`). Only content
   genuinely needed by more than one audience belongs in the shared layer.
2. **`audience != knowledge authority`.** Audience determines navigation and may
   determine physical ownership; authority independently decides what the
   document owns (current / contract / decision / evidence / history / governance
   / navigation).

The shared layer is therefore deliberately narrow. Today it is `docs/contracts/**`
only. A document does **not** stay in the shared root merely because it has many
links; path stability is a migration cost to weigh, not proof of shared ownership.

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
│   ├── how-to/
│   └── reference/
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
    ├── rendering.md
    ├── svg-symbols.md
    └── dexpi-process-adapter.md
```

## Entry points and repository-root documents

These keep their current location because their **repository or project role**
requires it, not because the shared layer is broad.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `README.md` | shared | navigation | KEEP | — | GitHub/product front door; external inbound links | high |
| `VISION.md` | shared | governance (vision) | KEEP | — | Durable product vision; anchor of the planning hierarchy | high |
| `AGENTS.md` | dev/agent | navigation | KEEP | — | Root agent bootstrap and invariants | high |
| `project/brief.md` | dev/agent | current (project) | KEEP | — | `project/` role; project brief | medium |
| `docs/index.md` | shared | navigation | KEEP | — | The single documents router | high |
| `docs/dev/index.md` | dev/agent | navigation | KEEP | — | Developer map; task → context routing | medium |
| `docs/user/index.md` | user | navigation | KEEP | — | User map; must grow into a real home | low |
| `.agents/context-map.yaml` | dev/agent | navigation | KEEP | — | Machine-readable agent routing | medium |

## Shared layer — `docs/contracts/`

The only genuinely shared layer. Each entry is canonical for more than one
audience, or is a **contract** whose authority is cross-audience by nature.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `docs/contracts/index.md` | shared | navigation | KEEP | — | Contract index; cross-audience | medium |
| `docs/contracts/cli.md` | shared | contract | KEEP | — | Users run the CLI; developers implement it | medium |
| `docs/contracts/yaml-format.md` | shared | contract | KEEP | — | Users author YAML; developers load/save it | medium |
| `docs/contracts/plant-model.md` | shared | contract | KEEP | — | Canonical model semantics for both audiences | medium |
| `docs/contracts/process-model.md` | shared | contract | KEEP | — | Canonical model semantics for both audiences | medium |
| `docs/contracts/physical-piping.md` | shared | contract | KEEP | — | Canonical model semantics for both audiences | medium |
| `docs/contracts/dexpi-process-adapter.md` | dev/agent | contract | KEEP | — | Adapter contract; contract authority keeps it in the shared layer | medium |
| `docs/rendering.md` | shared | contract | MOVE | `docs/contracts/rendering.md` | Contract-authority document; users render, developers consume the API | medium (17) |
| `docs/svg-symbols.md` | dev/agent | contract | MOVE | `docs/contracts/svg-symbols.md` | Contract that belongs with the renderer it operationalizes | medium (20) |

`rendering.md` and `svg-symbols.md` were `KEEP`-in-place under v2. v2.1 reverses
that: they are contracts, and contracts are the shared layer. The earlier
"stable canonical path outweighs co-location" argument is a link-cost argument,
and it does not establish that the root is their correct owner.

## Developer authority layer — architecture, governance, planning

Canonical developer/agent content. It is authoritative without being shared; it
moves out of the shared root into `docs/dev/**`.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `docs/architecture.md` | dev/agent | current | MOVE | `docs/dev/architecture/index.md` | Boundary map; developer/agent-only reading | high (41) |
| `docs/workflow.md` | dev/agent | governance | MOVE | `docs/dev/workflow/index.md` | Change loop; developer/agent process | medium (16) |
| `docs/quality.md` | dev/agent | governance | MOVE | `docs/dev/workflow/quality.md` | Quality gates; developer/agent process | medium (15) |
| `docs/conventions.md` | dev/agent | governance | MOVE | `docs/dev/workflow/conventions.md` | Documentation governance; a change-process rule | medium (16) |
| `docs/planning.md` | dev/agent | governance | MOVE | `docs/dev/planning/index.md` | Planning governance | medium (12) |
| `docs/roadmap.md` | dev/agent | current | MOVE | `docs/dev/planning/roadmap.md` | Current execution state and next direction | high (34) |
| `docs/direction.md` | dev/agent | current | MOVE | `docs/dev/planning/direction.md` | Long-term capability progression | medium (18) |
| `docs/product.md` | dev/agent | current | MOVE | `docs/dev/planning/product.md` | Product/planning thesis; users may be linked to it but it is not user guidance | medium (11) |
| `docs/standards.md` | dev/agent | governance + evidence | SPLIT | see below | Mixes policy, registry, and licence evidence | medium (17) |

`product.md` and `VISION.md` need a deliberate distinction: `VISION.md` stays at
the repository root as the durable identity document, while `product.md` is the
planning-level view and belongs with the rest of planning.

## Developer authority layer — decisions, evidence, history

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `docs/decisions/**` | dev/agent | decision | MOVE | `docs/dev/decisions/**` | Canonical decision records; developer-owned | high |
| `docs/decisions/index.md` | dev/agent | navigation | MOVE | `docs/dev/decisions/index.md` | Decision index | high |
| `docs/research/**` | dev/agent | evidence | MOVE | `docs/dev/research/**` | Canonical evidence; developer-owned | medium |
| `docs/research/index.md` | dev/agent | navigation | MOVE | `docs/dev/research/index.md` | Evidence index | medium |
| `docs/history/implementation-slices.md` | dev/agent | history | MOVE | `docs/dev/history/implementation-slices.md` | Completion history; developer-owned | medium |

## Root evidence and prototypes → `docs/dev/research/`

Evidence and prototype documents that currently sit in the `docs/` root. They
are not shared: only developers, agents, and decision-makers read them.

| Current path | Audience | Authority | Action | Target | Reason | Link cost |
|---|---|---|---|---|---|---|
| `docs/dexpi-process-spike.md` | dev/agent | evidence | MOVE | `docs/dev/research/dexpi/process-adapter-spike.md` | DEXPI Process interoperability evidence | medium (16) |
| `docs/dexpi-plant-pid-spike.md` | dev/agent | evidence | MOVE + SPLIT | `docs/dev/research/dexpi/plant-pid-semantic-boundary.md` (+ split parts) | Evidence; also mixes physical-topology, instrumentation, and presentation questions | medium (11) |
| `docs/dexpi-exchanging-thermal-energy-evidence.md` | dev/agent | evidence | MOVE | `docs/dev/research/dexpi/exchanging-thermal-energy.md` | `ExchangingThermalEnergy` mapping evidence | medium (14) |
| `docs/physical-piping-model.md` | dev/agent | evidence | MOVE | `docs/dev/research/physical-piping-model.md` | Design evidence behind a contract | low (8) |
| `docs/process-topology.md` | dev/agent | evidence | MOVE | `docs/dev/research/process-topology.md` | Process-topology evidence behind a contract | low (8) |
| `docs/process-fragment-prototype.md` | dev/agent | evidence | MOVE | `docs/dev/research/process-fragment-prototype.md` | Prototype modelling evidence | low (5) |
| `docs/process-step-classification.md` | dev/agent | evidence | MOVE | `docs/dev/research/process-step-classification.md` | Evidence behind ADR-0012 | low (8) |
| `docs/reference-products.md` | dev/agent | evidence | MOVE | `docs/dev/research/reference-products.md` | Reference/reuse landscape research | low (4) |

The DEXPI cluster gains a `dexpi/` subfolder once more than one DEXPI evidence
document moves there; it is not created in advance.

## `standards.md` — explicit split assessment

`docs/standards.md` mixes three independently maintained responsibilities with
different lifecycles. Under v2.1 all three are developer/agent-owned, so the
split moves them into the developer layer rather than leaving them shared:

```text
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

The split itself is a later bounded slice, not part of this correction. Until it
lands, the policy sections are the active part and the assessments are evidence
with their own dates. `docs/dev/reference/` is reserved for internal reference
material that is neither workflow governance nor investigation evidence.

## User layer — what is missing

`docs/user/**` answers how to use DeepPlant. Most of it does not exist yet; this
decision defines ownership only and creates no user content.

| Target | Authority | Action | Reason |
|---|---|---|---|
| `docs/user/index.md` | navigation | KEEP + grow | The user map; must route to real pages, not to the developer root |
| `docs/user/getting-started.md` | guidance | ADD (later) | Install, build, first validation run |
| `docs/user/concepts/` | guidance | ADD (later) | The concepts a user must understand (model, plant, process, piping) |
| `docs/user/how-to/` | guidance | ADD (later) | Write YAML, validate, render, diagnose errors |
| `docs/user/reference/` | navigation | ADD (later) | Pointer layer to the canonical `docs/contracts/` documents |

User pages may link to `docs/contracts/**` as authoritative reference; they must
not duplicate contract facts, and they must not require architecture, ADRs,
planning governance, or historical spikes to be read.

## Current → target summary

**Stays genuinely shared (unchanged or co-located):**

- `docs/contracts/**` — the entire contract set, including `rendering.md` and
  `svg-symbols.md` once relocated.
- Repository-root documents kept for repository/project role: `README.md`,
  `VISION.md`, `AGENTS.md`, `project/brief.md`.
- The two navigation layers: `docs/index.md`, `docs/dev/index.md`,
  `docs/user/index.md`.

**Eventually leaves the `docs/` root (nothing moves in this slice):**

- `docs/architecture.md` → `docs/dev/architecture/index.md`
- `docs/workflow.md` → `docs/dev/workflow/index.md`
- `docs/quality.md` → `docs/dev/workflow/quality.md`
- `docs/conventions.md` → `docs/dev/workflow/conventions.md`
- `docs/planning.md` → `docs/dev/planning/index.md`
- `docs/roadmap.md` → `docs/dev/planning/roadmap.md`
- `docs/direction.md` → `docs/dev/planning/direction.md`
- `docs/product.md` → `docs/dev/planning/product.md`
- `docs/standards.md` → split into `docs/dev/workflow/`,
  `docs/dev/reference/`, and `docs/dev/research/`
- `docs/decisions/**` → `docs/dev/decisions/**`
- `docs/research/**` → `docs/dev/research/**`
- `docs/history/**` → `docs/dev/history/**`
- `docs/rendering.md`, `docs/svg-symbols.md` → `docs/contracts/`
- `docs/dexpi-process-spike.md`, `docs/dexpi-plant-pid-spike.md`,
  `docs/dexpi-exchanging-thermal-energy-evidence.md`,
  `docs/physical-piping-model.md`, `docs/process-topology.md`,
  `docs/process-fragment-prototype.md`, `docs/process-step-classification.md`,
  `docs/reference-products.md` → `docs/dev/research/`

After full migration the `docs/` root holds only `index.md` plus the three
audience/authority trees (`user/`, `dev/`, `contracts/`).

**Splits:**

- `docs/dexpi-plant-pid-spike.md` — split by research question (physical
  topology, instrumentation, presentation).
- `docs/standards.md` — split into policy, registry, and licence evidence.

## Migration sequence

Directional and incremental. Each step is its own bounded, independently
reviewable change; no follow-up Issues are created by this slice, and a later
slice may reorder these steps if repository evidence supports it.

```text
1. Documentation Architecture v2.1 target-tree correction
   (this slice — ADR-0015 + this inventory + navigation/convention updates)

2. Developer authority-layer migration
   architecture / workflow / planning / decisions / research / history
   move under docs/dev/** with reconciled inbound links

3. User documentation foundation
   getting-started + primary workflows (create, validate, render, diagnose),
   linking to contracts instead of duplicating them

4. Evidence and prototype cleanup
   root evidence → docs/dev/research/; dexpi/ subfolder; spike splits

5. Standards split
   policy / registry / licence evidence into the developer layer

6. Optional documentation renderer/search
   only if a real need appears
```

Step 2 is placed before step 3 because user pages must link into a stable
developer tree, not into the pre-migration root. Step 4 is after step 2 so the
evidence moves reuse the links already reconciled once.

## Agent context consequences

This slice records the routing consequences; it does not build a routing engine.
After the migration, [.agents/context-map.yaml](../.agents/context-map.yaml)
`change_patterns` must be updated so that:

- `docs/**` routes to `docs/index.md`, `docs/dev/index.md`,
  `docs/dev/workflow/conventions.md`, and `docs/documentation-migration.md`;
- `docs/decisions/**` routes to `docs/dev/architecture/index.md` and
  `docs/dev/decisions/index.md`;
- `docs/roadmap.md` routes to `docs/dev/planning/roadmap.md` and
  `docs/dev/architecture/index.md`;
- `AGENTS.md` continues to point agents at `docs/dev/index.md` for the
  task → context table.

The goal is that `task + changed files + selected skill` resolves to a small
audience-appropriate context set without requiring knowledge of historical root
paths. The current routing already selects rather than eagerly loads; only the
paths change.

## Related

- [decisions/ADR-0015-documentation-architecture-v2-1.md](decisions/ADR-0015-documentation-architecture-v2-1.md)
  — the v2.1 decision behind this inventory.
- [decisions/ADR-0014-documentation-architecture-v2.md](decisions/ADR-0014-documentation-architecture-v2.md)
  — the preceding decision; its invariant is retained.
- [conventions.md](conventions.md) — KEEP / MOVE / SPLIT rules and the move
  procedure.
- [index.md](index.md) — the audience/authority router.
- [research/index.md](research/index.md) — evidence index.
