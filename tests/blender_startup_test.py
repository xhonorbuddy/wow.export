"""Exercise Blender's restricted addon-registration context, not direct register()."""
from pathlib import Path
import sys

import addon_utils
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'addons' / 'blender'))
module = addon_utils.enable('io_scene_wowobj', default_set=False)
assert module is not None, 'Addon failed to enable in Blender restricted context'
assert hasattr(bpy.types, 'IMPORT_SCENE_OT_wowobj'), 'Importer did not register'
assert hasattr(bpy.types, 'WOWEXPORT_PT_sidebar_panel'), 'Sidebar did not register'
from io_scene_wowobj.view_settings import hide_relationship_lines
assert bpy.app.timers.is_registered(hide_relationship_lines), 'Viewport update was not deferred'
addon_utils.disable('io_scene_wowobj', default_set=False)
assert not hasattr(bpy.types, 'IMPORT_SCENE_OT_wowobj'), 'Importer failed to unregister'
assert not bpy.app.timers.is_registered(hide_relationship_lines), 'Viewport timer survived addon disable'
print('WOWOBJ_STARTUP_RESTRICTED_PASS')
