# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""The implemented ``generic-iso`` symbol catalogue (Issue #119).

This module defines the representations the reviewed Issue #119 slices
implement: connectable piping components (gate, ball, and check valves, and a
reducer fitting), an equipment symbol with process anchors (centrifugal pump),
and the reusable base instrumentation graphic (local/field instrument). The
catalogue is expanded only in narrow, reviewed slices, and every definition
stays a plain explicit ``SymbolDefinition``: there is no symbol-to-symbol
composition, inheritance, or template mechanism, and no shared-geometry helper
worth its own abstraction at this catalogue size.

Geometry provenance
------------------

Every definition's geometry is DeepPlant-authored project seed geometry: it is
authored here from the primitives in :mod:`deepplant.symbols.definition`, from
the DeepPlant project specification recorded in
``docs/dev/reference/symbol-seed-geometry.md``, and it carries
``AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only")``. It is
not derived from normative standard artwork: no standard figure, table content,
or normative text was copied, traced, extracted, or embedded, and nothing was
taken from the company reference drawings. These shapes are DeepPlant geometry,
not claimed to be exact ISO geometry.

Standards relationship
----------------------

The standards relationship is conservative and independent of that provenance:
each definition records the ISO document its geometry is *intended* to correspond
to, at the canonical ``candidate-alignment`` state, because the geometry is
DeepPlant-original, the project intends it to correspond to that ISO family, and
no human has yet compared it against an authorized copy. ``candidate-alignment``
claims no human verification, and human verification is **not** a prerequisite
for it (``docs/dev/workflow/standards.md``, ADR-0007). Only a recorded human check
against an authorized copy may promote a symbol's correspondence to
``human-verified``, and until then no locator, standard-authored name, or other
detail that is only available from restricted material is recorded here.

Anchors
-------

Anchors record symbol-local connection points: each says where a connection line
leaves the symbol (``x``/``y``, ``orientation``) and which connection class the
slot accepts (``kind``). ``orientation`` is geometric only and never encodes flow
direction, while ``name`` may carry a symbol-local role such as ``port_a``,
``suction``, ``inlet``, ``outlet``, or ``large_end``. A role name does not turn
the anchor into a semantic ``ProcessPort`` or a physical port or nozzle: the
anchor stays presentation data that a consumer may later map to engineering
semantics.

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
    profile="generic-iso",
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

# DeepPlant-authored project seed geometry for the ball valve
# (docs/dev/reference/symbol-seed-geometry.md, seed D): the same bowtie body as
# the gate valve, with a circle on the process axis marking the ball. The two
# horizontal stubs are DeepPlant's connection representation of the adjacent
# pipeline (a presentation choice, not part of the valve body).
#
# Like the gate valve, a generic ball valve is not inherently an inlet/outlet
# device, so the anchors stay neutral: `port_a`/`port_b` say only where a line
# connects and which way it leaves the symbol, and no flow direction is encoded.
BALL_VALVE = SymbolDefinition(
    symbol_id="valve.ball",
    name="Ball valve",
    category="valve",
    diagram_types=("pid",),
    profile="generic-iso",
    primitives=(
        Line(x1=0.0, y1=50.0, x2=28.0, y2=50.0),
        Polygon(points=((28.0, 34.0), (28.0, 66.0), (50.0, 50.0))),
        Polygon(points=((50.0, 50.0), (72.0, 34.0), (72.0, 66.0))),
        Circle(cx=50.0, cy=50.0, r=8.0),
        Line(x1=72.0, y1=50.0, x2=100.0, y2=50.0),
    ),
    anchors=(
        SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process"),
        SymbolAnchor(name="port_b", x=100.0, y=50.0, orientation="east", kind="process"),
    ),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    standards=(
        StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment"),
    ),
)

# DeepPlant-authored project seed geometry for the check valve
# (docs/dev/reference/symbol-seed-geometry.md, seed E): one triangle on the
# process axis followed by a separate seat line, which is what makes the
# one-way character readable. The triangle and the seat line are separated by a
# gap so they never merge into one shape, and the stubs are DeepPlant's
# connection representation of the adjacent pipeline.
#
# This definition separates the two concepts the anchor contract keeps apart:
# `inlet`/`outlet` are semantic connection *roles*, while `orientation` stays
# purely geometric (`west`/`east`). No `flow_direction` field exists on a
# generic anchor, and none is added here.
CHECK_VALVE = SymbolDefinition(
    symbol_id="valve.check",
    name="Check valve",
    category="valve",
    diagram_types=("pid",),
    profile="generic-iso",
    primitives=(
        Line(x1=0.0, y1=50.0, x2=28.0, y2=50.0),
        Polygon(points=((28.0, 34.0), (28.0, 66.0), (58.0, 50.0))),
        Line(x1=62.0, y1=34.0, x2=62.0, y2=66.0),
        Line(x1=62.0, y1=50.0, x2=100.0, y2=50.0),
    ),
    anchors=(
        SymbolAnchor(name="inlet", x=0.0, y=50.0, orientation="west", kind="process"),
        SymbolAnchor(name="outlet", x=100.0, y=50.0, orientation="east", kind="process"),
    ),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    standards=(
        StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment"),
    ),
)

# DeepPlant-authored project seed geometry for the reducer
# (docs/dev/reference/symbol-seed-geometry.md, seed F): a tapered body that
# narrows from the large end to the small end, with a process stub on each side.
#
# `large_end`/`small_end` name the canonical geometry, which is what the drawing
# actually fixes. They deliberately do not imply process flow direction: a
# reducer may be used in either orientation, so the anchors are not named
# `inlet`/`outlet` and carry only geometric orientation.
FITTING_REDUCER = SymbolDefinition(
    symbol_id="fitting.reducer",
    name="Reducer",
    category="fitting",
    diagram_types=("pid",),
    profile="generic-iso",
    primitives=(
        Line(x1=0.0, y1=50.0, x2=28.0, y2=50.0),
        Polygon(points=((28.0, 34.0), (72.0, 42.0), (72.0, 58.0), (28.0, 66.0))),
        Line(x1=72.0, y1=50.0, x2=100.0, y2=50.0),
    ),
    anchors=(
        SymbolAnchor(name="large_end", x=0.0, y=50.0, orientation="west", kind="process"),
        SymbolAnchor(name="small_end", x=100.0, y=50.0, orientation="east", kind="process"),
    ),
    provenance=DEEPP_LANT_ORIGINAL_PROVENANCE,
    standards=(
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
    profile="generic-iso",
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
    profile="generic-iso",
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

#: The definitions the implemented ``generic-iso`` profile currently exposes.
#: Declaration order here is not significant: the registry exposes them in
#: stable symbol-id order.
IMPLEMENTED_SYMBOLS: tuple[SymbolDefinition, ...] = (
    GATE_VALVE,
    BALL_VALVE,
    CHECK_VALVE,
    PUMP_CENTRIFUGAL,
    FITTING_REDUCER,
    INSTRUMENT_LOCAL,
)
