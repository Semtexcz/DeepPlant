# ADR-0015: Documentation Architecture v2.1 — Audience-Owned Canonical Content and a Narrow Shared Layer

> Status: Accepted
> Date: 2026-10-02
> Supersedes: ADR-0014 physical-ownership interpretation only; the
> `audience != knowledge authority` invariant is retained

## Context

[ADR-0014](ADR-0014-documentation-architecture-v2.md) (Documentation Architecture
v2, Issue #41 / PR #45) established the durable invariant
`audience != knowledge authority` and adopted a **hybrid** structure. It made two
different claims at once:

1. an **invariant** — knowledge authority (contract / decision / evidence /
   history) is independent of audience (user / developer / agent); and
2. a **physical-ownership interpretation** — almost all canonical content stays
   in a shared root layer (`docs/contracts/`, root-level current/policy
   documents, `docs/decisions/`, `docs/research/`, `docs/history/`,
   `project/brief.md`), while `docs/user/` and `docs/dev/` hold "only genuinely
   audience-specific navigation or guidance".

The invariant is sound. The physical-ownership interpretation was too broad, and
its consequence is visible in the tree it produced: `docs/user/index.md` and
`docs/dev/index.md` are navigation veneers over a root directory that still holds
most of the real content. Audience is nominally expressed but physically almost
absent, so:

- root-level evidence and prototypes (`docs/dexpi-*-spike.md`,
  `docs/process-topology.md`, `docs/physical-piping-model.md`, …) have no
  audience home and no ownership signal distinguishing them from contracts;
- developer/agent governance (`architecture.md`, `workflow.md`, `quality.md`,
  `planning.md`, `roadmap.md`, `direction.md`, `conventions.md`, `standards.md`)
  sits beside shared contracts in the same flat root;
- a reader or agent looking for "the user documentation" or "the developer
  documentation" still lands in the same root directory;
- [`docs/dev/workflow/documentation-migration.md`](../workflow/documentation-migration.md) defaulted
  most root paths to `KEEP` because they already exist — a migration-cost
  argument, not a semantic-ownership argument.

The narrower and more accurate reading is:

```text
canonical != shared-directory
```

A document can be authoritative — the single canonical home for its knowledge
type — while being owned by one audience. Only documents whose canonical content
genuinely serves multiple audiences belong in a shared layer, and audience
ownership means physical location for audience-specific content.

## Options

- **A — retain ADR-0014 unchanged.** The shared root layer stays broad and the
  audience directories remain navigation-only. Rejected: audience stays
  physically unimplemented, and the inventory keeps using "the path already
  exists" as a reason to keep it.
- **B — narrow shared layer with audience-owned canonical content (v2.1).**
  `docs/contracts/**` holds only genuinely cross-audience contracts; `docs/dev/**`
  owns developer/agent canonical content, including developer-only contracts and
  reference, architecture, governance, decisions, research/evidence, history, and
  planning; `docs/user/**` owns user guidance. Authority stays independent of the
  physical owner.
- **C — fully audience-first (ADR-0014 option A).** Every document, including a
  cross-audience contract, is owned by one audience. Rejected for the same reason
  ADR-0014 rejected it: a contract canonical for both users and developers must
  not be forced under a single audience.

## Decision

**B (v2.1) is accepted.** It refines ADR-0014 rather than discarding its
reasoning: the invariant, the authority taxonomy, atomicity, and the migration
safety rules all remain in force; only the physical-ownership interpretation of
the shared layer changes.

### 1. Invariant retained

`audience != knowledge authority` remains the governing principle. Authority
decides what kind of truth a document owns; audience decides who primarily needs
it; physical location follows audience ownership unless the content is genuinely
cross-audience. Authority independently answers:

```text
current / contract = what must hold now
decision           = why a durable boundary exists
evidence           = what was investigated
history            = what happened earlier
```

### 2. The shared layer is narrow

The shared documentation layer contains only canonical documents whose content is
genuinely needed across audiences and would be misrepresented by ownership under a
single audience. Today, cross-audience contracts are expected to live under:

```text
docs/contracts/**
```

The CLI surface, the authored YAML format, the model contracts, and the public
renderer API are authoritative for users and developers alike. Contract authority,
however, does not by itself make a document shared: developer-only contracts and
reference remain developer-owned under `docs/dev/reference/`.

### 3. Canonical does not mean shared directory

A document is **canonical** when it is the single authoritative home for its
knowledge type, regardless of physical directory. Therefore:

```text
docs/dev/architecture/**   canonical for current architecture
docs/dev/decisions/**      canonical for decision records
docs/dev/research/**       canonical for evidence and investigations
docs/dev/history/**        canonical for completion history
docs/dev/planning/**       canonical for planning and direction
docs/dev/workflow/**       canonical for the change loop, quality, and
                           documentation governance
docs/dev/reference/**      canonical for developer-only contracts/reference
```

These are canonical without being shared. Users normally do not read them; that
does not make them second-class or non-authoritative.

### 4. Audience physical ownership

```text
shared  = canonical documents genuinely needed across audiences;
          today, cross-audience contracts under docs/contracts/**
user    = how to use DeepPlant
dev     = how DeepPlant works, why it works that way, how to change it,
          evidence, planning, and development history
```

`docs/user/**` answers user tasks: What is DeepPlant? How do I install it? How do
I create, validate, and render a model? How do I write YAML? How do I diagnose an
error? Which concepts do I need? It may link to contracts as authoritative
reference. A user should not need architecture research, ADRs, planning
governance, or historical spikes to learn how to use DeepPlant.

`docs/dev/**` owns architecture, workflow/governance, planning/direction,
decisions, research/evidence, history, prototypes/spikes, internal
standards/provenance governance, and developer-only contracts/reference.

### 5. Target tree (directional)

```text
docs/
├── index.md                       global audience/authority router
├── user/
│   ├── index.md
│   ├── getting-started.md         future content, not created by this decision
│   ├── concepts/
│   ├── how-to/
│   └── reference/
├── dev/
│   ├── index.md
│   ├── architecture/
│   ├── workflow/
│   ├── planning/
│   ├── reference/                 developer-only canonical contracts/reference
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

This tree is the target, not permission to create empty directories. A folder
appears only when a real document moves into it.

### 6. Repository-role exceptions and global navigation remain distinct

`README.md` (GitHub/product front door), `VISION.md` (durable public-facing
product thesis), `AGENTS.md` (agent bootstrap), and `project/brief.md` (project
brief) are not moved into `docs/`: their locations follow repository or tooling
role, not shared-audience ownership. `README.md` and `VISION.md` serve a broad
public/repository audience; `AGENTS.md` and `project/brief.md` remain
developer/agent-oriented despite their root or `project/` locations.

`docs/index.md` is global navigation: it routes between audiences but is not part
of the shared documentation layer. Root placement does not imply shared audience
ownership.

### 7. Explicitly retained from ADR-0014

The authority taxonomy, conceptual atomicity, the small metadata vocabulary
(deliberately **no `audience:` field**), the KEEP/MOVE/SPLIT criteria and the
link-reconciliation move procedure, the navigation-size soft signal, Markdown as
the canonical format, and the absence of a mandatory renderer all remain in
force.

### 8. Migration is incremental and evidence-driven

This decision defines the target; it moves nothing. `KEEP` no longer means "the
path already exists" and `MOVE` no longer means "a cleaner taxonomy is
preferable". Each move is a separate bounded change with reconciled inbound links
([docs/dev/workflow/conventions.md](../workflow/conventions.md)). The current inventory and sequence
are in [docs/dev/workflow/documentation-migration.md](../workflow/documentation-migration.md).

## Consequences

### Positive

- Physical structure reflects audience for content that is genuinely
  audience-specific.
- The shared layer stays small and defensible document by document.
- Developer/agent material gains a stable home without becoming non-canonical.
- Users do not navigate research, ADRs, planning governance, or historical spikes
  to learn the tool.
- Agent routing becomes `audience path` plus `authority path`, instead of
  requiring knowledge of the historical root layout.

### Negative

- Migration cost: many root documents and their inbound links move across several
  reviewable changes.
- External links to current root paths may break unless a compatibility stub is
  justified by a concrete external consumer.
- `docs/user/index.md` and `docs/dev/index.md` must be maintained as real maps,
  not veneers, or the audience layer regresses.
- Reviewers must still hold audience and authority as separate dimensions; the
  physical owner is a third signal, not a replacement for either.

## Deferred

- Performing any document move, split, or the `standards.md` split.
- Writing user-documentation content (`getting-started`, concepts, how-to).
- Creating the future migration Issues.
- A documentation renderer or search layer.
- Any automated documentation-linter beyond the current conventions.

## Revisit When

- A document in `docs/contracts/` turns out to serve only one audience, or a
  developer-only contract becomes genuinely cross-audience.
- A developer-owned canonical document becomes user-facing enough to justify a
  user-owned counterpart.
- Migrations complete and the inventory can be retired from routine maintenance.
- A renderer/search requirement changes link-stability trade-offs.

## Related

- [ADR-0014](ADR-0014-documentation-architecture-v2.md) — the preceding decision;
  its `audience != knowledge authority` invariant is retained and only its
  physical-ownership interpretation is superseded.
- [docs/dev/workflow/conventions.md](../workflow/conventions.md) — operational documentation rules.
- [docs/dev/workflow/documentation-migration.md](../workflow/documentation-migration.md) — current →
  target inventory and migration sequence.
- [docs/index.md](../../index.md) — the documentation router.
- Issue #46 — this decision's origin; Issue #41 / PR #45 — the preceding
  architecture decision; Issue #39 — the independent semantic-model `Now` item,
  unaffected by this decision.
