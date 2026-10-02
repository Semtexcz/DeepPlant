---
type: guidance
status: active
canonical_for:
  - rendering-process-svg
read_when:
  - rendering-process-svg
  - using-deepplant
update_when:
  - renderer-api-change
  - renderer-behavior-change
  - user-documentation-change
depends_on:
  - docs/contracts/rendering.md
  - docs/contracts/process-model.md
decision: []
evidence: []
superseded_by: null
---

# Render a Process Diagram to SVG

> **Question this page answers:** how do I turn a `ProcessModel` into a process
> diagram today?

Rendering is **Python API only**. There is no render CLI command, no menu item,
and no interactive view. You write a few lines of Python and get an SVG document
back as a string.

## The API

```python
from deepplant import load_plant, render_process_svg

model = load_plant("examples/realistic-process-fragment/plant.yaml")

svg = render_process_svg(
    model.process,
    symbol_pack="basic",
    symbol_role_overrides={"PS-vessel": "vessel"},
)

with open("process.svg", "w", encoding="utf-8") as file:
    file.write(svg)
```

Save this as, for example, `my_render.py` and run it from the repository root:

```bash
uv run python my_render.py
```

It writes `process.svg` next to where you ran it.

## What you give it, and what you get back

- **Input:** a `ProcessModel`. The renderer never reads `Equipment`, `Port`, or
  `Connection` — only process steps and streams are drawn. The physical bootstrap
  layer therefore stays out of the diagram.
- **Output:** one complete standalone SVG document, returned as a string. It is
  deterministic: rendering the same model twice gives byte-identical output.
- **Symbol pack:** only the built-in `basic` pack exists today. An unknown pack
  fails loudly instead of silently substituting another symbol.
- **Layout:** automatic and headless. There is no way to place or drag symbols;
  layout is a fixed heuristic that may change between versions.
- **Presentation is derived, never stored.** No symbol role, coordinate, or
  routing value is written into the model or into the YAML.

## The override, and why it is needed

A step's **engineering function** is not the same thing as the **symbol** drawn
for it. The renderer maps a step's `function` to a default symbol role
(`pumping` → `pump`, `heat_exchange` → `heat_exchanger`, and so on).

The realistic fragment's `PS-vessel` has `function: unspecified`, because its real
engineering function is not known. `unspecified` has no default symbol, so the
call passes an explicit, **transient** `symbol_role_overrides` mapping:

```python
{"PS-vessel": "vessel"}
```

The override exists only for that one render call. It is never stored in
`plant.yaml`, in the model, or in a view file. Without it, rendering that model
raises `ProcessRenderError` — a presentation error, not a problem with the
semantic model.

## What does not exist

- no render CLI command
- no P&ID rendering
- no manual layout or saved coordinates
- no interactive editing
- no custom symbol-pack loading
- no persistent view configuration

## Where the exact behaviour lives

[rendering.md](../../contracts/rendering.md) is authoritative for the public
renderer API, symbol-role resolution, the layout and routing heuristics, and their
known limitations.
