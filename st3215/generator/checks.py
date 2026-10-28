"""Collision sweep over the joint ranges, using the real ST3215 case meshes.

Horns are left out on purpose: they are bolted to the next link and touch it by design.
"""
import itertools

import numpy as np
import trimesh

import assembly
import layout
from scene import _matrix, _mesh

LINKS = ('coxa', 'femur', 'tibia')


def _frame(link, i, yaw, hip, knee):
    if link == 'core':
        return np.eye(4)
    return _matrix(layout.frames(i, yaw, hip, knee)[link.split('/')[1]])


def link_meshes(legs=(0,)):
    """Meshes of every rigid body in its own link frame (core in the robot frame)."""
    parts = assembly.core()
    for i in legs:
        parts += assembly.leg(i)
    cache, groups = {}, {}
    for p in parts:
        if 'horn' in p.name and p.kind == 'servo':
            continue
        leg = int(p.link[3]) - 1 if p.link != 'core' else 0
        rel = np.linalg.inv(_frame(p.link, leg, 0, 0, 0)) @ _matrix(p.loc)
        v, f = _mesh(p.shape, cache)
        m = trimesh.Trimesh(v, f, process=False)
        m.apply_transform(rel)
        groups.setdefault(p.link, []).append(m)
    return {k: trimesh.util.concatenate(v) for k, v in groups.items()}


class Checker:
    def __init__(self, legs=(0,)):
        self.legs = legs
        self.meshes = link_meshes(legs)
        self.cm = trimesh.collision.CollisionManager()
        for name, mesh in self.meshes.items():
            self.cm.add_object(name, mesh)

    def pose(self, poses):
        """poses: {leg index: (yaw, hip, knee)}"""
        for name in self.meshes:
            if name == 'core':
                continue
            i = int(name[3]) - 1
            self.cm.set_transform(name, _frame(name, i, *poses[i]))

    def collisions(self, poses):
        self.pose(poses)
        hit, names = self.cm.in_collision_internal(return_names=True)
        return sorted(names) if hit else []

    def clearance(self, poses):
        self.pose(poses)
        return self.cm.min_distance_internal(return_names=True)


def interference(pose=None, tol_mm3=0.01):
    """Exact (B-rep) overlap of every pair of parts of the core and leg 1, in the stand pose.
    Parts of the same vendor servo are skipped: the vendor model's case shells overlap each other."""
    pose = pose or layout.STAND
    parts = assembly.core() + assembly.leg(0, **pose)
    placed = [(p, p.placed()) for p in parts]
    boxes = [s.BoundingBox() for _, s in placed]
    hits = []
    for a, b in itertools.combinations(range(len(placed)), 2):
        pa, pb = placed[a][0], placed[b][0]
        if ' / ' in pa.name and pa.name.split(' / ')[0] == pb.name.split(' / ')[0]:
            continue
        ba, bb = boxes[a], boxes[b]
        if ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin \
                or ba.zmax < bb.zmin or bb.zmax < ba.zmin:
            continue
        v = placed[a][1].intersect(placed[b][1]).Volume()
        if v > tol_mm3:
            hits.append((pa.name, pb.name, round(v, 3)))
    return len(parts), hits


def sweep_leg(step=5.0):
    """Every (yaw, hip, knee) on a grid inside layout.RANGES, single leg against the core."""
    chk = Checker((0,))
    rng = {k: np.arange(lo, hi + 1e-6, step) for k, (lo, hi) in layout.RANGES.items()}
    bad = []
    count = 0
    for yaw in (rng['yaw'][0], 0.0, rng['yaw'][-1]):
        for hip, knee in itertools.product(rng['hip'], rng['knee']):
            count += 1
            hits = chk.collisions({0: (yaw, hip, knee)})
            if hits:
                bad.append(((float(yaw), float(hip), float(knee)), hits))
    return count, bad


def neighbours(yaw_toward=25.0):
    """Legs 1 and 2 turned towards each other in the stand pose."""
    chk = Checker((0, 1))
    st = layout.STAND
    hits = chk.collisions({0: (yaw_toward, st['hip'], st['knee']), 1: (-yaw_toward, st['hip'], st['knee'])})
    return hits


if __name__ == '__main__':
    import sys
    step = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    n, hits = interference()
    print(f'interference: {n} parts, {len(hits)} overlapping pairs', hits[:10])
    chk = Checker((0,))
    st = layout.STAND
    d, names = chk.clearance({0: (st['yaw'], st['hip'], st['knee'])})
    print(f'stand pose: min clearance {d:.2f} mm between {names}')
    n, bad = sweep_leg(step)
    print(f'{n} poses, {len(bad)} with contact')
    for pose, hits in bad[:40]:
        print('  ', pose, hits)
    for a in (15, 20, 25, 30):
        print(f'neighbours turned {a} deg towards each other:', neighbours(a) or 'clear')
