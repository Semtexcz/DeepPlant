---
type: navigation
status: active
canonical_for:
  - current-contract-index
read_when:
  - start-work
  - model-change
  - adapter-change
  - renderer-change
depends_on:
  - docs/dev/architecture/index.md
  - docs/dev/workflow/conventions.md
decision:
  - docs/decisions/ADR-0015-documentation-architecture-v2-1.md
evidence: []
superseded_by: null
---

# Current Contracts

A **contract** answers one stable question: *what must conforming data, code, or
callers do now?* Contracts describe the implemented state. They do not record
why a choice was made (ADRs), what was investigated (evidence), or what
happened in which slice (history).

Every cross-audience contract listed here has one canonical home.
Developer-only canonical contracts/reference live under `docs/dev/reference/`.
Other documents link to that home instead of restating the facts.

## Contract documents

| Contract | Document | Answers |
|---|---|---|
| Plant model | [plant-model.md](plant-model.md) | What physical/plant objects exist, what identifies them, and which structural and reference rules must hold? |
| Process model | [process-model.md](process-model.md) | What process objects exist, how is the process graph owned, and which rules (S1–S4) apply? |
| Physical piping | [physical-piping.md](physical-piping.md) | How is physical piping realized over identified connections, and which rules (C1, P1–P5) apply? |
| YAML format | [yaml-format.md](yaml-format.md) | What is the authored YAML document shape, and what does load/save guarantee? |
| CLI surface | [cli.md](cli.md) | Which commands exist, what do they print, and what exit codes do they use? |
| Headless process renderer | [rendering.md](rendering.md) | What is the public renderer API and its deterministic behaviour? |

The public renderer contract now lives in this shared layer. The DEXPI Process
adapter ([../dev/reference/dexpi-process-adapter.md](../dev/reference/dexpi-process-adapter.md))
and SVG symbol pack ([../dev/reference/svg-symbols.md](../dev/reference/svg-symbols.md))
retain contract authority but are developer-only reference, so they live under
`docs/dev/reference/`, not here. Contract authority does not by itself establish
shared ownership. See
[documentation-migration.md](../dev/workflow/documentation-migration.md).

## How contracts relate to the other document types

```text
contract (here)      what must hold now
decisions/           why the current boundary exists (ADRs, immutable record)
research/            what was investigated, with outcomes and evidence
history/             what shipped in which slice, in what order
governance/          how work, planning, quality, and standards are governed
```

- A contract may summarise a decision in one sentence and then link to the ADR.
- An ADR may summarise the resulting contract in one sentence and then link here.
- Evidence documents compare their findings against a contract but never own
  current rules.

## Changing a contract

1. Change the contract document first; it is the single source of the fact.
2. Record a durable decision in an ADR when the change alters an architectural
   boundary, not merely a detail inside an accepted boundary.
3. Keep the terminology of this repository: `Port` is a physical connection
   point owned by `Equipment`; `ProcessPort` belongs to a `ProcessStep`; piping
   realization references `Connection` ids; symbol roles are presentation data
   (see [architecture.md](../dev/architecture/index.md)).
