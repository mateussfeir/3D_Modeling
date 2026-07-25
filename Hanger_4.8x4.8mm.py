import bpy

# =========================================================
# SINGLE HANGER TEST
#
# Plug:
#   4.8 mm × 4.8 mm
#   4 mm insertion depth
#
# J-shaped hook beneath the plug
# =========================================================

PLUG_SIZE = 0.0048
PLUG_HEIGHT = 0.004

STEM_WIDTH = 0.005
STEM_DEPTH = 0.005
STEM_HEIGHT = 0.025

HOOK_LENGTH = 0.014
HOOK_HEIGHT = 0.006

object_parts = []

def create_cube(name, location, dimensions):
    bpy.ops.mesh.primitive_cube_add(location=location)

    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dimensions

    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True
    )

    object_parts.append(obj)
    return obj

# Plug that enters the 5 mm socket
create_cube(
    "HANGER_PLUG_4_8MM",
    (0, 0, PLUG_HEIGHT / 2),
    (
        PLUG_SIZE,
        PLUG_SIZE,
        PLUG_HEIGHT
    )
)

# Vertical stem downward
stem_center_z = -STEM_HEIGHT / 2

create_cube(
    "HANGER_STEM",
    (0, 0, stem_center_z),
    (
        STEM_DEPTH,
        STEM_WIDTH,
        STEM_HEIGHT
    )
)

# Bottom horizontal section
hook_center_x = HOOK_LENGTH / 2
hook_center_z = -STEM_HEIGHT + HOOK_HEIGHT / 2

create_cube(
    "HANGER_BOTTOM",
    (hook_center_x, 0, hook_center_z),
    (
        HOOK_LENGTH,
        STEM_WIDTH,
        HOOK_HEIGHT
    )
)

# Upward retaining tip
tip_height = 0.012
tip_center_x = HOOK_LENGTH - STEM_DEPTH / 2
tip_center_z = -STEM_HEIGHT + tip_height / 2

create_cube(
    "HANGER_UP_TIP",
    (tip_center_x, 0, tip_center_z),
    (
        STEM_DEPTH,
        STEM_WIDTH,
        tip_height
    )
)

# Join all parts into one hanger
bpy.ops.object.select_all(action="DESELECT")

for part in object_parts:
    part.select_set(True)

bpy.context.view_layer.objects.active = object_parts[0]
bpy.ops.object.join()

hanger = bpy.context.active_object
hanger.name = "HANGER_TEST_4_8MM"

print("Single 4.8 mm hanger test created.")
print("Plug size: 4.8 × 4.8 mm")
print("Plug insertion length: 4 mm")
