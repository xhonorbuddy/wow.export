"""Flatten imported world placements into Recast's right-handed, Y-up space."""
import os
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.io_utils import ExportHelper


def export_navigation(context, filename, map_id, selected_only=True, roots=None,
                      include_children=True, progress=None):
    if roots is None:
        roots = list(context.selected_objects if selected_only else context.scene.objects)
    # Roots can overlap (an ADT collection may link both a parent and its
    # descendants). Walking children_recursive for every root repeats the
    # same traversal many times on continent sized exports. Traverse the
    # object graph once, then filter the resulting unique set.
    if include_children:
        objects = set()
        pending = list(roots)
        while pending:
            obj = pending.pop()
            if obj in objects:
                continue
            objects.add(obj)
            pending.extend(obj.children)
    else:
        # Region collections link all imported meshes directly, including
        # WMO/doodad descendants. Avoid walking their shared object hierarchy.
        objects = set(roots)
    objects = {obj for obj in objects
               if obj.type == 'MESH' and not obj.get('wow_nav_exclude', False)}
    if not objects:
        raise ValueError('Select imported terrain roots or mesh objects first')
    target = Path(filename).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.obj.tmp')
    count = 0
    offset = 1
    depsgraph = context.evaluated_depsgraph_get()
    try:
        with temporary.open('w', encoding='utf-8', newline='\n', buffering=1024*1024) as output:
            output.write('# WoW navigation: Recast (Y-up); client (x,y,z) -> (y,z,x)\n')
            ordered_objects = sorted(objects, key=lambda o: o.name)
            total_objects = max(1, len(ordered_objects))
            for object_index, obj in enumerate(ordered_objects):
                evaluated = obj.evaluated_get(depsgraph) if obj.modifiers else None
                mesh = evaluated.to_mesh() if evaluated else obj.data
                try:
                    matrix = np.asarray(obj.matrix_world, dtype=np.float64)
                    flip = np.linalg.det(matrix[:3, :3]) < 0
                    mesh.calc_loop_triangles()
                    # The importer rotates raw WoW OBJ (x,height,z) into Blender
                    # (x,-z,height). This rotation reverses that without mirroring.
                    output.write('g ' + obj.name.replace('\n', '_') + '\n')
                    area = obj.get('wow_nav_area', 'ground')
                    if area not in {'ground', 'water', 'magma', 'slime'}:
                        raise ValueError(f'Unsupported navigation area on {obj.name}: {area}')
                    output.write(f'usemtl wow_nav_{area}\n')
                    # Blender's foreach_get crosses the Python/C boundary once
                    # per array instead of once per vertex and triangle. Keep
                    # formatting bounded in chunks so continent exports don't
                    # allocate a second full text representation in memory.
                    vertex_count = len(mesh.vertices)
                    coordinates = np.empty(vertex_count * 3, dtype=np.float32)
                    mesh.vertices.foreach_get('co', coordinates)
                    coordinates = coordinates.reshape((-1, 3))
                    for start in range(0, vertex_count, 131072):
                        end = min(start + 131072, vertex_count)
                        world = coordinates[start:end] @ matrix[:3, :3].T + matrix[:3, 3]
                        obj_vertices = np.column_stack((world[:, 0], world[:, 2], -world[:, 1]))
                        np.savetxt(output, obj_vertices, fmt='v %.9g %.9g %.9g')
                        if progress:
                            fraction = end / max(1, vertex_count)
                            progress(100 * (object_index + 0.5 * fraction) / total_objects,
                                     f'Vertices: {obj.name}')

                    triangle_count = len(mesh.loop_triangles)
                    triangles = np.empty(triangle_count * 3, dtype=np.int32)
                    mesh.loop_triangles.foreach_get('vertices', triangles)
                    triangles = triangles.reshape((-1, 3))
                    if area != 'ground':
                        local_normals = np.empty(triangle_count * 3, dtype=np.float32)
                        mesh.loop_triangles.foreach_get('normal', local_normals)
                        normal_matrix = np.linalg.inv(matrix[:3, :3]).T
                        world_normals = local_normals.reshape((-1, 3)) @ normal_matrix.T
                        reverse = np.logical_xor(flip, world_normals[:, 2] < 0)
                        triangles[reverse, 1], triangles[reverse, 2] = (
                            triangles[reverse, 2].copy(), triangles[reverse, 1].copy())
                    elif flip:
                        triangles[:, [1, 2]] = triangles[:, [2, 1]]
                    triangles += offset
                    for start in range(0, triangle_count, 131072):
                        np.savetxt(output, triangles[start:start + 131072],
                                   fmt='f %d %d %d')
                        if progress:
                            fraction = min(start + 131072, triangle_count) / max(1, triangle_count)
                            progress(100 * (object_index + 0.5 + 0.5 * fraction) / total_objects,
                                     f'Faces: {obj.name}')
                    count += triangle_count
                    offset += vertex_count
                finally:
                    if evaluated:
                        evaluated.to_mesh_clear()
        os.replace(temporary, target)
        setup = target.with_suffix('.gset')
        setup.write_text(f'f {target.as_posix()}\nw {map_id}\n', encoding='utf-8')
        return count
    finally:
        if temporary.exists():
            temporary.unlink()


