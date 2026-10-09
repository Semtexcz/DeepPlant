# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Generate the registry-driven developer symbol gallery (Issue #121).

The gallery answers the visual questions the structural symbol tests cannot --
does the geometry read as the intended component, do the connection stubs line up
with the anchors, is a new symbol consistent with the rest of the catalogue --
without becoming a second catalogue:

```text
SymbolDefinition     canonical geometry      deepplant.symbols
        |
SYMBOLS.list()       the built-in registry
        |
render_symbol_svg()  the production renderer, used unmodified
        |
symbols/<id>.svg     derived preview artifacts
        |
index.html           derived developer artifact
```

Every card, preview, anchor marker, provenance value, and standards relationship
is derived from ``SYMBOLS.list()`` and the definition objects. No symbol id,
name, metadata, geometry, or anchor is maintained here, so a newly registered
definition appears in the gallery without changing this tool.

Behaviour
---------

- The whole page and every preview are rendered before anything is written, and
  the complete replacement gallery is written beside the target first, so an
  ordinary write failure leaves the previous gallery intact.
- The output directory is generator-owned. An existing directory is replaced
  only when it carries the ownership marker this tool writes
  (:data:`OWNERSHIP_MARKER`); an unowned directory is refused untouched, and a
  successful refresh leaves exactly the current registry's page and previews, so
  a preview of a symbol that has left the registry cannot survive as a stale
  file.
- Output is deterministic and byte-stable: no timestamps, no random values, and
  explicit ``\n`` line endings.
- The page is static: embedded CSS only, no JavaScript, no remote or raster
  resource, and no local filesystem path, so ``build/symbol-gallery/index.html``
  opens directly over ``file://``.
- The output lives in the ignored ``build/`` directory and is never committed.
  ``SymbolDefinition`` stays the canonical geometry source and generated SVG
  stays a derived artifact (ADR-0017, docs/dev/reference/symbol-library.md).

