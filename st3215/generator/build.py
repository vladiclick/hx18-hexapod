"""Build every output of HX18 ST3215 into the folder above this one.

    python build.py            # CAD, meshes, BOM and checks
    python build.py --renders  # also the PNG renders (needs node, three and playwright-core)
"""
import argparse
import csv
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import cadquery as cq

import assembly as A
import gait
import layout
import scene

OUT = Path(__file__).resolve().parents[1]
GEN = Path(__file__).resolve().parent

# file name, shape key, quantity per robot, material, colour, print orientation (rotations about x, y in degrees)
PRINTS = [
    ('core-tub', 'core_tub', 1, 'PETG', 'charcoal', (0, 0)),
    ('core-lid', 'core_lid', 1, 'PETG', 'charcoal', (0, 0)),
    ('front-arrow', 'front_arrow', 1, 'PLA', 'red', (0, 0)),
    ('battery-bay', 'battery_bay', 1, 'PETG', 'charcoal', (0, 0)),
    ('coxa', 'coxa', 6, 'PETG', 'white', (-90, 0)),
    ('coxa-cap', 'coxa_cap', 6, 'PLA', 'red', (180, 0)),
    ('femur', 'femur', 6, 'PETG', 'white', (-90, 0)),
    ('femur-cover', 'femur_cover', 6, 'PLA', 'red', (180, 0)),
    ('tibia', 'tibia', 6, 'PETG', 'white', (-90, 0)),
    ('toe-boot', 'toe_boot', 6, 'TPU 95A', 'black', None),
]
DENSITY = {'PETG': 1.27, 'PLA': 1.24, 'TPU 95A': 1.21}

HARDWARE = [
    ('Waveshare ST3215 serial bus servo (30 kg.cm, 12 V)', 18, 'one per joint, IDs 1-18'),
    ('M3 x 6 socket head screw', 72, '4 per joint into the drive horn'),
    ('M3 x 5 socket head screw', 72, '4 per joint into the idler horn (it is only 3.35 mm thick)'),
    ('M3 x 10 screw, self-tapping or with heat-set insert', 24, '4 per coxa cap'),
    ('M3 x 8 screw, self-tapping or with heat-set insert', 30, '4 per femur cover, 6 for the lid'),
    ('M3 x 14 screw, self-tapping', 6, 'battery bay to the tub floor'),
    ('M2 x 6 screw', 24, '2 per hip and knee servo, into the bottom-case holes'),
    ('M2 x 5 screw', 12, '2 per yaw servo, through the tub floor'),
    ('3S LiPo, about 106 x 35 x 25 mm (e.g. 2200 mAh) with XT60', 1, 'sits in the battery bay'),
    ('ESP32 bus-servo driver board, 65 x 50 mm envelope', 1, 'e.g. Waveshare Servo Driver with ESP32; on the tub floor'),
]


def _shank_up(shape):
    """The toe boot is printed standing on its open end, tip up."""
    t = cq.Location(cq.Vector(0, 0, -layout.TIBIA_BEND_Z))
    a = cq.Location(cq.Vector(), cq.Vector(0, 1, 0), -layout.TIBIA_BEND)
    return shape.moved(a * t).rotate((0, 0, 0), (1, 0, 0), 180)


