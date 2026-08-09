import bpy

# ============================================================
# CUT THE LOCKING SCREW HOLES
#
# Before running:
# 1. Run your preview script.
# 2. Make sure the preview is correctly positioned.
# 3. Select ONLY the car mesh.
# 4. Run this script.
#
# This script:
# - Finds the SCREW_HOLE_PREVIEW collection
# - Duplicates all preview mesh objects
# - Joins them into one temporary cutter
# - Remeshes the cutter
# - Cuts the selected car
# - Creates a hidden backup
# - Deletes the preview after a successful cut
# ============================================================

PREVIEW_COLLECTION_NAME = "SCREW_HOLE_PREVIEW"
TEMP_CUTTER_NAME = "TEMP_SCREW_HOLE_CUTTER"

BACKUP_SUFFIX = "_BACKUP_BEFORE_SCREW_HOLE_CUT"
FINISHED_SUFFIX = "_WITH_SCREW_HOLES"

# 0.15 mm cutter remesh resolution
VOXEL_SIZE_MM = 0.15


# ============================================================
# MILLIMETRE CONVERSION
# ============================================================

scene_scale = bpy.context.scene.unit_settings.scale_length

if scene_scale <= 0:
    scene_scale = 1.0


def mm(value):
    return (value / 1000.0) / scene_scale


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")

    obj.hide_set(False)
    obj.hide_viewport = False
    obj.select_set(True)

    bpy.context.view_layer.objects.active = obj


def remove_object(obj):
    if obj is not None and obj.name in bpy.data.objects:
        bpy.data.objects.remove(
            obj,
            do_unlink=True
        )


def remove_collection(collection):
    if collection is None:
        return

    for obj in list(collection.objects):
        remove_object(obj)

    bpy.data.collections.remove(collection)


# ============================================================
# VALIDATE SELECTED CAR
# ============================================================

car = bpy.context.active_object

if car is None:
    raise RuntimeError(
        "Nothing is selected.\n"
        "Select the car mesh and run the script again."
    )

if car.type != "MESH":
    raise RuntimeError(
        f"'{car.name}' is not a mesh.\n"
        "Select the car mesh."
    )

if car.name.startswith("SCREW_"):
    raise RuntimeError(
        "You selected a screw-hole preview object.\n"
        "Select the car mesh instead."
    )

if car.name == TEMP_CUTTER_NAME:
    raise RuntimeError(
        "You selected the temporary cutter.\n"
        "Select the car mesh instead."
    )

if bpy.context.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")


# ============================================================
# FIND PREVIEW COLLECTION
# ============================================================

preview_collection = bpy.data.collections.get(
    PREVIEW_COLLECTION_NAME
)

if preview_collection is None:
    raise RuntimeError(
        f"Collection '{PREVIEW_COLLECTION_NAME}' was not found.\n"
        "Run the screw-hole preview script first."
    )


# ============================================================
# FIND PREVIEW MESH OBJECTS
# ============================================================

preview_parts = [
    obj
    for obj in preview_collection.all_objects
    if obj.type == "MESH"
]

if not preview_parts:
    raise RuntimeError(
        f"No mesh objects were found inside "
        f"'{PREVIEW_COLLECTION_NAME}'."
    )

if car in preview_parts:
    raise RuntimeError(
        "The selected car is inside the preview collection.\n"
        "Move the car outside SCREW_HOLE_PREVIEW."
    )

print("")
print("========================================")
print("SCREW-HOLE CUT STARTED")
print("========================================")
print("Selected car:", car.name)
print("Preview pieces found:", len(preview_parts))

for obj in preview_parts:
    print(" -", obj.name)


# ============================================================
# REMOVE OLD TEMPORARY CUTTER
# ============================================================

old_cutter = bpy.data.objects.get(TEMP_CUTTER_NAME)

if old_cutter is not None:
    remove_object(old_cutter)
    print("Old temporary cutter removed.")


# ============================================================
# APPLY CAR SCALE
# ============================================================

select_only(car)

bpy.ops.object.transform_apply(
    location=False,
    rotation=False,
    scale=True
)

print("Car scale applied.")


# ============================================================
# CREATE HIDDEN BACKUP
# ============================================================

backup_name = car.name + BACKUP_SUFFIX

old_backup = bpy.data.objects.get(backup_name)

if old_backup is not None:
    remove_object(old_backup)

backup = car.copy()
backup.data = car.data.copy()
backup.animation_data_clear()
backup.name = backup_name
backup.matrix_world = car.matrix_world.copy()

if car.users_collection:
    car.users_collection[0].objects.link(backup)
else:
    bpy.context.collection.objects.link(backup)

backup.hide_set(True)
backup.hide_viewport = True
backup.hide_render = True

print("Hidden backup created:", backup.name)


# ============================================================
# DUPLICATE PREVIEW PARTS
# ============================================================

temporary_parts = []

