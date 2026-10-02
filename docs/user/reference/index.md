---
type: navigation
status: active
canonical_for:
  - user-reference-navigation
read_when:
  - using-deepplant
  - find-canonical-rules
update_when:
  - user-documentation-change
depends_on:
  - docs/contracts/index.md
decision: []
evidence: []
superseded_by: null
---

# Reference

> **Question this page answers:** where do I find the exact, authoritative rule
> for something?

This page is a **router**, not a specification. `docs/user/reference/` does **not**
duplicate canonical contracts — it points at them, so every rule keeps exactly one
authoritative copy.

| Need | Read |
|---|---|
| Exact CLI behaviour (commands, output, exit codes) | [contracts/cli.md](../../contracts/cli.md) |
| YAML document shape and load/save guarantees | [contracts/yaml-format.md](../../contracts/yaml-format.md) |
| Plant / Equipment / Port / Connection semantics | [contracts/plant-model.md](../../contracts/plant-model.md) |
| ProcessStep / ProcessStream semantics | [contracts/process-model.md](../../contracts/process-model.md) |
| Piping line / segment / realization semantics | [contracts/physical-piping.md](../../contracts/physical-piping.md) |
| Renderer API and guarantees | [contracts/rendering.md](../../contracts/rendering.md) |

All of these live in the shared [contracts/](../../contracts/index.md) layer, which
is authoritative for users and developers alike. Where a how-to page and a
contract disagree, the contract wins.

## Contracts state rules; how-to pages state workflows

Contracts describe **what must hold now** — field rules, identity rules, and what
load/save or a render call guarantees. They assume you already know the workflow.
If you do not, start from a how-to page:

- [../how-to/author-plant-yaml.md](../how-to/author-plant-yaml.md)
- [../how-to/validate-a-model.md](../how-to/validate-a-model.md)
- [../how-to/diagnose-validation-errors.md](../how-to/diagnose-validation-errors.md)
- [../how-to/render-process-svg.md](../how-to/render-process-svg.md)
