---
type: guidance
status: active
canonical_for:
  - validating-a-model
read_when:
  - validating-a-model
  - using-deepplant
  - authoring-plant-yaml
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

# Validate a Model

> **Question this page answers:** how do I check that a model file is valid, and
> what do the results mean?

## The command

```bash
uv run deepplant validate <path>
```

`<path>` is the model file. From the repository root, for example:

```bash
uv run deepplant validate examples/minimal-process/plant.yaml
uv run deepplant validate examples/realistic-process-fragment/plant.yaml
uv run deepplant validate /path/to/my-plant.yaml
```

## Success

A valid model prints a summary to standard output and exits with code `0`:

```text
✓ valid DeepPlant model
✓ plant: demo
✓ equipment: 2
✓ ports: 3
✓ connections: 1
```

The counts describe the **physical/bootstrap layer only**: `equipment` counts
equipment items, `ports` counts every port they own, and `connections` counts
top-level connections. The process graph and piping submodels are not reported
yet.

## Failure

An invalid model prints one concise `✗` message to **standard error** and exits
with code `1`:

```text
✗ invalid DeepPlant model in 'my-plant.yaml': connections[0].source: unknown component 'T-999'
```

Expected problems with an authored file — a missing file, invalid YAML, an unknown
field, a broken reference — are reported this way, as a message rather than a
traceback. The exit code makes the command usable in a script:

```bash
if uv run deepplant validate my-plant.yaml; then
    echo "model is valid"
else
    echo "model is not valid"
fi
```

## What validation checks — and what it does not

Validation currently covers:

- **structural rules** — required fields, non-empty values, no unknown fields,
  unique ids;
- **reference integrity** — connections resolving to real equipment and ports,
  piping realizations resolving to real connections, process streams resolving to
  real steps and ports;
- **canonical model validation** — the checks the model objects themselves
  enforce.

It does **not** yet perform general engineering-rule validation such as DN
continuity, line-number consistency, or other process-engineering checks. A
"valid" result means the model is structurally sound and internally consistent,
not that the engineering design is correct.

## Failures, explained

For the main error classes and how to fix them, see
[diagnose-validation-errors.md](diagnose-validation-errors.md).

## Where the exact behaviour lives

- [cli.md](../../contracts/cli.md) — commands, printed output, and exit codes
- [yaml-format.md](../../contracts/yaml-format.md) — the error-message contract