Visual review checks presentation quality only: it does not establish standards
conformance and does not promote a symbol's standards relationship to
``human-verified`` (docs/dev/workflow/standards.md).
"""

from __future__ import annotations

import math
import shutil
from dataclasses import dataclass
from html import escape
from pathlib import Path

from deepplant.symbols import (
    SYMBOLS,
    StandardsReference,
    SymbolAnchor,
    SymbolDefinition,
    SymbolRegistry,
    render_symbol_svg,
)

#: The documented default output directory: a gallery under the ignored ``build/``
#: tree, so generated previews are never staged or committed.
DEFAULT_OUTPUT_DIR = Path("build") / "symbol-gallery"

#: The preview subdirectory inside the gallery output directory.
SYMBOL_SUBDIR = "symbols"

#: The generated gallery page.
INDEX_FILENAME = "index.html"

#: The ownership marker written into the gallery output directory. Its presence
#: is the only thing that authorizes the generator to replace an existing
#: directory: a name, a location inside ``build/``, an ``index.html``, or a
#: ``symbols/`` directory never imply ownership.
OWNERSHIP_MARKER = ".deepplant-symbol-gallery"

#: The marker's stable project-authored contents: no timestamp, no random value,
#: no absolute path, and nothing machine-specific. Like the page and the
#: previews, it is a generated artifact, so it takes part in the byte-stability
#: guarantees.
OWNERSHIP_MARKER_TEXT = (
    "DeepPlant generated symbol gallery\nDo not edit or store unrelated files here.\n"
)

#: The preview area's long edge, in ``rem``; the short edge keeps the view box aspect.
PREVIEW_LONG_EDGE_REM = 12.0

#: The repository root, used only to refuse a refresh that would delete it.
_REPO_ROOT = Path(__file__).resolve().parents[1]

#: How each canonical verification state is described in the gallery, in the
#: vocabulary of the standards policy. The wording is deliberately not a
#: conformance claim: ``candidate-alignment`` records an *intended*
#: correspondence that no human has checked against an authorized copy, and
#: ``reference`` claims no correspondence for a concrete geometry at all
#: (docs/dev/workflow/standards.md, ADR-0007).
_VERIFICATION_NOTES: dict[str, str] = {
    "reference": (
        "Reference direction only: the standard guides direction, terminology, or "
        "structure, and no correspondence is claimed for this geometry."
    ),
    "candidate-alignment": (
        "Intended correspondence only: this DeepPlant-authored geometry has not been "
        "compared against an authorized copy by a human, so it is not human-verified."
    ),
    "human-verified": (
        "Human-verified: a named human compared this geometry against an authorized "
        "copy. The recorded evidence is shown below."
    ),
}


class SymbolGalleryError(ValueError):
    """Raised when the gallery cannot be generated safely at the given location."""


@dataclass(frozen=True)
class GalleryResult:
    """What one successful generation wrote, in registry order."""

    output_dir: Path
    index_path: Path
    symbol_ids: tuple[str, ...]


def generate_symbol_gallery(output_dir: Path | None = None) -> GalleryResult:
    """Generate the gallery for the built-in registry into ``output_dir``.

    ``None`` targets the documented default (:data:`DEFAULT_OUTPUT_DIR`); a test
    passes a temporary directory instead of writing into the repository.

    Both guards run before anything is written: the location must not be a broad
    path, and an existing target must be a gallery this generator owns.
    """
    target = DEFAULT_OUTPUT_DIR if output_dir is None else output_dir
    require_safe_output_dir(target)
    require_owned_gallery(target)
    definitions = SYMBOLS.list()
    page = render_gallery_page(SYMBOLS)
    documents = tuple(
        (definition.symbol_id, render_symbol_svg(definition)) for definition in definitions
    )
    _replace_gallery(target, documents, page)
    return GalleryResult(
        output_dir=target,
        index_path=target / INDEX_FILENAME,
        symbol_ids=tuple(definition.symbol_id for definition in definitions),
    )


def require_safe_output_dir(output_dir: Path) -> None:
    """Fail closed when a gallery output directory is too broad to recreate.

    Generation replaces its output directory, so the location must be a
    developer artifact directory: the filesystem root, the user's home
    directory, and the repository root are refused rather than deleted.
    """
    resolved = output_dir.resolve()
    if resolved == resolved.parent:
        raise SymbolGalleryError(f"refusing to refresh the filesystem root {resolved}")
    if resolved == Path.home().resolve():
        raise SymbolGalleryError(f"refusing to refresh the home directory {resolved}")
    if resolved == _REPO_ROOT:
        raise SymbolGalleryError(f"refusing to refresh the repository root {resolved}")


def require_owned_gallery(output_dir: Path) -> None:
    """Fail closed unless ``output_dir`` is absent or explicitly gallery-owned.

    Generation replaces its output directory, so ownership is explicit: only a
    directory carrying :data:`OWNERSHIP_MARKER` may be replaced. The name
    ``symbol-gallery``, the parent ``build/`` directory, an ``index.html``, or a
    ``symbols/`` directory never imply ownership, because any of them can belong
    to someone else. When the target exists and is not owned, nothing is written
    or deleted and the caller sees :class:`SymbolGalleryError`.
    """
    if not output_dir.exists():
        return
    if not output_dir.is_dir():
        raise SymbolGalleryError(f"refusing to replace the non-directory {output_dir}")
    if not (output_dir / OWNERSHIP_MARKER).is_file():
        raise SymbolGalleryError(
            f"refusing to replace {output_dir}: it carries no {OWNERSHIP_MARKER} "
            "ownership marker, so this generator does not own it"
        )


def render_gallery_page(registry: SymbolRegistry = SYMBOLS) -> str:
    """Render the complete static gallery page for ``registry``.

    Pure and deterministic: the page is a function of the definitions alone, so a
    test can render a test-only registry without touching the built-in
    catalogue. The built-in registry is only the default.
    """
    definitions = registry.list()
    cards = "\n".join(_render_card(definition) for definition in definitions)
    return "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>DeepPlant symbol gallery</title>",
            "<style>",
            _STYLE.rstrip("\n"),
            "</style>",
            "</head>",
            "<body>",
            _render_header(len(definitions)).rstrip("\n"),
            '<main class="gallery">',
            cards,
            "</main>",
            _render_footer().rstrip("\n"),
            "</body>",
            "</html>",
            "",  # a trailing newline, so the page is a normal text file
        ]
    )


def format_number(value: float) -> str:
    """Format one normalized coordinate deterministically for display.

    Display stays locale-independent and byte-stable: values are rounded to three
    decimals and printed without a trailing ``.0`` (``0.0`` -> ``0``,
    ``12.5`` -> ``12.5``).
    """
    rounded = round(value, 3)
    if math.isclose(rounded, round(rounded), abs_tol=1e-9):
        return str(int(round(rounded)))
    return f"{rounded:.3f}".rstrip("0").rstrip(".")


def _replace_gallery(output_dir: Path, documents: tuple[tuple[str, str], ...], page: str) -> None:
    """Replace ``output_dir`` with a completely written gallery.

    The replacement is written to a temporary sibling first and moved into place
    only once every write has succeeded, so a write failure leaves the previous
    gallery exactly as it was instead of deleting it and leaving a partial one.
    The temporary sibling is removed on both paths and never outlives this call.
    """
    staging = _temporary_sibling(output_dir, "generated")
    try:
        _write_gallery_files(staging, documents, page)
        _move_into_place(staging, output_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _write_gallery_files(
    directory: Path, documents: tuple[tuple[str, str], ...], page: str
) -> None:
    """Write one complete gallery into ``directory``, which the caller owns.

    This is the only place a gallery is materialized, so a test can make it fail
    to prove that an interrupted refresh leaves the previous gallery untouched.
    The ownership marker is written with the artifacts, so the finished directory
    is a gallery this generator may replace later.
    """
    symbol_dir = directory / SYMBOL_SUBDIR
    symbol_dir.mkdir(parents=True)
    (directory / OWNERSHIP_MARKER).write_text(OWNERSHIP_MARKER_TEXT, encoding="utf-8", newline="\n")
    for symbol_id, document in documents:
        (symbol_dir / f"{symbol_id}.svg").write_text(document, encoding="utf-8", newline="\n")
    (directory / INDEX_FILENAME).write_text(page, encoding="utf-8", newline="\n")


def _move_into_place(staging: Path, output_dir: Path) -> None:
    """Move a finished gallery from ``staging`` to ``output_dir``.

    An existing gallery is renamed aside first and removed only after the new one
    is in place, so a failed final replace restores the previous gallery rather
    than leaving the target missing. ``staging`` is a sibling of the target, so
    replacing the target can never destroy data still needed to finish the
    replacement.
    """
    if not output_dir.exists():
        staging.rename(output_dir)
        return
    backup = _temporary_sibling(output_dir, "replaced")
    output_dir.rename(backup)
    try:
        staging.rename(output_dir)
    except OSError:
        backup.rename(output_dir)
        raise
    shutil.rmtree(backup)


def _temporary_sibling(output_dir: Path, label: str) -> Path:
    """Return an unused sibling path of ``output_dir`` for temporary data.

    The name is derived from the target alone, so no random or machine-specific
    value can reach the final output, and a path that already exists is treated
    as somebody else's and skipped rather than deleted. The returned path is
    never part of the public result.
    """
    index = 0
    while True:
        candidate = output_dir.parent / f".{output_dir.name}.{label}{index}"
        if not candidate.exists():
            return candidate
        index += 1


def _render_header(count: int) -> str:
    """Render the gallery introduction, which states what the artifact is."""
    return (
        "<header>\n"
        "<h1>DeepPlant symbol gallery</h1>\n"
        "<p>Generated from the <code>deepplant.symbols</code> registry through its "
        "production renderer. A <code>SymbolDefinition</code> is the canonical "
        "geometry, every preview is a derived artifact, and this page is a derived "
        "developer artifact for visual review: it is not a second catalogue and not a "
        "standards-conformance statement.</p>\n"
        f"<p>Registered symbols: {count}</p>\n"
        "</header>\n"
    )


def _render_footer() -> str:
    """Render the closing statement about how to read the gallery."""
    return (
        "<footer>\n"
        "<p>The page is static and loads no remote resource, so it can be opened "
        "directly as a local file.</p>\n"
        "<p>Visual review checks presentation quality only. It does not establish "
        "standards conformance and does not promote a symbol to "
        "<code>human-verified</code>.</p>\n"
        "</footer>\n"
    )


def _render_card(definition: SymbolDefinition) -> str:
    """Render one symbol's card: preview, identity, anchors, provenance, standards."""
    return (
        '<article class="card">\n'
        '<div class="card-header">\n'
        f"<h2>{escape(definition.name)}</h2>\n"
        f'<p class="symbol-id">{escape(definition.symbol_id)}</p>\n'
        "</div>\n"
        '<div class="card-body">\n'
        f"{_render_preview(definition)}"
        '<div class="details">\n'
        f"{_render_identity(definition)}"
        f"{_render_anchors(definition)}"
        f"{_render_provenance(definition)}"
        f"{_render_standards(definition)}"
        "</div>\n"
        "</div>\n"
        "</article>\n"
    )


