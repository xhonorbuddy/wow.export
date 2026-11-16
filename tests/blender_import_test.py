"""Run with Blender --background --factory-startup --python this_file."""
import os
import sys
import tempfile
import time
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'addons' / 'blender'))
import io_scene_wowobj as addon
from io_scene_wowobj.import_session import ImportSession
from io_scene_wowobj.navigation_import import region_paths

addon.register()


def settings():
    return addon.Settings(importTextures=False, importLiquid=False)


with tempfile.TemporaryDirectory(prefix='wowobj-test-') as tmp:
    root = Path(tmp)
    triangle = 'v 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\nf 1/1 2/2 3/3\n'
    (root/'basic.obj').write_text(triangle)
    # No group declaration must still import its faces.
    session = ImportSession(bpy.context, [str(root/'basic.obj')], settings())
    session.finish()
    obj = session.roots[0]
    assert len(obj.data.polygons) == 1
    assert tuple(obj.data.uv_layers[0].data[1].uv) == (1, 0)
    assert session.value == 100
    session.close()
    # Navigation imports retain geometry without allocating render-only data.
    image_count, material_count = len(bpy.data.images), len(bpy.data.materials)
    navigation = addon.Settings(navigationOnly=True)
    assert not navigation.importTextures and not navigation.useAlpha
    session = ImportSession(bpy.context, [str(root/'basic.obj')], navigation)
    session.finish()
    nav_mesh = session.roots[0].data
    assert len(nav_mesh.polygons) == 1 and not nav_mesh.uv_layers
    assert not nav_mesh.color_attributes and not nav_mesh.materials
    assert (len(bpy.data.images), len(bpy.data.materials)) == (image_count, material_count)
    session.close()
    # Neighborhood imports are bounded and put the chosen center first.
    for row in range(4):
        for column in range(4):
            (root/f'adt_{row}_{column}.obj').write_text(triangle)
    nearby = region_paths(root/'adt_1_1.obj', 1)
    assert len(nearby) == 9 and Path(nearby[0]).name == 'adt_1_1.obj'
    assert len(region_paths(root/'adt_1_1.obj', 0)) == 1
    # Partial mesh allocation is rolled back on a late UV validation failure.
    (root/'bad.obj').write_text(triangle.replace('3/3', '3/99'))
    before = {name: len(getattr(bpy.data, name)) for name in ImportSession.DATA}
    session = ImportSession(bpy.context, [str(root/'bad.obj')], settings())
    try:
        session.finish()
        raise AssertionError('invalid UV accepted')
    except ValueError:
        session.close(rollback=True)
    assert before == {name: len(getattr(bpy.data, name)) for name in ImportSession.DATA}
    # Cancellation while parsing closes files and removes partial data.
    (root/'large.obj').write_text(triangle*5000)
    session = ImportSession(bpy.context, [str(root/'large.obj')], settings())
    assert session.step(budget=0)
    session.close(rollback=True)
    assert before == {name: len(getattr(bpy.data, name)) for name in ImportSession.DATA}
    # Repeated placements share meshes; basename collisions remain separate.
    for folder in ('a', 'b'):
        (root/folder).mkdir()
        (root/folder/'model.obj').write_text(triangle)
    (root/'adt_test.obj').write_text(triangle)
    header = 'ModelFile;PositionX;PositionY;PositionZ;RotationX;RotationY;RotationZ;RotationW;ScaleFactor;ModelId;Type\n'
    rows = ''.join(f'{folder}/model.obj;0;0;0;0;0;0;1;1;{i};m2\n'
                   for i, folder in enumerate(('a', 'a', 'b')))
    (root/'adt_test_ModelPlacementInformation.csv').write_text(header+rows)
    session = ImportSession(bpy.context, [str(root/'adt_test.obj')], settings())
    values = []
    original = session.progress
    session.progress = lambda value, text: (values.append(value), original(value, text))[-1]
    session.finish()
    assert values == sorted(values), values
    models = [o for o in bpy.data.objects if o.name.startswith('model.obj')]
    assert len(models) == 3
    assert len({o.data for o in models}) == 2
    session.close()
    # Cyclic placement references fail cleanly rather than exhausting the stack.
    (root/'cycle.obj').write_text(triangle)
    (root/'cycle_ModelPlacementInformation.csv').write_text(
        header+'cycle.obj;0;0;0;0;0;0;1;1;999;m2\n')
    before = {name: len(getattr(bpy.data, name)) for name in ImportSession.DATA}
    session = ImportSession(bpy.context, [str(root/'cycle.obj')], settings())
    try:
        session.finish()
        raise AssertionError('cycle accepted')
    except ValueError as exc:
        assert 'Cyclic' in str(exc)
        session.close(rollback=True)
    assert before == {name: len(getattr(bpy.data, name)) for name in ImportSession.DATA}

print('WOWOBJ_REGRESSION_PASS')
