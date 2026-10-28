"""A flat list of coloured, placed parts and the exporters for it (STEP, GLB, STL)."""
from dataclasses import dataclass, field

import cadquery as cq
import numpy as np
import trimesh

TOLERANCE = {'printed': 0.02, 'servo': 0.05, 'preview': 0.12}
ANGULAR_TOLERANCE = {'printed': 0.1, 'servo': 0.2, 'preview': 0.4}


@dataclass
class Part:
    name: str
    shape: cq.Shape              # in its own frame; the same object may be shared by many parts
    color: tuple                 # sRGB 0..1
    loc: cq.Location = field(default_factory=cq.Location)
    kind: str = 'printed'        # printed | servo | electronics | hardware
    metal: bool = False
    link: str = 'core'           # which rigid body it moves with: core, or '<leg>/<coxa|femur|tibia>'

    def placed(self):
        return self.shape.moved(self.loc)


_CACHE = {}


def _mesh(shape, cache=None, kind='printed'):
    cache = _CACHE if cache is None else cache
    key = id(shape)
    if key not in cache:
        verts, tris = shape.tessellate(TOLERANCE.get(kind, 0.05), ANGULAR_TOLERANCE.get(kind, 0.2))
        cache[key] = (np.array([v.toTuple() for v in verts]), np.array(tris, dtype=np.int64))
    return cache[key]


def _matrix(loc):
    t = loc.wrapped.Transformation()
    m = np.eye(4)
    for r in range(3):
        for c in range(4):
            m[r, c] = t.Value(r + 1, c + 1)
    return m


def _linear(c):
    """Part colours are sRGB; glTF base colours are linear."""
    return [((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c]


def export_glb(parts, path):
    """GLB with one node per part; identical shapes share one mesh."""
    scene = trimesh.Scene()
    cache, geoms = _CACHE, {}
    for i, p in enumerate(parts):
        gkey = (id(p.shape), p.color, p.metal)
        if gkey not in geoms:
            v, f = _mesh(p.shape, cache, p.kind)
            mesh = trimesh.Trimesh(v, f, process=False)
            mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
                baseColorFactor=[*_linear(p.color), 1.0],
                metallicFactor=0.9 if p.metal else 0.0,
                roughnessFactor=0.32 if p.metal else (0.42 if p.kind == 'servo' else 0.6),
                name=f'{p.kind}-{len(geoms)}'))
            geoms[gkey] = f'g{len(geoms)}'
            scene.add_geometry(mesh, geom_name=geoms[gkey], node_name=f'{p.name}#{i}',
                               transform=_matrix(p.loc))
        else:
            scene.add_geometry(scene.geometry[geoms[gkey]], geom_name=geoms[gkey],
                               node_name=f'{p.name}#{i}', transform=_matrix(p.loc))
    scene.export(path)


def _tree_path(p, leg_names):
    """Browser path of a part: Core or 'Leg n (...)', then a servo or 'Screws' group, then the part."""
    if p.name.startswith('Leg '):
        n = int(p.name.split()[1])
    elif p.link != 'core':
        n = int(p.link[3])
    else:
        n = None
    top = 'Core' if n is None else f'Leg {n} ({leg_names[n - 1]})'
    if ' / ' in p.name:                                     # vendor servo part
        servo_name, leaf = p.name.split(' / ')
        return top, servo_name.split(' ', 2)[2] if n else servo_name, leaf
    if p.kind == 'hardware':
        return top, 'Screws', p.name
    return top, None, p.name.split(' ', 2)[2] if n and p.name.startswith('Leg ') else p.name


def export_step(parts, path, leg_names, name='HX18-ST3215'):
    """Coloured STEP assembly: Core and one sub-assembly per leg, each servo as its own sub-assembly."""
    tree = {}
    for p in parts:
        top, group, leaf = _tree_path(p, leg_names)
        tree.setdefault(top, {}).setdefault(group, []).append((leaf, p))
    root = cq.Assembly(name=name)
    for top, groups in tree.items():
        top_assy = cq.Assembly(name=top)
        for group, items in groups.items():
            target = top_assy if group is None else cq.Assembly(name=group)
            used = {}
            for leaf, p in items:
                used[leaf] = used.get(leaf, 0) + 1
                label = leaf if used[leaf] == 1 else f'{leaf} {used[leaf]}'
                target.add(p.shape, name=label, loc=p.loc, color=cq.Color(*p.color, 1.0))
            if group is not None:
                top_assy.add(target)
        root.add(top_assy)
    root.export(str(path), 'STEP')


def export_stl(shape, path, tolerance=0.02, angular=0.15):
    cq.exporters.export(cq.Workplane().add(shape), str(path), tolerance=tolerance, angularTolerance=angular)


def merged_mesh(parts, kinds=None, quality='preview'):
    """One trimesh of the given parts (all kinds when None), already placed; coarse by default."""
    cache, meshes = {}, []
    for p in parts:
        if kinds and p.kind not in kinds:
            continue
        v, f = _mesh(p.shape, cache, quality)
        m = trimesh.Trimesh(v, f, process=False)
        m.apply_transform(_matrix(p.loc))
        meshes.append(m)
    return trimesh.util.concatenate(meshes)
