"""Check native STL exports and make separate bed-oriented copies; never repair CAD."""
import json, math, sys
from pathlib import Path
sys.modules['networkx'] = None
import numpy as np
import trimesh

def bed_orient(mesh, axis):
    rotations = {'z': 0., 'y': math.pi/2, '-y': -math.pi/2}
    if axis not in rotations:
        raise ValueError('Unsupported bed normal: '+axis)
    result = mesh.copy()
    if rotations[axis]:
        result.apply_transform(trimesh.transformations.rotation_matrix(rotations[axis], (1, 0, 0)))
    result.apply_translation(-result.bounds[0])
    return result

def component_count(mesh):
    parents = np.arange(len(mesh.faces))
    def find(index):
        while parents[index] != index:
            index = parents[index]
        return index
    for left, right in mesh.face_adjacency:
        a, b = find(left), find(right)
        if a != b:
            parents[b] = a
    groups = {}
    for i in range(len(mesh.faces)):
        key = find(i)
        groups[key] = groups.get(key, []) + [i]
    # A closed inward-facing inner shell is a void, not a second solid.
    volumes = [trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces[indices], process=False).volume for indices in groups.values()]
    return int(sum(volume > 1e-5 for volume in volumes))

def inspect(folder):
    folder = Path(folder)
    cad = json.loads((folder/'CAD-validation.json').read_text())
    target = folder/'STL-BED-CONCEPT'
    target.mkdir(exist_ok=True)
    rows = []
    for part in cad['print_parts']:
        name = part['part']
        raw = trimesh.load_mesh(folder/'STL-CONCEPT'/(name+'.stl'))
        relative_error = abs(raw.volume/1000-part['volume_cm3'])/part['volume_cm3']
        count = component_count(raw)
        assert raw.is_watertight and raw.is_winding_consistent and raw.volume > 0, name+' invalid mesh'
        assert count == 1, name+' disconnected solids'
        assert relative_error < .002, name+' STL/BRep volume mismatch'
        placed = bed_orient(raw, part['print_bed_normal'])
        placed.export(target/(name+'.stl'))
        reopened = trimesh.load_mesh(target/(name+'.stl'))
        assert reopened.is_watertight and reopened.is_winding_consistent
        assert abs(reopened.bounds[0][2]) < 1e-5
        assert abs(reopened.volume-raw.volume)/raw.volume < 1e-5
        rows.append(dict(part=name, quantity=part['quantity'], watertight=True,
            winding_consistent=True, connected_solids=count, triangles=len(raw.faces),
            volume_error_percent=relative_error*100, bed_normal=part['print_bed_normal'],
            oriented_dimensions_mm=placed.extents.tolist(), lowest_z_mm=float(reopened.bounds[0][2])))
    result = dict(units='mm', status='mesh integrity and proposed orientation only; fit/support/strength not validated',
                  mesh_count=len(rows), parts=rows)
    (folder/'Mesh-validation.json').write_text(json.dumps(result, indent=2))
    return result

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python mesh_checks.py path/to/v3-concept')
    print(json.dumps(inspect(sys.argv[1]), indent=2))
