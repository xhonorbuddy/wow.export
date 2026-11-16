"""Blender --background --factory-startup --python-exit-code 1 --python this_file."""
import sys
import tempfile
import json
from math import radians
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'addons'/'blender'))
from io_scene_wowobj.navigation_export import export_navigation
from io_scene_wowobj.import_wowobj import _iter_liquids
from io_scene_wowobj import Settings

root = bpy.data.objects.new('World root', None)
bpy.context.scene.collection.objects.link(root)
mesh = bpy.data.meshes.new('Downward liquid')
mesh.from_pydata([(0,0,0), (0,5,0), (5,5,0), (5,0,0)], [], [(0,1,2,3)])
liquid = bpy.data.objects.new('Liquid', mesh)
bpy.context.scene.collection.objects.link(liquid)
liquid.parent = root
liquid.location = (10,-20,3)
liquid['wow_nav_area'] = 'water'
for obj in bpy.context.selected_objects:
    obj.select_set(False)
root.select_set(True)
with tempfile.TemporaryDirectory(prefix='wow-nav-export-') as temporary:
    path = Path(temporary)/'world.obj'
    assert export_navigation(bpy.context, str(path), 289) == 2
    vertices = []
    faces = []
    for line in path.read_text().splitlines():
        if line.startswith('v '):
            vertices.append(tuple(map(float, line.split()[1:])))
        elif line.startswith('f '):
            faces.append([int(i)-1 for i in line.split()[1:]])
    assert vertices[0] == (10,3,20), vertices
    for face in faces:
        a,b,c = (vertices[i] for i in face)
        normal_y = (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2])
        assert normal_y > 0, (face, vertices)
    assert 'usemtl wow_nav_water' in path.read_text()
    assert 'w 289' in path.with_suffix('.gset').read_text()

    # Batched navigation liquids must preserve every masked face and placement.
    liquid_data = {'liquidChunks': []}
    for index, liquid_type in enumerate((2, 2, 3)):
        liquid_data['liquidChunks'].append({'instances': [{
            'liquidType': liquid_type, 'width': 2, 'height': 2,
            'worldPosition': [index*30, 4, 20], 'bitmap': [0b1011],
            'vertexData': {'height': [4,5,6,4,5,6,4,5,6]}}]})
    liquid_file = Path(temporary)/'liquids.json'
    liquid_file.write_text(json.dumps(liquid_data))
    parents = []
    for navigation in (False, True):
        parent = bpy.data.objects.new(f'Liquid test {navigation}', None)
        bpy.context.scene.collection.objects.link(parent)
        parent.rotation_euler.x = radians(90)
        for _ in _iter_liquids(str(liquid_file), parent,
                               Settings(importTextures=False, navigationOnly=navigation)):
            pass
        parents.append(parent)
    bpy.context.view_layer.update()

    def surfaces(parent):
        result = []
        for obj in parent.children_recursive:
            if obj.type != 'MESH':
                continue
            for polygon in obj.data.polygons:
                vertices = tuple(sorted(tuple(round(c,5) for c in obj.matrix_world @ obj.data.vertices[v].co)
                                        for v in polygon.vertices))
                result.append((obj['wow_liquid_type'], vertices))
        return sorted(result)

    assert surfaces(parents[0]) == surfaces(parents[1])
    assert len([o for o in parents[0].children_recursive if o.type == 'MESH']) == 3
    assert len([o for o in parents[1].children_recursive if o.type == 'MESH']) == 2
print('WOW_NAV_EXPORT_PASS: axes, child placement, liquid winding and map metadata')