def _render_preview(definition: SymbolDefinition) -> str:
    """Render the symbol's own generated SVG with gallery-only anchor markers.

    The preview is the generated SVG file itself, and the markers are positioned
    as percentages of the definition's view box, so the overlay needs no
    JavaScript and nothing is written back into the production document.
    """
    min_x, min_y, width, height = definition.view_box
    markers = "".join(
        _render_marker(anchor, min_x, min_y, width, height) for anchor in definition.anchors
    )
    return (
        '<figure class="preview">\n'
        f'<div class="viewport" style="{_viewport_style(width, height)}">\n'
        f'<img src="{SYMBOL_SUBDIR}/{escape(definition.symbol_id)}.svg" '
        f'alt="{escape(definition.symbol_id)} symbol preview">\n'
        f'<div class="anchor-overlay" aria-hidden="true">{markers}</div>\n'
        "</div>\n"
        "<figcaption>Normalized view box "
        f"{_render_view_box(definition.view_box)} &middot; the dashed box and the "
        "dots are gallery-only</figcaption>\n"
        "</figure>\n"
    )


def _render_marker(
    anchor: SymbolAnchor, min_x: float, min_y: float, width: float, height: float
) -> str:
    """Render one gallery-only anchor marker at its normalized position."""
    left = _percent(anchor.x, min_x, width)
    top = _percent(anchor.y, min_y, height)
    label = f"{anchor.name} \u00b7 {anchor.orientation} \u00b7 {anchor.kind}"
    return (
        f'<span class="anchor anchor--{escape(anchor.kind)}" '
        f'style="left: {format_number(left)}%; top: {format_number(top)}%" '
        f'title="{escape(label)}"></span>'
    )


