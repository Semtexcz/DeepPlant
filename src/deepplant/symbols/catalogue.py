# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""The built-in machine-rendered symbol catalogue (Issue #119, expanded by #130/#132).

The catalogue intentionally spans two notation profiles. The first Issue #119
slice implements three representative ``generic-iso`` representations: a
connectable piping component (gate valve), an equipment symbol with process
anchors (centrifugal pump), and the reusable base instrumentation graphic
(local/field instrument). Issue #130 adds the first ``deepplant-default``
production representation, the restriction orifice
(``fitting.restriction_orifice``), and Issue #132 adds the three basic P&ID
valve bodies (``valve.globe``, ``valve.check``, ``valve.ball``) in the same
profile, so this is a deliberately mixed-profile catalogue and not a
single-profile one. The catalogue is expanded one reviewed representation at a
time.

The #132 valve bodies are three independent definitions, not a shared valve
glyph: the curated reference set does not give glob/two-port valves one common
outer body, so each is authored separately from its own review. Building them
also established that a solid variant mark cannot be expressed by a stroked
outline, which is why :class:`~deepplant.symbols.definition.Circle` gained one
boolean ``filled`` capability rather than a styling system.

Geometry provenance
------------------

Every definition's geometry is DeepPlant-authored project seed geometry: it is
authored here from the primitives in :mod:`deepplant.symbols.definition`, from
the DeepPlant project specification recorded in
``docs/dev/reference/symbol-seed-geometry.md``, and it carries
``AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only")``. It is
not derived from normative standard artwork: no standard figure, table content,
or normative text was copied, traced, extracted, or embedded. The private
references informed qualitative graphical form and structural decomposition
only. The normalized coordinates and primitive construction are independently
DeepPlant-authored; no artwork, source coordinates, dimensions, paths, or pixel
geometry were copied, traced, vectorized, or mechanically transferred. These
shapes are DeepPlant geometry, not claimed to be exact ISO geometry.

Standards relationship
----------------------

