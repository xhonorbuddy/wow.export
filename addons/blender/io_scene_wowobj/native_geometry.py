"""Optional Windows x64 geometry parser; pure Python remains the fallback."""
from array import array
import ctypes
from functools import lru_cache
from pathlib import Path
import sys


class Result(ctypes.Structure):
    _fields_ = [('vertices', ctypes.c_uint64), ('triangles', ctypes.c_uint64),
                ('positions', ctypes.c_void_p), ('indices', ctypes.c_void_p),
                ('owner', ctypes.c_void_p)]


@lru_cache(maxsize=1)
def library():
    if sys.platform != 'win32' or ctypes.sizeof(ctypes.c_void_p) != 8:
        return None
    try:
        native = ctypes.CDLL(str(Path(__file__).with_suffix('.dll')))
        native.wowobj_load.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(Result),
                                      ctypes.c_char_p, ctypes.c_uint64]
        native.wowobj_load.restype = ctypes.c_int
        native.wowobj_free.argtypes = [ctypes.POINTER(Result)]
        native.wowobj_free.restype = None
        return native
    except OSError:
        return None


def available():
    return library() is not None


def populate(mesh, path):
    native = library()
    result = Result()
    error = ctypes.create_string_buffer(512)
    if not native.wowobj_load(str(path), ctypes.byref(result), error, len(error)):
        raise ValueError(f'{Path(path).name}: {error.value.decode("utf-8", errors="replace")}')
    try:
        vertices, triangles = result.vertices, result.triangles
        if vertices > 0x7fffffff or triangles > 0x7fffffff//3:
            raise ValueError('OBJ exceeds Blender mesh element limits')
        positions, indices = array('f'), array('i')
        if vertices:
            positions.frombytes(ctypes.string_at(result.positions, vertices*12))
        if triangles:
            indices.frombytes(ctypes.string_at(result.indices, triangles*12))
        mesh.vertices.add(vertices)
        mesh.vertices.foreach_set('co', positions)
        mesh.loops.add(triangles*3)
        mesh.loops.foreach_set('vertex_index', indices)
        mesh.polygons.add(triangles)
        mesh.polygons.foreach_set('loop_start', array('i', range(0, triangles*3, 3)))
        mesh.polygons.foreach_set('loop_total', array('i', [3])*triangles)
        mesh.update(calc_edges=True)
    finally:
        native.wowobj_free(ctypes.byref(result))
