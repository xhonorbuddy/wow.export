"""Run in a hidden Blender window to exercise real timer-driven UI imports."""
import sys
import tempfile
import time
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'addons'/'blender'))
import io_scene_wowobj as addon
from io_scene_wowobj.import_session import ImportSession

addon.register()
temporary = tempfile.TemporaryDirectory(prefix='wowobj-modal-')
path = Path(temporary.name)/'modal.obj'
path.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\n' + 'f 1 2 3\n'*20000)
ticks = []
original = ImportSession.step


def step(self, budget=0):
    ticks.append(self.value)
    return original(self, budget=0)


ImportSession.step = step
started = time.perf_counter()


def start():
    try:
        result = bpy.ops.import_scene.wowobj(filepath=str(path), importTextures=False,
                                           importLiquid=False, importWMO=False,
                                           importM2=False, importGOBJ=False, importWMOSets=False)
        assert result == {'RUNNING_MODAL'}, result
        bpy.app.timers.register(check, first_interval=0.1)
    except Exception:
        import traceback
        (ROOT/'tmp'/'blender-modal-result.txt').write_text(traceback.format_exc())
        bpy.ops.wm.quit_blender()


def check():
    if ImportSession.running is not None and time.perf_counter()-started < 60:
        return 0.1
    try:
        assert ImportSession.running is None, 'modal import timed out'
        assert len(ticks) > 5, ticks
        assert ticks == sorted(ticks), ticks
        obj = bpy.data.objects.get('modal.obj')
        assert obj and len(obj.data.polygons) == 20000
        result = f'WOWOBJ_MODAL_PASS ticks={len(ticks)}'
    except Exception:
        import traceback
        result = traceback.format_exc()
    (ROOT/'tmp'/'blender-modal-result.txt').write_text(result)
    temporary.cleanup()
    bpy.ops.wm.quit_blender()


bpy.app.timers.register(start, first_interval=1)
