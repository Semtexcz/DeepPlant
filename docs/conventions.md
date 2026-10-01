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
decision: []
evidence: []
superseded_by: null
---

# Documentation Conventions

> **Question this document answers:** how must a DeepPlant document be typed,
> bounded, linked, and reviewed so readers can tell current rules from evidence
> and history?

## One document, one question

Every document answers exactly **one stable primary question** and has exactly
one authoritative purpose. Four authority types are never mixed in one file:

| Type | Answers | Lives in |
|---|---|---|
| contract / policy | what must hold now? | `docs/contracts/`, root-level governance documents under `docs/`, `project/brief.md` |
| decision | why does this boundary exist? | `docs/decisions/` |
| evidence | what was investigated, and what came out of it? | `docs/research/`, slice documents |
| history | what shipped, in what order? | `docs/history/` |

A section that answers a different question with a different lifecycle moves to
its own document. Length alone is never a reason to split.

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
read_when:       # reader intents, not maintenance activities
  - example-intent
depends_on:      # repository-root-relative paths of prerequisites
  - docs/contracts/index.md
decision:        # ADRs that constrain this document
  - docs/decisions/ADR-0000-example.md
evidence:        # evidence documents supporting an active contract or policy
  - docs/research/example.md
superseded_by: null   # required for historical/superseded documents
---
```

Rules:

1. `type`, `status`, `canonical_for`, and `read_when` are required.
2. `canonical_for` names the question or contract key this document owns. An
   evidence document names its *evidence question*, never a current contract.
3. Paths in `depends_on`, `decision`, and `evidence` are repository-root-relative
   and unambiguous.
4. `superseded_by` is required when `status` is `historical` or `superseded` and
   a replacement exists; use `null` only when no replacement is appropriate.
5. ADRs keep their in-body header (`> Status: …`, `> Date: …`), which is the
   ADR metadata form; supersession is stated in that status line.
6. Future tooling should validate front matter, allowed types, required fields,
   relative links, heading anchors, and hard-limit violations. This convention
   does not require a documentation-linter framework today.

## Length policy

Line counts are `wc -l` of the committed Markdown file, including front matter
and blank lines.

| Document type | Soft limit | Hard limit | Required action beyond hard limit |
|---|---:|---:|---|
| Navigation, project brief, roadmap | 150 | 220 | Split historical/detail content out or replace it with links |
| Governance/policy, architecture, contracts, direction (vision/direction documents use this row too) | 250 | 350 | Extract independent contracts, evidence, or extended examples |
| ADR | 160 | 250 | Move detailed evidence and investigations to an evidence document |
| Research/evidence/spike/prototype/history | 500 | no fixed hard limit | Add or improve a ≤40-line outcome card; split only by independent research question |
| Registry, catalogue, reference inventory | 300 | 500 | Split by independently maintained domain, or generate it later |

Exception process:

- Crossing a **soft** limit requires an explicit statement in the change: retain
  with reason, shorten, split, reclassify, or justify as auditable evidence.
- Crossing a **hard** limit blocks ordinary growth until independent material is
  extracted. A current contract may not hide rules inside an evidence report.
- The "no fixed hard limit" exception applies only to material that must remain
  auditable, and only together with a compliant outcome card.

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

## Migration status

This repository adopted the conventions above in stages. Current state:

- **Canonical contracts**: `docs/contracts/*` (plant model, process model,
  physical piping, YAML format, CLI, DEXPI Process adapter) plus
  [rendering.md](rendering.md) and [svg-symbols.md](svg-symbols.md), which are
  canonical in place.
- **Canonical current documents**: [architecture.md](architecture.md),
  [roadmap.md](roadmap.md), [direction.md](direction.md),
  [product.md](product.md), [planning.md](planning.md),
  [workflow.md](workflow.md), [quality.md](quality.md),
  [standards.md](standards.md), `project/brief.md`.
- **Evidence and history**: [decisions/](decisions/index.md),
  [history/implementation-slices.md](history/implementation-slices.md), and the
  DEXPI/prototype/design documents listed in
  [research/index.md](research/index.md).

Still outstanding (each a small, independently reviewable change):

1. Relocate the two in-place canonical contracts (`rendering.md`,
   `svg-symbols.md`) under `docs/contracts/` and update their inbound links.
2. Split `standards.md` into an active policy document, a standards registry, and
   source/asset-licence evidence.
3. Split the DEXPI Plant/P&ID spike by research question (physical topology,
   instrumentation, presentation) and split the physical-piping design evidence
   from its contract, each with an outcome card.
4. Relocate the historical prototype/evidence documents into `docs/research/`
   subdirectories once their inbound links can be updated in one pass.

## Related

- [index.md](index.md) — question-led navigation with authority labels.
- [contracts/index.md](contracts/index.md) — the current contract set.
- [decisions/index.md](decisions/index.md) — decision records.
- [research/index.md](research/index.md) — evidence and prototype index.
