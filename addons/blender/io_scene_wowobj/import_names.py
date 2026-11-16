"""Append-ordered navigation IDs avoid Blender's sorted-name list scans."""
import time

import bpy


def ordered_name(settings, label):
    if not getattr(settings, 'navigationOnly', False):
        return label
    if not hasattr(settings, '_name_epoch'):
        epoch = time.time_ns()
        # A second import in the same scene must sort after the previous batch.
        for data in (bpy.data.objects, bpy.data.meshes):
            if len(data):
                last = data[-1].name
                if last.startswith('~WN'):
                    try:
                        epoch = max(epoch, int(last[3:23])+1)
                    except ValueError:
                        pass
        settings._name_epoch = epoch
        settings._name_serial = 0
    settings._name_serial += 1
    return f'~WN{settings._name_epoch:020d}{settings._name_serial:012d}_{label[:24]}'


def new_object(settings, label, data):
    obj = bpy.data.objects.new(ordered_name(settings, label), data)
    if getattr(settings, 'navigationOnly', False):
        obj['wow_import_label'] = label
    return obj


def new_mesh(settings, label):
    return bpy.data.meshes.new(ordered_name(settings, label))