def export_navigation_regions(context, collections, output_dir, map_id, group_size=5, progress=None, resume=False):
    """Write overlapping ADT collection windows as bounded Studio OBJ/GSET inputs."""
    import re
    from collections import defaultdict

    pattern = re.compile(r'adt_(\d+)_(\d+)$', re.IGNORECASE)
    by_tile = {}
    for collection in collections:
        match = pattern.fullmatch(collection.name)
        if match:
            by_tile[tuple(map(int, match.groups()))] = collection
    if not by_tile:
        raise ValueError('No imported adt_ROW_COLUMN collections were found')
    rows = [tile[0] for tile in by_tile]
    columns = [tile[1] for tile in by_tile]
    # Adjacent windows overlap by one ADT so nearby baked regions retain a
    # shared walkable strip at their edges.
    step = max(1, group_size - 1)
    starts_r = list(range(min(rows), max(rows) + 1, step))
    starts_c = list(range(min(columns), max(columns) + 1, step))
    if starts_r[-1] + group_size - 1 < max(rows): starts_r.append(max(rows) - group_size + 1)
    if starts_c[-1] + group_size - 1 < max(columns): starts_c.append(max(columns) - group_size + 1)
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    jobs = [(r, c) for r in starts_r for c in starts_c
            if any(r <= y < r + group_size and c <= x < c + group_size for y, x in by_tile)]
    results = []
    for index, (r, c) in enumerate(jobs, 1):
        selected = [collection for (y, x), collection in by_tile.items()
                    if r <= y < r + group_size and c <= x < c + group_size]
        region_roots = [obj for collection in selected for obj in collection.objects]
        filename = output / f'kalimdor_{r:02d}_{c:02d}.obj'
        setup = filename.with_suffix('.gset')
        if resume and filename.is_file() and setup.is_file():
            triangles = None
        else:
            triangles = export_navigation(context, filename, map_id,
                                          roots=region_roots, include_children=False)
        results.append((filename, triangles))
        if progress:
            progress(index, len(jobs), filename.name, triangles)
        context.workspace.status_text_set(
            f'Kalimdor export {index * 100 / len(jobs):.1f}% — {filename.name}')
    context.workspace.status_text_set(None)
    return results


class WOWEXPORT_OT_export_navigation(bpy.types.Operator, ExportHelper):
    """Export selected terrain roots and all their placed objects for WoW Navigation Studio"""
    bl_idname = 'wowexport.export_navigation'
    bl_label = 'Export Navigation Geometry'
    filename_ext = '.obj'
    filter_glob: bpy.props.StringProperty(default='*.obj', options={'HIDDEN'})
    map_id: bpy.props.IntProperty(name='WoW Map ID', min=0, default=0,
                                 description='Client instance map ID, not a UI map ID')
    selected_only: bpy.props.BoolProperty(name='Selected Roots and Children', default=True)

    def execute(self, context):
        try:
            wm = context.window_manager
            wm.progress_begin(0, 100)
            try:
                def report(value, detail):
                    wm.progress_update(value)
                    context.workspace.status_text_set(
                        f'Export Navigation Geometry {value:.1f}% — {detail}')
                triangles = export_navigation(context, self.filepath, self.map_id,
                    self.selected_only, progress=report)
            finally:
                wm.progress_end()
                context.workspace.status_text_set(None)
            self.report({'INFO'}, f'Exported {triangles:,} triangles and a .gset project for WoW Navigation Studio')
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
