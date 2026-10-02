# ADR-0014: Documentation Architecture v2 — Audience Navigation over a Shared Canonical Authority Layer

> Status: Accepted; its physical-ownership interpretation is superseded by
> [ADR-0015](ADR-0015-documentation-architecture-v2-1.md). The
> `audience != knowledge authority` invariant, the authority taxonomy, atomicity,
> the metadata vocabulary, and the KEEP/MOVE/SPLIT safety rules recorded here
> remain in force.
> Date: 2026-10-02

> **Supersession note (2026-10-02).** This ADR's decision text is retained
> unmodified as the historical record. Its **physical-ownership
> interpretation** — that the shared canonical layer is broad and that
> developer/agent material (root current/governance documents, `decisions/`,
> `research/`, `history/`) stays in a shared root — was too broad.
> [ADR-0015](ADR-0015-documentation-architecture-v2-1.md) refines it: the shared
> layer is narrow (`docs/contracts/**` only), and canonical content may be
> audience-owned (`docs/dev/**`, `docs/user/**`). Read this ADR for the accepted
> invariant and its reasoning; read ADR-0015 for the current target tree and
> ownership boundary.

## Context

DeepPlant's documentation already separates **knowledge authority** from a single
undifferentiated pile: [contracts](../contracts/index.md) own what must hold now,
[decisions](index.md) record why a boundary exists,
[research](../research/index.md) records what was investigated, and
[history](../history/implementation-slices.md) records what shipped. The rules
for that authority model live in [docs/dev/workflow/conventions.md](../dev/workflow/conventions.md).

Issue #41 found that authority separation is necessary but **not sufficient** as
a navigation model:

- **Audience is implicit.** User-facing obligations (authoring YAML, running the
  CLI) and developer/agent material share the same navigation space.
- **Entry points compete.** `README.md`, `docs/index.md`, the contract index, the
  governance documents, and `AGENTS.md` all present themselves as broad starters.
- **Repeated routing metadata and hard file-size rules cost context** without
  materially improving ownership.
- **A size rule invited cosmetic work.** A recent review reformatted a document
  from roughly 355 to 348 lines to satisfy a hard numeric limit rather than
  improving its conceptual structure.

The governing constraint for any fix is:

```text
audience != knowledge authority
```

DeepPlant must make **user vs developer/agent navigation** and **contract /
decision / evidence / history authority** explicit, without collapsing the two
into one dimension.

## Options

- **A — audience-first tree.** `docs/user/` and `docs/dev/` own the knowledge;
  authority is expressed separately inside each audience.
- **B — shared canonical reference + audience navigation.** Canonical documents
  keep stable positions in a shared layer (`contracts/`, `decisions/`,
  `research/`, `history/`); audience navigation points into it.
- **C — hybrid.** A shared canonical layer keeps cross-audience truth; `user/`
  and `dev/` hold genuinely audience-specific navigation or guidance.

Scored against the criteria Issue #41 requires:

| Criterion | A audience-first | B shared + navigation | C hybrid |
|---|---|---|---|
| Findability | strong for browsers; weak on "which doc is canonical?" | good via indexes | strong |
| Single source of truth | weakens: a cross-audience contract must sit under one audience | strong | strong |
| Audience clarity | strong | good but implicit | strong |
| Stable authority | risks equating location with audience | strong | strong |
| Link/migration cost | high (moves every cross-audience document) | low | low for the initial proof |
| Agent routing | hides authority behind audience paths | good | good |
| Duplication risk | high (material is re-copied per audience) | low | low |
| Repository usability | looks tidy, misleads about ownership | stable but no audience home | best fit |

Evidence for the choice: existing contracts already declare cross-audience
reader intents (`docs/contracts/cli.md` lists `user-documentation`;
`docs/contracts/yaml-format.md` lists `authoring-plant-yaml`), and
[docs/contracts/index.md](../contracts/index.md) already treats the in-place root
contracts ([rendering.md](../contracts/rendering.md), [svg-symbols.md](../dev/reference/svg-symbols.md))
as canonical *where they are*. Canonical truth is cross-audience, not
audience-owned.

## Decision

**C (hybrid) is accepted as Documentation Architecture v2**, on these explicit
terms:

1. **Audience and knowledge authority are independent dimensions.** Neither
   replaces the other.
2. **A shared canonical layer keeps current truth.** `docs/contracts/`, the
   root-level canonical current/policy documents (`architecture.md`,
   `workflow.md`, `quality.md`, `planning.md`, `roadmap.md`, `direction.md`,
   `product.md`, `conventions.md`, `standards.md`), and `project/brief.md` stay
   where they are; reasons stay in `decisions/`, evidence in `research/`, history
   in `history/`.
3. **`docs/user/` and `docs/dev/` hold only genuinely audience-specific
   navigation or guidance.** A document canonical for more than one audience
   stays in the shared canonical layer and is linked from both audience indexes.
4. **Filesystem location is not the only audience signal.** Audience is expressed
   primarily by **navigation** (indexes and `read_when`), with `user/` and `dev/`
   used only where content is genuinely audience-specific.
5. **No `audience:` front-matter field is introduced.** Audience is a navigation
   concern, not a document-authority field; the metadata vocabulary stays small.
6. **Conceptual atomicity is the decomposition rule** — one document owns one
   durable concept, workflow, task, or question. Numeric line counts are a review
   signal, not architectural validity.
7. **Markdown stays canonical and repository-readable.** No documentation
   renderer is introduced by this decision.

The operational rules that implement this — document types, the metadata
vocabulary, the audience model, and the KEEP / MOVE / SPLIT policy — live in
[docs/dev/workflow/conventions.md](../dev/workflow/conventions.md). The evidence-backed migration inventory
and the proposed incremental sequence live in
[docs/dev/workflow/documentation-migration.md](../dev/workflow/documentation-migration.md).

## Consequences

### Positive

- A canonical document can serve users, developers, and agents without a second
  audience-owned copy.
- Stable canonical paths are preserved, so existing inbound links keep working.
- A reader or agent has one explicit starting decision: which audience am I, and
  what kind of truth do I need?
- Adding a future audience is additive (a navigation index), not a migration.

### Negative

- Two organising ideas (audience and authority) must both be understood; a
  directory listing alone does not explain the model.
- Discipline is required so `user/` and `dev/` do not drift into dumping grounds
  or duplicate canonical facts.
- The migration inventory becomes a maintained artifact until migrations
  complete.

## Deferred

- Performing document moves, splits, or the `standards.md` split.
- Creating follow-up migration Issues.
- A documentation renderer or search layer (for example Zensical).
- A machine-readable documentation linter beyond the current conventions.

## Revisit When

- Audience-specific content grows large enough that navigation-only treatment is
  insufficient.
- A genuinely audience-owned canonical document appears.
- A renderer/search requirement makes path stability matter less.
- The metadata vocabulary stops earning its keep.

## Related

- [docs/dev/workflow/conventions.md](../dev/workflow/conventions.md) — operational documentation rules.
- [docs/dev/workflow/documentation-migration.md](../dev/workflow/documentation-migration.md) — migration
  inventory and sequence.
- [docs/index.md](../index.md) — the audience/authority router.
- [docs/decisions/index.md](index.md) — decision index.
- Issue #41 — this decision's origin. Issue #39 — the independent semantic-model
  `Now` item, unaffected by this decision.
