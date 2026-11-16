"""Load a bounded neighborhood of exported ADTs for navigation editing."""
from pathlib import Path
import re

import bpy
from bpy_extras.io_utils import ImportHelper


def region_paths(center, radius):
    center = Path(center)
    match = re.fullmatch(r'adt_(\d+)_(\d+)\.obj', center.name, re.IGNORECASE)
    if not match:
        raise ValueError('Choose an adt_ROW_COLUMN.obj terrain tile as the region center')
    row, column = map(int, match.groups())
    selected = []
    for path in center.parent.glob('*.obj'):
        tile = re.fullmatch(r'adt_(\d+)_(\d+)\.obj', path.name, re.IGNORECASE)
        if tile:
            y, x = map(int, tile.groups())
            if abs(y-row) <= radius and abs(x-column) <= radius:
                selected.append((abs(y-row)+abs(x-column), path.name, str(path.resolve())))
    if not selected:
        raise ValueError('No exported terrain tiles found in that region')
    return [entry[2] for entry in sorted(selected)]


class WOWEXPORT_OT_import_navigation_region(bpy.types.Operator, ImportHelper):
    """Choose one ADT and load its nearby tiles without rendering textures"""
    bl_idname = 'wowexport.import_navigation_region'
    bl_label = 'Import Navigation Region'
    filename_ext = '.obj'
    filter_glob: bpy.props.StringProperty(default='adt_*.obj', options={'HIDDEN'})
    radius: bpy.props.IntProperty(name='Neighbor Radius', default=1, min=0, max=2,
                                 description='0 = one tile, 1 = up to 3×3, 2 = up to 5×5 tiles')

    def execute(self, context):
        try:
            paths = region_paths(self.filepath, self.radius)
            result = bpy.ops.import_scene.wowobj(
                directory='', files=[{'name': path} for path in paths], navigationOnly=True)
            return {'CANCELLED'} if result == {'CANCELLED'} else {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
