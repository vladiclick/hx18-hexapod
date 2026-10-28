"""Interference and collision checks with the real ST3215 models.

Horns are left out of the collision sweep on purpose: each one is bolted to the
next link and turns against its own servo case by design.
"""
import itertools

import numpy as np
import trimesh

import assembly
import layout
from scene import _matrix, _mesh


def _frame(link, pose):
    if link == 'core':
        return np.eye(4)
    leg, name = link.split('/')
    return _matrix(layout.frames(int(leg[3:]) - 1, *pose)[name])


def link_meshes(legs=(0,)):
    """Mesh of every rigid body in its own link frame (core in the robot frame)."""
    parts = assembly.core()
    for i in legs:
        parts += assembly.leg(i)
    cache, groups = {}, {}
    for p in parts:
        if p.kind == 'servo' and 'horn' in p.name:
            continue
        rel = np.linalg.inv(_frame(p.link, (0, 0, 0))) @ _matrix(p.loc)
        v, f = _mesh(p.shape, cache)
        m = trimesh.Trimesh(v, f, process=False)
        m.apply_transform(rel)
        groups.setdefault(p.link, []).append(m)
    return {k: trimesh.util.concatenate(v) for k, v in groups.items()}


class Checker:
    def __init__(self, legs=(0,)):
        self.meshes = link_meshes(legs)
        self.cm = trimesh.collision.CollisionManager()
        for name, mesh in self.meshes.items():
            self.cm.add_object(name, mesh)

    def pose(self, poses):
        """poses: {leg index: (yaw, hip, knee)}"""
        for name in self.meshes:
            if name != 'core':
                self.cm.set_transform(name, _frame(name, poses[int(name.split('/')[0][3:]) - 1]))

    def collisions(self, poses):
        self.pose(poses)
        hit, names = self.cm.in_collision_internal(return_names=True)
        return sorted(names) if hit else []

    def clearance(self, poses):
        self.pose(poses)
        return self.cm.min_distance_internal(return_names=True)


def interference(tol_mm3=0.01):
    """Exact B-rep overlap of every pair of parts of the core and leg 1 in the modelled pose.
    Parts of one vendor servo are skipped: its case shells overlap each other in the vendor file."""
    parts = assembly.core() + assembly.leg(0)
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


def sweep_leg(ranges=None, step=3.0):
    """Single leg against the core: yaw at its limits and 0, hip x knee on a grid."""
    ranges = ranges or layout.RANGES
    chk = Checker((0,))
    rng = {k: np.unique(np.r_[np.arange(lo, hi, step), hi]) for k, (lo, hi) in ranges.items()}
    bad, count = [], 0
    for yaw in (ranges['yaw'][0], 0.0, ranges['yaw'][1]):
        for hip, knee in itertools.product(rng['hip'], rng['knee']):
            count += 1
            hits = chk.collisions({0: (yaw, float(hip), float(knee))})
            if hits:
                bad.append(((yaw, float(hip), float(knee)), hits))
    return count, bad


def joint_limits(step=1.0, reach=150.0):
    """Free travel of each joint alone from the modelled pose, until the first contact."""
    chk = Checker((0,))
    out = {}
    for j, name in enumerate(('yaw', 'hip', 'knee')):
        ends = []
        for sign in (-1, 1):
            a, last = 0.0, 0.0
            while abs(a) < reach:
                a += sign * step
                q = [0.0, 0.0, 0.0]
                q[j] = a
                if chk.collisions({0: tuple(q)}):
                    break
                last = a
            ends.append(last)
        out[name] = ends
    return out


def neighbours(yaw_toward):
    """Legs 1 and 2 turned towards each other."""
    chk = Checker((0, 1))
    return chk.collisions({0: (yaw_toward, 0, 0), 1: (-yaw_toward, 0, 0)})


if __name__ == '__main__':
    n, hits = interference()
    print(f'interference: {n} parts, {len(hits)} overlapping pairs')
    for h in hits:
        print('  ', h)
    chk = Checker((0,))
    d, names = chk.clearance({0: (0, 0, 0)})
    print(f'modelled pose: min clearance {d:.2f} mm between {names}')
    n, bad = sweep_leg()
    print(f'concept ranges {layout.RANGES}: {n} poses, {len(bad)} with contact')
    for pose, h in bad[:30]:
        print('  ', pose, h)
    print('free travel from the modelled pose:', joint_limits())
    for a in (20, 30):
        print(f'neighbours turned {a} deg towards each other:', neighbours(a) or 'clear')