for original in preview_parts:

    duplicate = original.copy()
    duplicate.data = original.data.copy()
    duplicate.animation_data_clear()

    # Link duplicate into the car's collection
    if car.users_collection:
        car.users_collection[0].objects.link(duplicate)
    else:
        bpy.context.collection.objects.link(duplicate)

    # Preserve the exact world location
    world_matrix = original.matrix_world.copy()

    duplicate.parent = None
    duplicate.matrix_world = world_matrix

    duplicate.hide_set(False)
    duplicate.hide_viewport = False
    duplicate.hide_render = False
    duplicate.display_type = "SOLID"

    temporary_parts.append(duplicate)

if not temporary_parts:
    raise RuntimeError(
        "The screw-hole preview objects could not be duplicated."
    )

print("Preview pieces duplicated.")


# ============================================================
# JOIN DUPLICATED PARTS
# ============================================================

bpy.ops.object.select_all(action="DESELECT")

for obj in temporary_parts:
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.select_set(True)

bpy.context.view_layer.objects.active = temporary_parts[0]

try:
    bpy.ops.object.join()

except Exception as error:
    raise RuntimeError(
        "The preview pieces could not be joined.\n"
        f"Blender error: {error}"
    )

cutter = bpy.context.active_object
cutter.name = TEMP_CUTTER_NAME
cutter.display_type = "SOLID"

print("Preview pieces joined.")


# ============================================================
# APPLY CUTTER SCALE
# ============================================================

select_only(cutter)

bpy.ops.object.transform_apply(
    location=False,
    rotation=False,
    scale=True
)

print("Cutter scale applied.")


# ============================================================
# MERGE ALL OVERLAPPING CUTTER PARTS
# ============================================================

remesh = cutter.modifiers.new(
    name="MERGE_SCREW_HOLE_CUTTER",
    type="REMESH"
)

remesh.mode = "VOXEL"
remesh.voxel_size = mm(VOXEL_SIZE_MM)
remesh.use_smooth_shade = False

select_only(cutter)

print(
    "Remeshing cutter at",
    VOXEL_SIZE_MM,
    "mm..."
)

try:
    bpy.ops.object.modifier_apply(
        modifier=remesh.name
    )

except Exception as error:
    cutter.display_type = "WIRE"
    cutter.show_in_front = True

    raise RuntimeError(
        "The cutter remesh failed.\n"
        "The temporary cutter was kept for inspection.\n"
        "The hidden car backup is still available.\n"
        f"Blender error: {error}"
    )

print("Cutter merged into one solid.")


# ============================================================
# CHECK CUTTER
# ============================================================

if len(cutter.data.polygons) == 0:
    cutter.display_type = "WIRE"
    cutter.show_in_front = True

    raise RuntimeError(
        "The cutter became empty after remeshing.\n"
        "Try changing VOXEL_SIZE_MM from 0.15 to 0.10."
    )


# ============================================================
# BOOLEAN DIFFERENCE
# ============================================================

select_only(car)

boolean = car.modifiers.new(
    name="CUT_LOCKING_SCREW_HOLES",
    type="BOOLEAN"
)

boolean.operation = "DIFFERENCE"
boolean.solver = "EXACT"
boolean.object = cutter

if hasattr(boolean, "use_self"):
    boolean.use_self = False

if hasattr(boolean, "use_hole_tolerant"):
    boolean.use_hole_tolerant = True

print("Applying Boolean difference...")

try:
    bpy.ops.object.modifier_apply(
        modifier=boolean.name
    )

except Exception as error:

    # Keep cutter visible if Boolean fails
    cutter.hide_set(False)
    cutter.hide_viewport = False
    cutter.display_type = "WIRE"
    cutter.show_in_front = True

    raise RuntimeError(
        "The Boolean cut failed.\n"
        "The temporary cutter is visible in wireframe.\n"
        "The preview and hidden backup were preserved.\n"
        f"Blender error: {error}"
    )

print("Boolean cut applied successfully.")


# ============================================================
# REMOVE TEMPORARY CUTTER
# ============================================================

remove_object(cutter)

print("Temporary cutter removed.")


# ============================================================
# REMOVE ORIGINAL PREVIEW COLLECTION
# Only after the Boolean succeeds
# ============================================================

remove_collection(preview_collection)

print("Original preview removed.")


# ============================================================
# UPDATE AND RENAME CAR
# ============================================================

car.data.update()

base_name = car.name

if base_name.endswith(FINISHED_SUFFIX):
    base_name = base_name[:-len(FINISHED_SUFFIX)]

car.name = base_name + FINISHED_SUFFIX


# ============================================================
# SELECT FINISHED CAR
# ============================================================

select_only(car)

print("")
print("========================================")
print("SCREW HOLES CUT SUCCESSFULLY")
print("========================================")
print("Finished car:", car.name)
print("Hidden backup:", backup.name)
print("Outer visible depth: 2 mm")
print("Inner hidden depth: additional 4 mm")
print("Total maximum depth: approximately 6 mm")