def _render_identity(definition: SymbolDefinition) -> str:
    """Render the definition's identity, diagram types, and notation profile."""
    return (
        "<h3>Identity</h3>\n"
        '<dl class="meta">\n'
        f"<dt>Symbol id</dt><dd>{escape(definition.symbol_id)}</dd>\n"
        f"<dt>Name</dt><dd>{escape(definition.name)}</dd>\n"
        f"<dt>Category</dt><dd>{escape(definition.category)}</dd>\n"
        f"<dt>Diagram types</dt><dd>{escape(', '.join(definition.diagram_types))}</dd>\n"
        f"<dt>Notation profile</dt><dd>{escape(definition.notation_profile)}</dd>\n"
        f"<dt>View box</dt><dd>{_render_view_box(definition.view_box)}</dd>\n"
        "</dl>\n"
    )


def _render_anchors(definition: SymbolDefinition) -> str:
    """Render every explicit connection anchor, in declaration order."""
    if not definition.anchors:
        return "<h3>Anchors</h3>\n<p>None: this symbol declares no connection anchor.</p>\n"
    rows = "".join(
        "<li>"
        f'<span class="anchor-name">{escape(anchor.name)}</span>'
        f"<span>({format_number(anchor.x)}, {format_number(anchor.y)})</span>"
        f"<span>{escape(anchor.orientation)}</span>"
        f"<span>{escape(anchor.kind)}</span>"
        "</li>\n"
        for anchor in definition.anchors
    )
    return (
        "<h3>Anchors &middot; name &middot; (x, y) &middot; orientation &middot; kind</h3>\n"
        f'<ul class="anchors">\n{rows}</ul>\n'
    )


def _render_provenance(definition: SymbolDefinition) -> str:
    """Render the asset provenance recorded on the definition itself."""
    return (
        "<h3>Asset provenance</h3>\n"
        '<dl class="meta">\n'
        f"<dt>Origin</dt><dd>{escape(definition.provenance.origin)}</dd>\n"
        f"<dt>Licence</dt><dd>{escape(definition.provenance.license)}</dd>\n"
        "</dl>\n"
    )


def _render_standards(definition: SymbolDefinition) -> str:
    """Render the standards relationship and its verification state."""
    if not definition.standards:
        return (
            "<h3>Standards relationship</h3>\n"
            "<p>None recorded: this symbol claims no standards correspondence.</p>\n"
        )
    items = "".join(_render_standards_reference(reference) for reference in definition.standards)
    return f'<h3>Standards relationship</h3>\n<ul class="standards">\n{items}</ul>\n'


def _render_standards_reference(reference: StandardsReference) -> str:
    """Render one standards relationship, its state, and the evidence recorded."""
    return (
        "<li>"
        f'<span class="standard">{escape(reference.standard)}</span> '
        f'<span class="verification">{escape(reference.verification)}</span>'
        f'<p class="note">{escape(_verification_note(reference))}</p>'
        f"{_render_evidence(reference)}"
        "</li>\n"
    )


def _verification_note(reference: StandardsReference) -> str:
    """Describe one verification state in the canonical policy's vocabulary."""
    try:
        return _VERIFICATION_NOTES[reference.verification]
    except KeyError:
        raise SymbolGalleryError(
            f"standards reference {reference.standard!r} records the unknown "
            f"verification state {reference.verification!r}"
        ) from None


