import bpy

# =========================================================
# FAST KEYHOLE CUT
# Select the CAR mesh.
# Requires the existing KEYHOLE_PREVIEW.
#
# Combines all preview components into one cutter,
# remeshes the cutter, then performs one Boolean.
# =========================================================

PREVIEW_PARENT_NAME = "KEYHOLE_PREVIEW"
TEMP_CUTTER_NAME = "TEMP_JOINED_KEYHOLE_CUTTER"

car = bpy.context.active_object

if car is None or car.type != "MESH":
    raise Exception(
        "Select the car mesh before running this script."
    )

if car.name.startswith("KEYHOLE_"):
    raise Exception(
        "You selected a preview object. Select the car."
    )

if bpy.context.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

preview = bpy.data.objects.get(PREVIEW_PARENT_NAME)

if preview is None:
    raise Exception(
        "KEYHOLE_PREVIEW was not found. "
        "Create and position the preview first."
    )

target_name = preview.get("target_car")

if target_name and target_name != car.name:
    raise Exception(
        f"The preview belongs to '{target_name}', "
        f"but you selected '{car.name}'."
    )

# Find preview mesh components
preview_parts = [
    obj for obj in bpy.data.objects
    if obj.type == "MESH"
    and obj.name.startswith("KEYHOLE_")
]

if not preview_parts:
    raise Exception(
        "No keyhole preview mesh objects were found."
    )

# Delete an older temporary cutter
old_temp = bpy.data.objects.get(TEMP_CUTTER_NAME)

if old_temp:
    bpy.data.objects.remove(old_temp, do_unlink=True)

# =========================================================
# Create hidden backup
# =========================================================

backup = car.copy()
backup.data = car.data.copy()
backup.animation_data_clear()
backup.name = car.name + "_BACKUP_BEFORE_KEYHOLE_CUT"

if car.users_collection:
    car.users_collection[0].objects.link(backup)
else:
    bpy.context.collection.objects.link(backup)

backup.hide_set(True)
backup.hide_render = True

print("Backup created:", backup.name)

# =========================================================
# Duplicate preview pieces
# Do not modify the original preview
# =========================================================

temporary_parts = []

for original in preview_parts:
    duplicate = original.copy()
    duplicate.data = original.data.copy()

    if car.users_collection:
        car.users_collection[0].objects.link(duplicate)
    else:
        bpy.context.collection.objects.link(duplicate)

    # Preserve exact world position
    world_matrix = original.matrix_world.copy()

    duplicate.parent = None
    duplicate.matrix_world = world_matrix
    duplicate.hide_set(False)
    duplicate.hide_viewport = False
    duplicate.display_type = "SOLID"

    temporary_parts.append(duplicate)

# =========================================================
# Join all temporary pieces
# =========================================================

bpy.ops.object.select_all(action="DESELECT")

for obj in temporary_parts:
    obj.select_set(True)

bpy.context.view_layer.objects.active = temporary_parts[0]

bpy.ops.object.join()

cutter = bpy.context.active_object
cutter.name = TEMP_CUTTER_NAME

# Apply cutter scale
bpy.ops.object.transform_apply(
    location=False,
    rotation=False,
    scale=True
)

print("Preview pieces joined.")

# =========================================================
# Remesh only the small cutter
# This merges overlapping cylinders and connectors
# =========================================================

remesh = cutter.modifiers.new(
    name="MERGE_KEYHOLE_PARTS",
    type="REMESH"
)

remesh.mode = "VOXEL"
remesh.voxel_size = 0.00015   # 0.15 mm
remesh.use_smooth_shade = False

bpy.context.view_layer.objects.active = cutter

bpy.ops.object.modifier_apply(
    modifier=remesh.name
)

print("Cutter remeshed into one solid.")

# =========================================================
# Apply one Boolean to the car
# =========================================================

bpy.ops.object.select_all(action="DESELECT")
car.select_set(True)
bpy.context.view_layer.objects.active = car

boolean = car.modifiers.new(
    name="KEYHOLE_SINGLE_BOOLEAN",
    type="BOOLEAN"
)

boolean.operation = "DIFFERENCE"
boolean.solver = "EXACT"
boolean.object = cutter

if hasattr(boolean, "use_self"):
    boolean.use_self = False

if hasattr(boolean, "use_hole_tolerant"):
    boolean.use_hole_tolerant = True

print("Applying one Boolean operation...")

try:
    bpy.ops.object.modifier_apply(
        modifier=boolean.name
    )

except Exception as error:
    cutter.hide_set(False)

    raise Exception(
        "The Boolean failed. The original preview and hidden "
        "backup are still available. "
        f"Blender error: {error}"
    )

# =========================================================
# Remove temporary cutter
# Keep original preview until successful
# =========================================================

bpy.data.objects.remove(
    cutter,
    do_unlink=True
)

# Remove original preview pieces
for obj in list(bpy.data.objects):
    if (
        obj.name == PREVIEW_PARENT_NAME
        or obj.name.startswith("KEYHOLE_")
    ):
        bpy.data.objects.remove(
            obj,
            do_unlink=True
        )

car.data.update()

bpy.ops.object.select_all(action="DESELECT")
car.select_set(True)
bpy.context.view_layer.objects.active = car

car.name = car.name.replace(
    "_WITH_KEYHOLES",
    ""
) + "_WITH_KEYHOLES"

print("KEYHOLES CUT SUCCESSFULLY")
print("Only one Boolean operation was used.")
print("Hidden backup:", backup.name)