The standards relationship is conservative and independent of that provenance.
The three ``generic-iso`` definitions record the ISO document their geometry is
*intended* to correspond to, at the canonical ``candidate-alignment`` state,
because the geometry is DeepPlant-original, the project intends it to correspond
to that ISO family, and no human has yet compared it against an authorized copy.
The four ``deepplant-default`` definitions (the restriction orifice and the three
#132 basic valves) record no standards relationship at all (``standards=()``):
``deepplant-default`` makes no ISO/ISA/PIP conformance claim, so it requires none,
and none is invented merely to populate the field (ADR-0007). The coverage matrix
may still record a concept-level ISO reference *direction* for a `deepplant-default`
concept, but a concept-level reference is not a concrete correspondence for this
geometry. ``candidate-alignment`` claims no human verification, and human
verification is **not** a prerequisite for it
(``docs/dev/workflow/standards.md``, ADR-0007).
Only a recorded human check against an authorized copy may promote a symbol's
correspondence to ``human-verified``, and until then no locator, standard-authored
name, or other detail that is only available from restricted material is recorded
here.

Anchors
-------

Anchors are geometry: each records where a connection line leaves the symbol
(``orientation``) and which connection class the slot accepts (``kind``). Neither
flow direction nor inlet/outlet semantics are part of a graphical anchor.

Where the intended representation shows the adjacent pipeline as separate line
segments, the DeepPlant definition draws that connection to the view-box edge
instead, so the symbol is directly connectable at its anchors. Those connection
stubs are DeepPlant presentation choices, not part of the equipment body, and
each is commented as such below.
"""

from deepplant.symbols.definition import (
    AssetProvenance,
    Circle,
    Line,
    Polygon,
    StandardsReference,
    SymbolAnchor,
    SymbolDefinition,
)

#: The provenance every definition in this catalogue carries: DeepPlant-authored
#: geometry distributed under the repository licence.
DEEPP_LANT_ORIGINAL_PROVENANCE = AssetProvenance(
    origin="deepplant-original", license="AGPL-3.0-only"
)

# DeepPlant-authored project seed geometry for the gate valve
# (docs/dev/reference/symbol-seed-geometry.md, seed A): two triangles meet apex
# to apex on the process axis to form the valve body. The two horizontal stubs
# are DeepPlant's connection representation of the adjacent pipeline (a
# presentation choice, not part of the valve body). The reference document at the
# top of this module records the exact construction this geometry came from.
#
# The anchors are neutral graphical connection ports: a generic gate valve does
# not inherently have an inlet and an outlet, so neither the names nor the
# geometry may encode semantic flow direction. `port_a`/`port_b` state only where
# a line connects and which way it leaves the symbol.
GATE_VALVE = SymbolDefinition(
    symbol_id="valve.gate",
    name="Gate valve",
    category="valve",
    diagram_types=("pid",),
    notation_profile="generic-iso",
    primitives=(
        Line(x1=0.0, y1=50.0, x2=28.0, y2=50.0),
        Polygon(points=((28.0, 34.0), (28.0, 66.0), (50.0, 50.0))),
        Polygon(points=((50.0, 50.0), (72.0, 34.0), (72.0, 66.0))),
        Line(x1=72.0, y1=50.0, x2=100.0, y2=50.0),
    ),
    anchors=(
        SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process"),
        SymbolAnchor(name="port_b", x=100.0, y=50.0, orientation="east", kind="process"),
    ),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    standards=(
        # Intended correspondence only, with no human verification claimed: the
        # geometry is DeepPlant-authored, and no locator, standard-authored name,
        # or verifier evidence is recorded until a human check against an
        # authorized copy supplies it (ADR-0007).
        StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment"),
    ),
)

# DeepPlant-authored project seed geometry for the centrifugal pump
# (docs/dev/reference/symbol-seed-geometry.md, seed B): a circular casing with a
# full horizontal line through it, plus a line from the casing top and a line
# from the casing bottom, both meeting the horizontal line at the casing's
# right-hand point. The horizontal line is extended to the view-box edges as
# DeepPlant's connection representation of the adjacent pipeline.
#
# `suction` and `discharge` are meaningful engineering names for a pump and stay
# as the anchor names; the anchor geometry only records where each line leaves
# the symbol, never a flow direction.
PUMP_CENTRIFUGAL = SymbolDefinition(
    symbol_id="pump.centrifugal",
    name="Centrifugal pump",
    category="equipment",
    diagram_types=("pfd", "pid"),
    notation_profile="generic-iso",
    primitives=(
        Circle(cx=50.0, cy=50.0, r=24.0),
        Line(x1=0.0, y1=50.0, x2=100.0, y2=50.0),
        Line(x1=50.0, y1=26.0, x2=74.0, y2=50.0),
        Line(x1=50.0, y1=74.0, x2=74.0, y2=50.0),
    ),
    anchors=(
        SymbolAnchor(name="suction", x=0.0, y=50.0, orientation="west", kind="process"),
        SymbolAnchor(name="discharge", x=100.0, y=50.0, orientation="east", kind="process"),
    ),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    standards=(
        StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment"),
    ),
)

# DeepPlant-authored project seed geometry for the local/field instrument
# (docs/dev/reference/symbol-seed-geometry.md, seed C): the reusable base graphic
# is a plain instrument circle connected to the process by one vertical
# functional connection line, so the circle itself stays reusable for any
# instrument function.
#
# Deliberately absent: any function letter code (PIT, TIT, FIC, ...), tag text,
# reference designation, and also any signal connection. The base graphic must
# not assume that a local instrument has one - a local indicator may have no
# outgoing signal while a transmitter does - so a signal anchor belongs to a
# later concrete instrument-function composition, not to this base definition.
INSTRUMENT_LOCAL = SymbolDefinition(
    symbol_id="instrument.local",
    name="Local/field instrument",
    category="instrument",
    diagram_types=("pid",),
    notation_profile="generic-iso",
    primitives=(
        Circle(cx=50.0, cy=40.0, r=20.0),
        Line(x1=50.0, y1=60.0, x2=50.0, y2=100.0),
    ),
    anchors=(SymbolAnchor(name="tap", x=50.0, y=100.0, orientation="south", kind="process"),),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    standards=(
        StandardsReference(standard="ISO 15519-2:2015", verification="candidate-alignment"),
    ),
)

# DeepPlant-authored project seed geometry for the globe valve
# (docs/dev/reference/symbol-seed-geometry.md, seed E): the two-triangle valve
# body carries a small, solidly filled central disc, so the *variant mark* - not
# the outer body - distinguishes a globe valve. The two horizontal stubs are
# DeepPlant's connection representation of the adjacent pipeline (a presentation
# choice, not part of the valve body).
#
# The solid disc is why `Circle` gained `filled`: a stroked outline cannot express
# a filled mark, and the curated reference distinguishes this solid globe disc
# from the ball valve's hollow circle by exactly that. No stem, handwheel,
# actuator, letter code, tag, or flow arrow belongs to the reusable base glyph.
# The anchors are neutral: the body is symmetric and carries no flow semantics.
GLOBE_VALVE = SymbolDefinition(
    symbol_id="valve.globe",
    name="Globe valve",
    category="valve",
    diagram_types=("pid",),
    notation_profile="deepplant-default",
    primitives=(
        Line(x1=0.0, y1=50.0, x2=28.0, y2=50.0),
        Polygon(points=((28.0, 34.0), (28.0, 66.0), (50.0, 50.0))),
        Polygon(points=((50.0, 50.0), (72.0, 34.0), (72.0, 66.0))),
        Line(x1=72.0, y1=50.0, x2=100.0, y2=50.0),
        # The variant mark, drawn last so the solid disc reads over the apex.
        Circle(cx=50.0, cy=50.0, r=8.0, filled=True),
    ),
    anchors=(
        SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process"),
        SymbolAnchor(name="port_b", x=100.0, y=50.0, orientation="east", kind="process"),
    ),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    # No standards relationship: `deepplant-default` makes no ISO/ISA/PIP
    # conformance claim, so recording none is correct and nothing is invented to
    # populate the field (ADR-0007). The coverage matrix's concept-level ISO
    # reference direction is not a correspondence for this geometry.
    standards=(),
)

# DeepPlant-authored project seed geometry for the check valve
# (docs/dev/reference/symbol-seed-geometry.md, seed F): a rectangular valve body
# whose closing stroke runs corner to corner, hinged at one corner by a small
# solid peg. The two horizontal stubs are DeepPlant's connection representation
# of the adjacent pipeline, not part of the valve body.
#
# The glyph is deliberately asymmetric because a check valve is recognised by its
# one-way closing element, but that graphical asymmetry is a recognizability mark
# and not a semantic flow direction: `SymbolAnchor` carries only a geometric
# orientation, so the anchors stay the neutral `port_a`/`port_b` pair and no
# `inlet`/`outlet`/`flow_direction` is encoded. No tag, arrow, or annotation is
# part of the reusable base glyph.
CHECK_VALVE = SymbolDefinition(
    symbol_id="valve.check",
    name="Check valve",
    category="valve",
    diagram_types=("pid",),
    notation_profile="deepplant-default",
    primitives=(
        Line(x1=0.0, y1=50.0, x2=28.0, y2=50.0),
        # Rectangular body, four continuous edges.
        Line(x1=28.0, y1=34.0, x2=72.0, y2=34.0),
        Line(x1=72.0, y1=34.0, x2=72.0, y2=66.0),
        Line(x1=72.0, y1=66.0, x2=28.0, y2=66.0),
        Line(x1=28.0, y1=66.0, x2=28.0, y2=34.0),
        # Diagonal closing stroke from the hinge corner to the opposite corner.
        Line(x1=28.0, y1=34.0, x2=72.0, y2=66.0),
        Line(x1=72.0, y1=50.0, x2=100.0, y2=50.0),
        # Hinge mark, drawn last so the solid peg reads over the corner.
        Circle(cx=28.0, cy=34.0, r=5.0, filled=True),
    ),
    anchors=(
        SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process"),
        SymbolAnchor(name="port_b", x=100.0, y=50.0, orientation="east", kind="process"),
    ),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    standards=(),
)

# DeepPlant-authored project seed geometry for the ball valve
# (docs/dev/reference/symbol-seed-geometry.md, seed G): a large, hollow central
# circle is a structural body element. Four side-body diagonals run from the
# outer vertical edges to the circle circumference, so no body line passes through
# the clean circle interior. The two horizontal stubs are DeepPlant's connection
# representation of the adjacent pipeline, not part of the valve body.
#
# The circle is a stroked outline (not filled), which is exactly what separates it
# from the globe valve's solid disc. No stem, lever, actuator, tag, or flow arrow
# belongs to the reusable base glyph, and the anchors stay a symmetric neutral
# `port_a`/`port_b` pair.
BALL_VALVE = SymbolDefinition(
    symbol_id="valve.ball",
    name="Ball valve",
    category="valve",
    diagram_types=("pid",),
    notation_profile="deepplant-default",
    primitives=(
        Line(x1=0.0, y1=50.0, x2=18.0, y2=50.0),
        Line(x1=18.0, y1=34.0, x2=18.0, y2=66.0),
        Line(x1=18.0, y1=34.0, x2=38.0, y2=41.0),
        Line(x1=18.0, y1=66.0, x2=38.0, y2=59.0),
        Line(x1=82.0, y1=34.0, x2=82.0, y2=66.0),
        Line(x1=62.0, y1=41.0, x2=82.0, y2=34.0),
        Line(x1=62.0, y1=59.0, x2=82.0, y2=66.0),
        Line(x1=82.0, y1=50.0, x2=100.0, y2=50.0),
        Circle(cx=50.0, cy=50.0, r=15.0),
    ),
    anchors=(
        SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process"),
        SymbolAnchor(name="port_b", x=100.0, y=50.0, orientation="east", kind="process"),
    ),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    standards=(),
)

# DeepPlant-authored project seed geometry for the restriction orifice
# (docs/dev/reference/symbol-seed-geometry.md, seed D): two continuous outer
# transverse strokes frame a centred, split restriction stroke. The horizontal
# stubs are DeepPlant's connection representation of the adjacent pipeline up to
# the outer strokes; they are not part of the intrinsic glyph. This is the first
# built-in `deepplant-default` representation, so it records no standards
# relationship at all: the profile makes no ISO/ISA/PIP conformance claim, and no
# relationship is invented merely to populate the field.
#
# Deliberately absent: any valve body or control primitive, any tag or line
# number, and any inlet/outlet or flow-direction semantics. `port_a` / `port_b`
# are neutral process anchors whose orientation is routing geometry only.
RESTRICTION_ORIFICE = SymbolDefinition(
    symbol_id="fitting.restriction_orifice",
    name="Restriction orifice",
    category="fitting",
    diagram_types=("pid",),
    notation_profile="deepplant-default",
    primitives=(
        Line(x1=0.0, y1=50.0, x2=38.0, y2=50.0),
        Line(x1=38.0, y1=32.0, x2=38.0, y2=68.0),
        Line(x1=50.0, y1=20.0, x2=50.0, y2=43.0),
        Line(x1=50.0, y1=57.0, x2=50.0, y2=80.0),
        Line(x1=62.0, y1=32.0, x2=62.0, y2=68.0),
        Line(x1=62.0, y1=50.0, x2=100.0, y2=50.0),
    ),
    anchors=(
        SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process"),
        SymbolAnchor(name="port_b", x=100.0, y=50.0, orientation="east", kind="process"),
    ),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    # No standards relationship: `deepplant-default` makes no ISO/ISA/PIP
    # conformance claim, so recording none is the correct state and no
    # relationship, locator, or verifier evidence is invented here (ADR-0007).
    standards=(),
)

#: The definitions the built-in catalogue currently exposes, across both notation
#: profiles. The registry orders them by ``(notation_profile, symbol_id)``, so the
#: declaration order here does not affect lookup.
IMPLEMENTED_SYMBOLS: tuple[SymbolDefinition, ...] = (
    GATE_VALVE,
    GLOBE_VALVE,
    CHECK_VALVE,
    BALL_VALVE,
    PUMP_CENTRIFUGAL,
    INSTRUMENT_LOCAL,
    RESTRICTION_ORIFICE,
)