def _render_evidence(reference: StandardsReference) -> str:
    """Render exactly the evidence a standards reference records, if any."""
    verified_on = None if reference.verified_on is None else reference.verified_on.isoformat()
    rows = ""
    for label, value in (
        ("Locator", reference.locator),
        ("Standard name", reference.name),
        ("Verified by", reference.verified_by),
        ("Verified on", verified_on),
    ):
        if value is not None:
            rows += f"<dt>{label}</dt><dd>{escape(value)}</dd>"
    return "" if not rows else f'<dl class="meta">{rows}</dl>'


def _render_view_box(view_box: tuple[float, float, float, float]) -> str:
    """Format a view box the way the renderer does, for display."""
    return " ".join(format_number(item) for item in view_box)


def _viewport_style(width: float, height: float) -> str:
    """Size the preview box to the definition's view box aspect ratio.

    The overlay positions anchors as percentages of this box, so the box must
    have the same aspect ratio as the view box the preview is drawn in.
    """
    scale = PREVIEW_LONG_EDGE_REM / max(width, height)
    return f"width: {format_number(width * scale)}rem; height: {format_number(height * scale)}rem"


def _percent(value: float, minimum: float, size: float) -> float:
    """Convert one normalized view-box coordinate to a percentage."""
    return (value - minimum) / size * 100.0


#: The gallery's embedded stylesheet, and the only presentation code on the page:
#: there is no JavaScript, no remote stylesheet, no remote font, and no raster
#: asset. The page declares ``color-scheme: light`` and the preview box is white,
#: because the generated SVG strokes with the themeable ``currentColor`` and a
#: browser resolves that for an ``<img>`` document against the embedder's scheme.
#: Pinning light keeps the geometry legible whatever the reader's system prefers,
#: and the dashed frame is a gallery-only border that never touches the SVG.
_STYLE = """\
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 2rem 1.5rem;
  background: #f4f5f7;
  color: #1f2933;
  font-family: system-ui, sans-serif;
  line-height: 1.5;
}
header, footer, main { max-width: 64rem; margin: 0 auto; }
h1 { margin: 0 0 0.5rem; font-size: 1.5rem; }
h2 { margin: 0; font-size: 1.15rem; }
h3 {
  margin: 1rem 0 0.35rem;
  color: #52606d;
  font-size: 0.8rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
p { margin: 0.25rem 0; }
code { font-family: ui-monospace, monospace; }
.gallery { display: grid; gap: 1.5rem; margin-top: 1.5rem; }
.card {
  padding: 1.25rem;
  border: 1px solid #cbd2d9;
  border-radius: 0.5rem;
  background: #ffffff;
}
.card-header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e4e7eb;
}
.symbol-id {
  margin: 0;
  color: #52606d;
  font-family: ui-monospace, monospace;
  font-size: 0.9rem;
}
.card-body { display: flex; flex-wrap: wrap; gap: 1.5rem; margin-top: 1rem; }
.preview { margin: 0; }
.viewport { position: relative; border: 1px dashed #9aa5b1; background: #ffffff; }
.viewport img { display: block; width: 100%; height: 100%; }
.anchor-overlay { position: absolute; inset: 0; pointer-events: none; }
.anchor { position: absolute; width: 0; height: 0; }
.anchor::before {
  content: "";
  position: absolute;
  left: -0.25rem;
  top: -0.25rem;
  width: 0.5rem;
  height: 0.5rem;
  border: 1px solid #ffffff;
  border-radius: 50%;
  background: #c0392b;
}
.anchor--signal::before { background: #1d4ed8; }
figcaption { margin-top: 0.5rem; color: #52606d; font-size: 0.8rem; }
.details { flex: 1 1 24rem; min-width: 18rem; }
dl.meta {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.1rem 0.75rem;
  margin: 0.35rem 0 0;
  font-size: 0.9rem;
}
dl.meta dt { color: #52606d; }
dl.meta dd { margin: 0; overflow-wrap: anywhere; }
ul.anchors,
ul.standards { list-style: none; margin: 0.35rem 0 0; padding: 0; font-size: 0.9rem; }
ul.anchors li { display: flex; flex-wrap: wrap; gap: 1rem; }
.anchor-name { font-family: ui-monospace, monospace; min-width: 6rem; }
ul.standards li { padding: 0.35rem 0; border-top: 1px solid #e4e7eb; }
.note { color: #52606d; font-size: 0.85rem; }
footer { margin-top: 2rem; color: #52606d; font-size: 0.85rem; }
"""


def main() -> None:
    """Generate the gallery into the documented default location."""
    result = generate_symbol_gallery()
    print(f"Generated {len(result.symbol_ids)} symbols")
    print(f"Gallery: {result.index_path}")


if __name__ == "__main__":
    main()
