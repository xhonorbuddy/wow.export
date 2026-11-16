RELEASE 0.3.22 — Blender 5.0+:
Download the versioned addon ZIP from https://github.com/xhonorbuddy/wow.export/releases
Blender: Edit -> Preferences -> Add-ons -> menu -> Install from Disk.
Choose the ZIP, enable "Import WoW OBJ files with doodads", then restart Blender.
This release includes all navigation modules and the optional Windows x64 parser.
Console logging failures no longer interrupt geometry imports.

AUTOMATIC INSTALLATION:
1. Open wow.export
2. From the top-left menu, choose "Install Blender Add-on"
3. Choose "Install Automatically"
4. Restart Blender.
5. Ensure the add-on is enabled in Edit -> Preferences -> Add-ons

CONTINENTS AND NAVIGATION (0.3.19):
Use wow.export sidebar -> Import Navigation Region, choose the ADT tile at the
center of the area you want, and leave Neighbor Radius at 1 (up to 3x3 tiles).
This preserves placements and liquids while skipping textures, materials, UVs,
colors and animation metadata. Export Navigation Geometry then writes that region.
The normal OBJ import dialog also offers Navigation Geometry Only for an arbitrary
selection of files, including the full continent. Navigation mode builds data in
unlinked collections and links them once at completion, avoiding repeated scene
dependency-graph updates. Each ADT has its own collection; navigation object IDs
are ordered to avoid increasingly expensive Blender name-sorting scans. Liquid cells are batched by liquid type while preserving
all masks and heights. The new region appears when linking finishes; progress
reserves the final 2% for that work. Normal textured imports retain their behavior.
The Windows x64 addon includes native_geometry.dll for fast geometry-only parsing.
Other platforms and installations without the helper use the Python fallback.
To rebuild the optional helper, close Blender and run addons/blender/native/build.ps1
from this repository. No texture or material processing is done by the helper.
Avoid importing the entire continent with rendering textures for navigation work:
Kalimdor's 988 exported 4096x4096 textures occupy about 61.8 GiB as RGBA8 pixels
alone. Region imports let you work within memory limits without dropping collision
geometry or liquid surfaces inside the selected neighborhood.

IMPORTING LARGE WORLDS (0.3.17):
- Select all exported ADT OBJ tiles together, or choose Import Last Export.
- The status bar displays the current stage and percentage for the whole batch.
  Percentages describe completed import stages, not an estimated remaining time.
- Press Esc to cancel. Newly created import data is removed; existing scene data
  is retained. Imports run on Blender's main thread in short batches.
- Repeated placements reuse mesh data. Model caches use full file paths so models
  with the same filename in different folders do not overwrite one another.
- Missing referenced model files are reported in the console and completion warning.
  Malformed geometry stops the import with an error and removes partial data.
- One native mesh allocation or image decode must finish before cancellation can
  be processed. Available memory still limits the largest possible scene.

MANUAL INSTALLATION:
1. Locate your Blender add-on directory (%AppData%\Blender Foundation\Blender\VERSION\scripts\addons).
2. Copy this io_scene_wowobj directory into that directory.
3. If you are UPDATING the add-on, make sure to delete the __pycache__ directory found inside io_scene_wowobj.
4. Restart Blender.
5. Ensure the add-on is enabled in Edit -> Preferences -> Add-ons

LOCAL VALIDATION: All 988 Kalimdor ADTs with placements and liquids imported in
109.45 seconds using Navigation Geometry Only in background Blender 5.2.3. The
completed scene contained 209,003 objects and peaked at about 11.5 GiB working
memory. Interactive viewport rendering and undo can add overhead.
