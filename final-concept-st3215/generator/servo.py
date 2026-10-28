"""The real Waveshare ST3215 servo, loaded from the vendor STEP with its own colours.

Servo frame used everywhere in the generator (mm):
  origin  on the output axis, in the outer face of the drive horn
  +Z      output axis, pointing out of the drive horn
  +X      along the case, from the output end towards the long end
  Y       across the case (right-handed)

In this frame the case spans x -10.15..35.1, y -12.4..12.4 and z -37.8..0.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cadquery as cq
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label, TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool

VENDOR_STEP = Path(__file__).resolve().parents[2] / 'vendor' / 'Waveshare-ST3215.step'

# Vendor STEP: output axis is +Y through (x=-25.5, z=0), drive-horn face at y=9.6.
_AXIS_X = -25.5
_HORN_FACE_Y = 9.6

# Measured from the vendor model, in the servo frame.
CASE_X = (-10.15, 35.10)
CASE_Y = (-12.40, 12.40)
CASE_Z = (-37.81, -2.1)          # case body including the idler bushing (-37.8) and top case (-2.1)
TOP_FACE_Z = -2.1                # flat top of the case, drive side
BOTTOM_FACE_Z = -35.2            # flat bottom of the case, idler side
BOTTOM_PAD = (17.3, 29.8, 9.3, -37.1)  # raised, tapered pad on the bottom face: x0, x1, half width (at its base), lowest z
DRIVE_HORN_Z = (-4.5, 0.0)       # drive horn disc, outer face at z=0
IDLER_HORN_Z = (-37.25, -33.9)   # idler horn, recessed 0.56 mm into the bottom case
HORN_RADIUS = 9.6
HORN_SCREW_PCD = 14.0            # 4 x M3 tapped holes (2.5 mm tap drill) at 0/90/180/270 deg
CASE_SCREWS_BOTTOM = [(8.3, -10.2), (8.3, 10.2), (32.8, -10.2), (32.8, 10.2)]  # M2 tapped, bottom face
MID_PLANE_Z = (DRIVE_HORN_Z[1] + IDLER_HORN_Z[0]) / 2   # -18.63, centre between both horn faces

PART_NAMES = {
    'ZK_122': 'middle case',
    'SG-ZIJI_15': 'top case',
    'XG-ZIJI_16': 'bottom case',
    'MOTOR-1723_3': 'motor',
    'PCB-CHAZUO_92': 'PCB',
    'GE_27': 'gear train',
    '金属舵盘（驱动） v2': 'drive horn',
    '金属舵盘（从动） v2': 'idler horn',
}
VISIBLE = {'middle case', 'top case', 'bottom case', 'drive horn', 'idler horn'}


@dataclass(frozen=True)
class ServoPart:
    name: str
    shape: cq.Shape
    color: tuple


def _vendor_to_servo_frame():
    rot = gp_Trsf()
    rot.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), 3.141592653589793 / 2)  # (x,y,z)->(x,-z,y)
    move = gp_Trsf()
    move.SetTranslation(gp_Vec(-_AXIS_X, 0, -_HORN_FACE_Y))
    return move.Multiplied(rot)


def _name(label):
    attr = TDataStd_Name()
    return attr.Get().ToExtString() if label.FindAttribute(TDataStd_Name.GetID_s(), attr) else ''


@lru_cache(maxsize=None)
def load(include_internal=False):
    """Return the servo parts in the servo frame. Internal parts are hidden by the case anyway."""
    doc = TDocStd_Document(TCollection_ExtendedString('st3215'))
    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True)
    reader.SetNameMode(True)
    if reader.ReadFile(str(VENDOR_STEP)) != IFSelect_RetDone:
        raise RuntimeError(f'cannot read {VENDOR_STEP}')
    reader.Transfer(doc)
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colors = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    roots = TDF_LabelSequence()
    shapes.GetFreeShapes(roots)
    kids = TDF_LabelSequence()
    shapes.GetComponents_s(roots.Value(1), kids)
    trsf = _vendor_to_servo_frame()
    parts = []
    for i in range(1, kids.Length() + 1):
        label = kids.Value(i)
        ref = TDF_Label()
        shapes.GetReferredShape_s(label, ref)
        name = PART_NAMES.get(_name(ref), _name(ref))
        if not include_internal and name not in VISIBLE:
            continue
        c = Quantity_Color()
        if not (colors.GetColor_s(ref, XCAFDoc_ColorType.XCAFDoc_ColorSurf, c)
                or colors.GetColor_s(label, XCAFDoc_ColorType.XCAFDoc_ColorSurf, c)):
            c = Quantity_Color(0.05, 0.05, 0.05, 0)
        shape = cq.Shape.cast(shapes.GetShape_s(label)).moved(cq.Location(trsf))
        # sRGB values from the vendor file; a pure #020202 black would read as a hole in renders.
        rgb = (max(c.Red(), 0.09), max(c.Green(), 0.09), max(c.Blue(), 0.095))
        parts.append(ServoPart(name, shape, rgb))
    return tuple(parts)
