"""Batch liquid surfaces by type instead of creating hundreds of objects per ADT."""
from math import isfinite, radians

import bpy
from .import_names import new_object, new_mesh


def import_liquids(data, parent, settings):
    groups = {}
    for chunk in data.get('liquidChunks', []):
        yield
        if not chunk:
            continue
        for instance in chunk.get('instances', []):
            if not instance:
                continue
            width, height = instance.get('width', 8), instance.get('height', 8)
            if width <= 0 or height <= 0:
                continue
            if not isinstance(width, int) or not isinstance(height, int) or width > 8 or height > 8:
                raise ValueError('Invalid liquid instance dimensions')
            position = instance.get('worldPosition')
            if not position or len(position) != 3 or not all(map(isfinite, position)):
                raise ValueError('Liquid instance has no valid world position')
            heights = instance.get('vertexData', {}).get('height', [])
            bitmap = instance.get('bitmap', [])
            low = instance.get('minHeightLevel', 0)
            high = instance.get('maxHeightLevel', 0)
            vertices = []
            for y in range(height+1):
                for x in range(width+1):
                    index = y*(width+1)+x
                    z = (heights[index] if index < len(heights) else
                         position[1] if not heights else (low+high)/2)
                    if not isfinite(z):
                        raise ValueError('Invalid liquid surface height')
                    vertices.append((position[0]-(x-width/2)*(33.33333/8),
                                     -(position[2]-(y-height/2)*(33.33333/8)), z))
            faces = []
            for y in range(height):
                for x in range(width):
                    bit = y*width+x
                    if bitmap and bit//8 < len(bitmap) and not (bitmap[bit//8] & (1 << (bit%8))):
                        continue
                    a = y*(width+1)+x
                    faces.append((a, a+width+1, a+width+2, a+1))
            if not faces:
                continue
            liquid_type = instance.get('liquidType', 2)
            all_vertices, all_faces = groups.setdefault(liquid_type, ([], []))
            offset = len(all_vertices)
            all_vertices.extend(vertices)
            all_faces.extend(tuple(i+offset for i in face) for face in faces)

    collection = getattr(settings, '_collection', None)
    if collection is None:
        collection = bpy.context.view_layer.active_layer_collection.collection.objects
    for liquid_type, (vertices, faces) in groups.items():
        yield
        mesh = new_mesh(settings, f'Liquid_Type_{liquid_type}')
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = new_object(settings, f'Liquid_Type_{liquid_type}', mesh)
        obj.parent = parent
        obj.rotation_euler.x = radians(-90)
        obj['wow_nav_area'] = {3: 'magma', 4: 'slime'}.get(liquid_type, 'water')
        obj['wow_liquid_type'] = liquid_type
        collection.link(obj)
