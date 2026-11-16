"""Display-only import defaults; hierarchy and transforms are unchanged."""
import bpy


def hide_relationship_lines():
    for screen in getattr(bpy.data, 'screens', ()):
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_relationship_lines = False
