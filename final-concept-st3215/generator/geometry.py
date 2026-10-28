"""The sketch-and-extrude primitives of final-concept/Automation/HexapodV5.py, in CadQuery.

Same conventions as the Fusion script: a profile drawn on plane 'z' / 'y' / 'x' at
`offset`, sketch coordinates (a0, a1) map to (x, y) / (x, z) / (y, z), and the
extrusion runs `depth` mm along the +axis. Outlines come from the concept's own
v4_shapes and v3_core_layout modules.
"""
import sys
from pathlib import Path

import cadquery as cq

CONCEPT_SOURCE = Path(__file__).resolve().parents[2] / 'final-concept' / 'Automation' / 'HexapodV5'
sys.path.insert(0, str(CONCEPT_SOURCE))
import v4_shapes  # noqa: E402

V = cq.Vector


def to3(axis, offset, a):
    return {'z': V(a[0], a[1], offset), 'y': V(a[0], offset, a[1]), 'x': V(offset, a[0], a[1])}[axis]


AXIS = {'z': V(0, 0, 1), 'y': V(0, 1, 0), 'x': V(1, 0, 0)}


def wire(axis, offset, loop):
    kind, data = loop
    if kind == 'circle':
        x, y, r = data
        return cq.Wire.makeCircle(r, to3(axis, offset, (x, y)), AXIS[axis])
    if kind == 'arcs':
        edges = []
        for seg, coords in data:
            p = [to3(axis, offset, c) for c in coords]
            edges.append(cq.Edge.makeLine(*p) if seg == 'line' else cq.Edge.makeThreePointArc(*p))
        return cq.Wire.assembleEdges(edges)
    pts = [to3(axis, offset, a) for a in data]
    return cq.Wire.makePolygon(pts, close=True)


def rect(x0, y0, x1, y1): return ('poly', [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
def circ(x, y, r): return ('circle', (x, y, r))
def cap(a, b, r): return ('arcs', v4_shapes.capsule_entities(a, b, r))
def roundrect(x0, y0, x1, y1, r): return ('arcs', v4_shapes.rounded_rect_entities(x0, y0, x1, y1, r))
def poly(points): return ('poly', list(points))


def prism(axis, offset, loops, depth):
    out = None
    for loop in loops:
        face = cq.Face.makeFromWires(wire(axis, offset, loop))
        s = cq.Solid.extrudeLinear(face, AXIS[axis] * depth)
        out = s if out is None else out.fuse(s)
    return out


class Part:
    def __init__(self, name):
        self.name = name
        self.shape = None

    def add(self, axis, offset, loops, depth, note=''):
        s = prism(axis, offset, loops, depth)
        self.shape = s if self.shape is None else self.shape.fuse(s)
        return self

    def cut(self, axis, offset, loops, depth, note=''):
        self.shape = self.shape.cut(prism(axis, offset, loops, depth))
        return self

    def loft(self, axis, sections, op='join', note=''):
        wires = [wire(axis, off, loop) for off, loop in sections]
        s = cq.Solid.makeLoft(wires, True)
        if op == 'join':
            self.shape = s if self.shape is None else self.shape.fuse(s)
        else:
            self.shape = self.shape.cut(s)
        return self

    def solid(self):
        s = self.shape.clean()
        solids = s.Solids()
        assert len(solids) == 1, f'{self.name}: {len(solids)} solids'
        assert solids[0].isValid(), f'{self.name}: invalid'
        return solids[0]
