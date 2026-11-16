"""Verify the optional parser against the Python geometry path in real Blender."""
from pathlib import Path
import sys
import tempfile

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'addons'/'blender'))
import io_scene_wowobj as addon
from io_scene_wowobj import native_geometry
from io_scene_wowobj.import_session import ImportSession

if not native_geometry.available():
    print('WOWOBJ_NATIVE_SKIP: optional Windows helper unavailable')
else:
    original = native_geometry.available
    try:
        with tempfile.TemporaryDirectory(prefix='WoW native test ') as temporary:
            path = Path(temporary)/'geometry_ü.obj'
            path.write_text('v +0 0 0\nv 1e0 0 0\nv 1 1 0\nv 0 1 0\n'
                            'vt 0 0\nvn 0 0 1\ng Quad\nf -4/1/1 -3/1/1 -2/1/1 -1/1/1\n')
            results = []
            for enabled in (False, True):
                native_geometry.available = lambda: enabled
                session = ImportSession(bpy.context, [str(path)], addon.Settings(navigationOnly=True))
                try:
                    session.finish()
                    mesh = session.roots[0].data
                    results.append(([tuple(v.co) for v in mesh.vertices],
                                    [tuple(p.vertices) for p in mesh.polygons]))
                finally:
                    session.close()
            assert results[0] == results[1]
            native_geometry.available = original
            for geometry in ('v 0 0 0\nf 0 1 1\n', 'v nan 0 0\n', 'v 1-2 3\n'):
                path.write_text(geometry)
                before = {name: len(getattr(bpy.data, name)) for name in ImportSession.DATA}
                session = ImportSession(bpy.context, [str(path)], addon.Settings(navigationOnly=True))
                try:
                    session.finish()
                    raise AssertionError('Invalid native geometry accepted')
                except ValueError:
                    session.close(rollback=True)
                assert before == {name: len(getattr(bpy.data, name)) for name in ImportSession.DATA}
        print('WOWOBJ_NATIVE_PASS: Python parity, negative indices, quads, Unicode paths, validation and rollback')
    finally:
        native_geometry.available = original
