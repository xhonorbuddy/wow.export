"""Main-thread import scheduling, progress, and rollback for a batch of OBJs."""
import os
import time
from pathlib import Path

import bpy


class ImportSession:
    DATA = ('objects', 'collections', 'meshes', 'materials', 'images', 'node_groups')
    running = None

    def __init__(self, context, paths, settings):
        from .view_settings import hide_relationship_lines
        hide_relationship_lines()
        if ImportSession.running is not None:
            raise RuntimeError('A WoW import is already running; wait or press Esc to cancel it')
        self.context = context
        self.settings = settings
        self.paths = paths
        self.workspace = context.workspace
        self.before = {name: set(getattr(bpy.data, name)) for name in self.DATA}
        self.selected = list(context.selected_objects)
        self.active = context.view_layer.objects.active
        self.roots = []
        self.value = 0
        self.last_update = 0
        self.closed = False
        self.staging = None
        if getattr(settings, 'navigationOnly', False):
            # Unlinked data does not force Blender to rebuild a growing scene's
            # dependency graph after every modal timer slice.
            self.staging = bpy.data.collections.new('WoW Navigation Region')
            settings._collection = self.staging.objects
        self.iterator = self._run()
        context.window_manager.progress_begin(0, 100)
        ImportSession.running = self
        self.progress(0, 'Starting import')

    def progress(self, value, text):
        self.value = max(self.value, min(float(value), 100))
        now = time.perf_counter()
        if now - self.last_update < 0.1 and self.value < 100:
            return
        self.last_update = now
        self.context.window_manager.progress_update(self.value)
        if self.workspace:
            self.workspace.status_text_set(f'WoW import {self.value:.1f}% — {text} | Esc to cancel')
        for window in self.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type in {'STATUSBAR', 'VIEW_3D', 'TOPBAR'}:
                    area.tag_redraw()

    def _run(self):
        from .import_wowobj import iter_import
        for index, path in enumerate(self.paths):
            if self.staging:
                # Keep collection membership checks local to one ADT instead of
                # linking every placement into a continent-sized flat list.
                tile_collection = bpy.data.collections.new(Path(path).stem)
                self.staging.children.link(tile_collection)
                self.settings._collection = tile_collection.objects
            self.settings._progress = lambda value, text, i=index: self.progress(
                (i + value/100) * 98/len(self.paths), text)
            # A session-wide set deduplicates placements across all selected tiles.
            if not getattr(self.settings, '_import_cache_cleared', False):
                self.settings._model_ids = set()
                self.settings._models = {}
                self.settings._active_paths = set()
                self.settings._import_cache_cleared = True
            self.roots.append((yield from iter_import(path, settings=self.settings)))
            self.progress((index+1)*98/len(self.paths), f'Imported {os.path.basename(path)}')
        self.last_update = 0
        self.progress(98, 'Linking geometry into the scene')
        yield
        if self.staging:
            self.context.scene.collection.children.link(self.staging)
            self.context.view_layer.update()
        for obj in self.context.selected_objects:
            obj.select_set(False)
        for obj in self.roots:
            obj.select_set(True)
        if self.roots:
            self.context.view_layer.objects.active = self.roots[-1]
        bpy.context.scene['importedModelIDs'] = sorted(self.settings._model_ids)
        self.progress(100, 'Import complete')

    def step(self, budget=0.04):
        deadline = time.perf_counter() + budget
        while True:
            try:
                next(self.iterator)
            except StopIteration:
                return False
            if time.perf_counter() >= deadline:
                return True

    def finish(self):
        for _ in self.iterator:
            pass

    def close(self, rollback=False):
        if self.closed:
            return
        self.closed = True
        try:
            self.iterator.close()
            if rollback:
                for name in self.DATA:
                    data = getattr(bpy.data, name)
                    for block in list(data):
                        if block not in self.before[name]:
                            data.remove(block, do_unlink=True)
                for obj in self.selected:
                    obj.select_set(True)
                self.context.view_layer.objects.active = self.active
        finally:
            self.context.window_manager.progress_end()
            if self.workspace:
                self.workspace.status_text_set(None)
            self.settings._progress = None
            self.settings._models = {}
            self.settings._path_keys = {}
            self.settings._collection = None
            self.before.clear()
            ImportSession.running = None
