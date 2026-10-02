---
type: guidance
status: active
canonical_for:
  - user-getting-started
read_when:
  - start-work
  - using-deepplant
update_when:
  - cli-change
  - user-documentation-change
depends_on:
  - docs/contracts/cli.md
  - docs/contracts/yaml-format.md
decision: []
evidence: []
superseded_by: null
---

# Getting Started

> **Question this page answers:** how do I go from a repository checkout to a
> successfully validated DeepPlant model?

This is the shortest path to a first success. It uses only what DeepPlant
supports today: the `deepplant` CLI and the bundled examples.

## 1. Set up the project

From the repository root:

```bash
make setup
```

`make setup` runs `uv sync`, which creates the local environment and installs
DeepPlant with its dependencies. It needs `uv` and `make` to be installed.

## 2. Check the CLI works

```bash
uv run deepplant version
```

You should see the current DeepPlant version, for example:

```text
DeepPlant <version>
```

`uv run` executes the command inside the project environment, so you do not need
a global install.

## 3. Validate an example model

```bash
uv run deepplant validate examples/minimal-process/plant.yaml
```

A valid model prints a short summary and exits with code `0`:

```text
✓ valid DeepPlant model
✓ plant: demo
✓ equipment: 2
✓ ports: 3
✓ connections: 1
```

That is the whole loop: DeepPlant reads the YAML into typed semantic objects,
checks its structural and reference rules, and reports the result. On failure it
prints `✗ <message>` and exits with code `1` instead — see
[how-to/diagnose-validation-errors.md](how-to/diagnose-validation-errors.md).

## Where to go next

- Understand what DeepPlant is:
  [concepts/what-is-deepplant.md](concepts/what-is-deepplant.md)
- Write your own model: [how-to/author-plant-yaml.md](how-to/author-plant-yaml.md)
- Validate any model file: [how-to/validate-a-model.md](how-to/validate-a-model.md)
- Fix a validation error:
  [how-to/diagnose-validation-errors.md](how-to/diagnose-validation-errors.md)
- Render a process diagram:
  [how-to/render-process-svg.md](how-to/render-process-svg.md)
- Find the exact rules: [reference/index.md](reference/index.md)

The bundled examples are the best starting points.
[`examples/minimal-process/`](../../examples/minimal-process/README.md) is the
smallest complete model, and
[`examples/realistic-process-fragment/`](../../examples/realistic-process-fragment/README.md)
covers process steps, streams, recycle, and piping.
