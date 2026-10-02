---
type: governance
status: active
canonical_for:
  - documentation-conventions
read_when:
  - documentation-change
  - create-adr
  - update-documentation
depends_on:
  - docs/index.md
decision:
  - docs/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# Documentation Conventions

> **Question this document answers:** how must a DeepPlant document be typed,
> bounded, linked, and reviewed so readers can tell current rules from evidence
> and history, and so users, developers, and agents can find the right starting
> point? Two independent dimensions apply: **audience** and **knowledge
> authority** ([ADR-0014](decisions/ADR-0014-documentation-architecture-v2.md)).

## One document, one durable responsibility (atomicity)

Conceptual atomicity is the primary decomposition rule:

> One document primarily owns one durable concept, workflow, task, or question.

Split a document because it contains **independently maintained responsibilities
or lifecycles**, not merely because it is long. A section that answers a
different question with a different lifecycle moves to its own document; a
coherent, single-question document stays whole however long it is. Length alone
is never a reason to split (see [Size as a review signal](#size-as-a-review-signal)).

Documents should not mix independent authority types. This is the target
architectural rule; known legacy exceptions awaiting bounded migration are
recorded in [documentation-migration.md](documentation-migration.md):

| Type | Answers | Lives in |
|---|---|---|
| contract / policy | what must hold now? | `docs/contracts/`, root-level governance documents under `docs/`, `project/brief.md` |
| decision | why does this boundary exist? | `docs/decisions/` |
| evidence | what was investigated, and what came out of it? | `docs/research/`, root-level evidence/prototype documents pending migration |
| history | what shipped, in what order? | `docs/history/` |

## Audience model

Knowledge **authority** (contract / decision / evidence / history) and **audience**
(user / developer / agent) are independent dimensions
([ADR-0014](decisions/ADR-0014-documentation-architecture-v2.md)). Audience is
expressed by three mechanisms, with deliberately chosen responsibilities:

| Mechanism | Role in expressing audience |
|---|---|
| Physical location | Only for content that is genuinely audience-specific: `docs/user/`, `docs/dev/`. A canonical document that serves more than one audience stays in the shared canonical layer and must **not** be forced under an audience directory. |
| Navigation / indexes | The primary audience signal. `docs/index.md` routes by audience; `docs/user/index.md` and `docs/dev/index.md` are the audience maps; `read_when` contexts/tasks carry the signal for agents. |
| Metadata | Not used for audience. There is deliberately **no `audience:` front-matter field**; audience is a navigation concern, not a document-authority field. |

Rules:

1. A document canonical for more than one audience stays in the shared canonical
   layer; both audience indexes link to it. Keep one canonical copy — never
   duplicate a fact to give it an audience home.
2. Add `docs/user/` or `docs/dev/` material only when it is genuinely
   audience-specific. Do not create empty audience trees to match a taxonomy.
3. Filesystem location is never the only audience signal; a reader or agent must
   also be able to tell the audience from the navigation.

## Front matter

Every documentation file under `docs/` and `project/`, except ADRs, carries
standard YAML front matter. Repository entrypoint files `README.md`, `VISION.md`,
and `AGENTS.md` are explicit exceptions because GitHub, users, and tooling consume
them directly.

```yaml
---
type: architecture | governance | contract | roadmap | direction | project-brief
      | navigation | product | history | evidence | prototype | design-evidence
status: active | historical | superseded | proposed
canonical_for:   # the stable question or contract key this document owns
  - example-key
read_when:       # contexts/tasks in which this document should be read
  - example-context-or-task
depends_on:      # repository-root-relative paths of prerequisites
  - docs/contracts/index.md
decision:        # ADRs that constrain this document
  - docs/decisions/ADR-0000-example.md
evidence:        # evidence documents supporting an active contract or policy
  - docs/research/example.md
superseded_by: null   # required for historical/superseded documents
---
```

The vocabulary is deliberately small. Every field must earn its keep for
ownership, authority/lifecycle, navigation, or agent-context routing:

| Field | Required | Purpose it serves |
|---|---|---|
| `type` | yes | ownership / classification |
| `status` | yes | authority / lifecycle |
| `canonical_for` | yes | ownership — the one question the document owns |
| `read_when` | yes | contexts/tasks in which to read the document; agent-context routing / navigation |
| `update_when` | no | maintenance trigger for a document with a lifecycle |
| `depends_on` | no | prerequisites / navigation |
| `decision` | no | traceability to the ADRs that constrain it |
| `evidence` | no | traceability to the evidence behind it |
| `superseded_by` | when superseded | lifecycle |

Rules:

1. `type`, `status`, `canonical_for`, and `read_when` are required.
2. `read_when` lists the contexts or tasks in which the document should be loaded
   or read. Values may express a reader intent (for example,
   `authoring-plant-yaml`) or a change trigger (for example, `implement-change`
   or `architecture-change`); `update_when` remains the separate maintenance
   trigger.
3. `canonical_for` names the question or contract key this document owns. An
   evidence document names its *evidence question*, never a current contract.
4. Paths in `depends_on`, `decision`, and `evidence` are repository-root-relative
   and unambiguous.
5. `superseded_by` is required when `status` is `historical` or `superseded` and
   a replacement exists; use `null` only when no replacement is appropriate.
6. ADRs keep their in-body header (`> Status: …`, `> Date: …`), which is the
   ADR metadata form; supersession is stated in that status line.
7. Do **not** add an `audience:` field (see [Audience model](#audience-model)).
   Do not extend the vocabulary without a demonstrated need.
8. Future tooling should validate front matter, allowed types, required fields,
   relative links, heading anchors, and size signals. This convention does not
   require a documentation-linter framework today.

## Size as a review signal

Document size is a **review signal, not an architectural validity rule**. There
are no numeric hard limits: a coherent research report that answers one auditable
question may legitimately run to many hundreds of lines, and reformatting a
document to satisfy a line count is not a real change
([ADR-0014](decisions/ADR-0014-documentation-architecture-v2.md)).

When a document grows large, ask the atomicity question first: does it still own
one durable concept, workflow, task, or question? Split only when it does not.

One soft signal is retained, with a concrete operational reason — navigation
value decays as a router grows:

| Document kind | Soft signal | Why it exists |
|---|---:|---|
| Navigation and entry points (`README.md`, `docs/index.md`, `docs/user/index.md`, `docs/dev/index.md`, `*/index.md`) | 120 lines | A navigation document's only job is routing. Past this size it is usually dumping content into a router, which is the specific failure mode that harms findability. |

Crossing the navigation soft signal requires an explicit statement in the change:
retain with reason, shorten, or split. No other document kind has a numeric
limit; a long document is reviewed for concept count and lifecycle mixing, not
for length.

## Outcome card for evidence, research, and history

Evidence/research documents require an Outcome card. Navigation/index documents
under `docs/research/` do not. Every historical slice document begins, after its
title, with a card of at most 40 lines:

```markdown
## Outcome card

- **Question investigated:** …
- **Status:** historical evidence / open evidence / superseded by …
- **Inspection scope and date:** …
- **Conclusions:** 3–5 statements
- **Resulting ADRs:** …
- **Current contracts operationalizing the result:** …
- **Conditions for revisiting:** …
```

## Canonical ownership and link rules

1. **One fact, one home.** A current implementation fact is maintained in exactly
   one document — normally a contract. Every other document links to it.
2. **Scoped summary, then link.** When another document needs the fact for local
   comprehension, it states it in one sentence and links to the canonical home.
3. **Contracts link backward** to the ADRs and evidence that justify them; they do
   not reproduce long investigation tables.
4. **ADRs link forward.** New ADRs, and existing ADRs when materially updated, link
   forward to the current contract that operationalizes the decision where such a
   contract exists. Older ADRs may be migrated incrementally; the contract index
   remains the authoritative current-state navigation during that migration. An ADR
   is never the only location of a current contract.
5. **Evidence never owns current rules.** A research report may contain proposed
   or superseded shapes, clearly labelled, with the current contract linked.
6. **History is never the current state.** Completion records state what shipped;
   they do not define what must hold now.
7. **Navigation labels authority.** An index groups entries as *Current*,
   *Decision*, *Evidence*, *Historical*, or *Proposed*; a flat list of links with
   no authority signal is a defect.
8. **Superseded material stays readable.** Documents are not deleted; they are
   reclassified and linked with an outcome card or supersession note.

## Documentation impact review

Every change answers two independent documentation-impact questions. They are
review questions for the author and reviewer, not automated gates:

- **User Documentation Impact** — did user-facing behavior, YAML shape, CLI
  output, or public guidance change? If yes, the relevant user-facing contract and
  the `docs/user/` navigation may need an update; if no, state that.
- **Developer Documentation Impact** — did architecture, a contract boundary, a
  decision, or an invariant change? If yes, update the affected contract, ADR, or
  `docs/dev/` navigation; if no, state that.

```text
internal semantic-model refactor
    → User Documentation Impact: none expected
    → Developer Documentation Impact: review (architecture / contract)

new CLI command
    → User Documentation Impact: required (contracts/cli.md + user navigation)
    → Developer Documentation Impact: review too
```

Answering "none" for both is valid — record the reason instead of inventing
documentation. This stays lightweight: no separate workflow, labels, or
automation are introduced.

## Path stability: KEEP, MOVE, or SPLIT

Stable paths are worth more than an aesthetically perfect tree. Decide per
document:

- **KEEP** (default) — the path is stable and the document owns one
  responsibility. Do not move it merely because a cleaner taxonomy is possible.
- **MOVE** — the document's authority already belongs in a different layer (for
  example, root-level evidence that belongs under `docs/research/`) and its
  inbound links can be reconciled in one pass.
- **SPLIT** — the document mixes independently maintained responsibilities or
  lifecycles, so each part moves to the document type that owns it.

Consider before acting: inbound repository links, external GitHub links to the
path, cross-audience use, authority stability, and migration cost. The current
inventory is in [documentation-migration.md](documentation-migration.md).

### Performing a move

A move is complete only when all of these hold in the same change:

1. repository-internal inbound links are updated;
2. indexes and navigation (`docs/index.md`, `docs/user/index.md`,
   `docs/dev/index.md`, the relevant `*/index.md`) are updated;
3. front-matter references (`depends_on`, `decision`, `evidence`) that name the
   old path are updated;
4. `README.md` and `AGENTS.md` references are updated where relevant;
5. relative links resolve and validation passes;
6. exactly one canonical copy remains.

Permanent Markdown redirect stubs are **not** the default. Create a compatibility
stub at the old path only when a concrete, external consumer needs the old URL to
keep working and cannot be updated in the same change; a stub is a link and a
pointer only, never a second copy of the content.

## Migration status

The repository adopted the conventions above in stages, and
[ADR-0014](decisions/ADR-0014-documentation-architecture-v2.md) adds the audience
layer on top of the authority model. Current state:

- **Audience layer**: [index.md](index.md) routes by audience;
  [user/index.md](user/index.md) and [dev/index.md](dev/index.md) are the audience
  navigation maps. No canonical document moved to create them.
- **Canonical contracts**: `docs/contracts/*` (plant model, process model,
  physical piping, YAML format, CLI, DEXPI Process adapter) plus
  [rendering.md](rendering.md) and [svg-symbols.md](svg-symbols.md), which are
  canonical in place.
- **Canonical current documents**: [architecture.md](architecture.md),
  [roadmap.md](roadmap.md), [direction.md](direction.md),
  [product.md](product.md), [planning.md](planning.md),
  [workflow.md](workflow.md), [quality.md](quality.md),
  [standards.md](standards.md),
  [documentation-migration.md](documentation-migration.md), `project/brief.md`.
- **Evidence and history**: [decisions/](decisions/index.md),
  [history/implementation-slices.md](history/implementation-slices.md), and the
  DEXPI/prototype/design documents listed in
  [research/index.md](research/index.md).

The evidence-backed inventory and ordering for the remaining work live in
[documentation-migration.md](documentation-migration.md); each item there is a
small, independently reviewable change, not a pre-approved backlog:

1. Split `standards.md` into an active policy document, a standards registry, and
   source/asset-licence evidence.
2. Split the DEXPI Plant/P&ID spike by research question (physical topology,
   instrumentation, presentation) and split the physical-piping design evidence
   from its contract, each with an outcome card.
3. Relocate the historical prototype/evidence documents into `docs/research/`
   subdirectories once their inbound links can be updated in one pass.

## Related

- [index.md](index.md) — the audience/authority router.
- [user/index.md](user/index.md), [dev/index.md](dev/index.md) — audience
  navigation maps.
- [contracts/index.md](contracts/index.md) — the current contract set.
- [decisions/index.md](decisions/index.md) — decision records.
- [research/index.md](research/index.md) — evidence and prototype index.
- [documentation-migration.md](documentation-migration.md) — migration inventory
  and sequence.
- [decisions/ADR-0014-documentation-architecture-v2.md](decisions/ADR-0014-documentation-architecture-v2.md)
  — the documentation architecture decision.