def print_ready(key, orient):
    shape = A.shapes()[key]
    if orient is None:
        shape = _shank_up(shape)
    else:
        rx, ry = orient
        shape = shape.rotate((0, 0, 0), (1, 0, 0), rx).rotate((0, 0, 0), (0, 1, 0), ry)
    bb = shape.BoundingBox()
    return shape.translate(cq.Vector(-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def export_prints():
    (OUT / 'STL').mkdir(exist_ok=True)
    rows = []
    for name, key, qty, material, colour, orient in PRINTS:
        shape = print_ready(key, orient)
        scene.export_stl(shape, OUT / 'STL' / f'{name}.stl')
        bb = shape.BoundingBox()
        vol = shape.Volume() / 1000.0
        rows.append(dict(part=name, file=f'STL/{name}.stl', qty=qty, material=material, colour=colour,
                         volume_cm3=round(vol, 1), solid_mass_g=round(vol * DENSITY[material], 1),
                         bed_size_mm=f'{bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f}'))
    with open(OUT / 'PRINT-BOM.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(OUT / 'HARDWARE-BOM.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['item', 'qty', 'note'])
        w.writerows(HARDWARE)
    return rows


def export_cad(parts):
    scene.export_step(parts, OUT / 'hx18-st3215.step', layout.LEG_NAMES)
    printed = scene.merged_mesh(parts, kinds={'printed'})
    printed.export(OUT / 'hx18-st3215-printed-parts.stl')


def validation():
    import checks
    report = {}
    chk = checks.Checker((0,))
    st = layout.STAND
    d, names = chk.clearance({0: (st['yaw'], st['hip'], st['knee'])})
    report['stand_pose'] = dict(pose=st, min_clearance_mm=round(d, 2), closest=list(names),
                                height_mm=round(layout.stand_height(), 1))
    n_parts, overlaps = checks.interference()
    report['interference'] = dict(method='exact B-rep intersection, core + one leg, stand pose', parts=n_parts,
                                  overlapping_pairs=overlaps)
    n, bad = checks.sweep_leg(5.0)
    report['joint_sweep'] = dict(ranges_deg=layout.RANGES, step_deg=5.0, yaw_values=['min', 0, 'max'],
                                 poses=n, poses_with_contact=len(bad), contacts=[[list(p), h] for p, h in bad[:20]])
    cycle = gait.tripod()
    all_legs = checks.Checker(tuple(range(6)))
    gait_hits = [n for n, poses in enumerate(cycle) if all_legs.collisions(dict(enumerate(poses)))]
    flat = [q for poses in cycle for q in poses]
    report['tripod_gait'] = dict(frames=len(cycle), stride_mm=50, lift_mm=28, frames_with_contact=gait_hits,
                                 joint_min_deg=[round(min(q[j] for q in flat), 1) for j in range(3)],
                                 joint_max_deg=[round(max(q[j] for q in flat), 1) for j in range(3)])
    report['neighbours'] = {f'{a} deg towards each other': checks.neighbours(a) or 'clear' for a in (15, 25)}
    shapes = A.shapes()
    report['solids'] = {k: dict(valid=v.isValid(), solids=len(v.Solids()), volume_cm3=round(v.Volume() / 1000, 2))
                        for k, v in shapes.items()}
    report['servo'] = dict(model='Waveshare ST3215', source='https://files.waveshare.com/upload/5/59/ST3215-3D.zip',
                           count=18)
    with open(OUT / 'VALIDATION.json', 'w') as f:
        json.dump(report, f, indent=2)
    return report


# ------------------------------------------------------------------ renders
def _glb(parts, name):
    path = Path(tempfile.gettempdir()) / 'hx18-st3215-render' / f'{name}.glb'
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.export_glb(parts, path)
    return path


def render(glb, png, query, labels=None, modules=None):
    modules = modules or os.environ.get('HX18_NODE_MODULES')
    if labels is not None:
        lab = glb.parent / f'{glb.stem}-labels.json'
        lab.write_text(json.dumps(labels))
        query += f'&labels={lab.name}'
    subprocess.run(['node', str(GEN / 'render' / 'render.mjs'), modules, str(glb), str(png), query], check=True)


def servo_labels(parts):
    out = []
    for p in parts:
        if p.kind == 'servo' and p.name.endswith('/ top case'):
            loc = p.loc
            centre = layout.apply(loc, 12.0, 0.0, -18.6)
            sid = int(p.name.split(' ID ')[1].split(' ')[0])
            joint = p.name.split(' ')[2]
            out.append(dict(p=[centre.x, centre.y, centre.z], text=str(sid), kind=joint))
    return out


def exploded_leg():
    """Leg 1 pulled apart along its assembly directions (leg frame, all joints at 0)."""
    femur, tibia = (40.0, 0.0, 0.0), (80.0, 0.0, -20.0)
    bend = math.radians(layout.TIBIA_BEND)
    moves = [  # first match wins
        ('coxa cap', (0, 0, 55)), ('hip servo', (0, 0, 28)), ('yaw servo', (-55, 0, 0)), ('coxa', (0, 0, 0)),
        ('femur cover', (femur[0], 0, 40)), ('knee servo', (femur[0], 0, 22)), ('femur', femur),
        ('toe boot', (tibia[0] - 25 * math.sin(bend), 0, tibia[2] - 25 * math.cos(bend))), ('tibia', tibia),
    ]
    base_inv = layout.leg_base(0).inverse
    out = []
    for p in A.leg(0):
        if p.kind == 'hardware':
            continue
        d = next(v for k, v in moves if k in p.name)
        out.append(scene.Part(p.name, p.shape, p.color, cq.Location(cq.Vector(*d)) * base_inv * p.loc,
                              p.kind, p.metal, p.link))
    return out


def renders(parts):
    r = OUT / 'renders'
    r.mkdir(exist_ok=True)
    full = _glb(parts, 'robot')
    render(full, r / 'HX18-ST3215.png', 'dir=1.0,-1.25,0.8')
    render(full, r / 'HX18-ST3215-side.png', 'dir=0.12,-1,0.1&w=1800&h=1000')
    render(full, r / 'HX18-ST3215-top.png', 'dir=0,0,1&up=1,0,0&ground=0', labels=servo_labels(parts))
    render(full, r / 'HX18-ST3215-underside.png', 'dir=0.35,-0.5,-1&ground=0')
    core_open = _glb([p for p in parts if p.name not in ('Core lid', 'Front arrow', 'Battery bay')
                      and not p.name.startswith('M3 lid')], 'core-open')
    render(core_open, r / 'HX18-ST3215-core-open.png', 'dir=0.55,-0.8,1.35')
    leg_parts = [p for p in parts if p.link.startswith('leg1') or p.name.startswith('Leg 1 yaw')]
    render(_glb(leg_parts, 'leg'), r / 'Leg.png', 'dir=0.2,-1.2,0.55&ground=0')
    render(_glb(exploded_leg(), 'leg-exploded'), r / 'Leg-exploded.png', 'dir=0.25,-1.2,0.6&ground=0')


def gait_gif(frames=24):
    from PIL import Image
    tmp = Path(tempfile.gettempdir()) / 'hx18-st3215-render'
    tmp.mkdir(parents=True, exist_ok=True)
    jobs = []
    for n, poses in enumerate(gait.tripod(frames)):
        parts = A.on_ground(A.robot([dict(yaw=a, hip=h, knee=k) for a, h, k in poses]))
        jobs.append(dict(glb=str(_glb(parts, f'gait-{n:02d}')), out=str(tmp / f'gait-{n:02d}.png'),
                         query='dir=1.0,-1.25,0.62&w=960&h=600&target=0,0,62&dist=860'))
    (tmp / 'gait.json').write_text(json.dumps(jobs))
    subprocess.run(['node', str(GEN / 'render' / 'render.mjs'), os.environ.get('HX18_NODE_MODULES'),
                    str(tmp / 'gait.json')], check=True)
    images = [Image.open(j['out']).convert('RGB') for j in jobs]
    pal = images[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    images = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in images]
    images[0].save(OUT / 'renders' / 'HX18-ST3215-walk.gif', save_all=True, append_images=images[1:],
                   duration=80, loop=0, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--renders', action='store_true')
    ap.add_argument('--skip-cad', action='store_true')
    ap.add_argument('--gif', action='store_true')
    args = ap.parse_args()
    parts = A.on_ground(A.robot())
    if not args.skip_cad:
        rows = export_prints()
        export_cad(parts)
        rep = validation()
        print(json.dumps(rep['stand_pose']), rep['joint_sweep']['poses'], 'poses,',
              rep['joint_sweep']['poses_with_contact'], 'with contact')
        for r in rows:
            print(r)
    if args.renders:
        renders(parts)
    if args.gif:
        gait_gif()


if __name__ == '__main__':
    sys.exit(main())
