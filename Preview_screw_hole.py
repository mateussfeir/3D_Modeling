import bpy
import math
from mathutils import Vector

# =========================================================
# KEYHOLE PREVIEW — DOES NOT CUT
#
# OUTER / VISIBLE FACE:
#   Top:    4 mm
#   Bottom: 8 mm
#
# INNER / HIDDEN FACE:
#   Top:    8 mm
#   Bottom: 8 mm
# =========================================================

PREVIEW_PARENT = "KEYHOLE_PREVIEW"

HORIZONTAL_SPACING = 0.08   # 8 mm between keyholes
VERTICAL_SPACING = 0.008     # 8 mm top-to-bottom centers

OUTER_TOP_DIAMETER = 0.004
OUTER_BOTTOM_DIAMETER = 0.008

INNER_TOP_DIAMETER = 0.008
INNER_BOTTOM_DIAMETER = 0.008

OUTER_DEPTH = 0.002          # 2 mm visible layer
INNER_DEPTH = 0.004          # 4 mm hidden cavity

car = bpy.context.active_object

if car is None or car.type != "MESH":
    raise Exception("Select the car mesh before running the script.")

if car.name.startswith(("KEYHOLE_", "SCREW_")):
    raise Exception("Select the car, not a preview object.")

if bpy.context.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

# ---------------------------------------------------------
# Delete previous preview objects
# ---------------------------------------------------------

for obj in list(bpy.data.objects):
    if (
        obj.name == PREVIEW_PARENT
        or obj.name.startswith("KEYHOLE_")
        or obj.name.startswith("SCREW_")
    ):
        bpy.data.objects.remove(obj, do_unlink=True)

# ---------------------------------------------------------
# Find the car's world-space bounds
# ---------------------------------------------------------

corners = [
    car.matrix_world @ Vector(corner)
    for corner in car.bound_box
]

min_x = min(p.x for p in corners)
max_x = max(p.x for p in corners)

min_y = min(p.y for p in corners)
max_y = max(p.y for p in corners)

min_z = min(p.z for p in corners)
max_z = max(p.z for p in corners)

car_width = max_y - min_y
car_height = max_z - min_z

center_y = (min_y + max_y) / 2

# The new flat cut surface is assumed to be minimum X
surface_x = min_x

# Initial keyhole height
center_z = min_z + car_height * 0.72

# Keep requested 100 mm spacing when it fits
safe_spacing = min(
    HORIZONTAL_SPACING,
    max(car_width - 0.020, 0.020)
)

left_y = center_y - safe_spacing / 2
right_y = center_y + safe_spacing / 2

top_z = center_z + VERTICAL_SPACING / 2
bottom_z = center_z - VERTICAL_SPACING / 2

# ---------------------------------------------------------
# Create movable preview controller
# ---------------------------------------------------------

bpy.ops.object.empty_add(
    type="PLAIN_AXES",
    location=(surface_x, center_y, center_z)
)

controller = bpy.context.active_object
controller.name = PREVIEW_PARENT
controller.show_in_front = True
controller.empty_display_size = 0.010

controller["target_car"] = car.name
controller["horizontal_spacing_mm"] = safe_spacing * 1000
controller["vertical_spacing_mm"] = VERTICAL_SPACING * 1000

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def parent_preserve_world(obj):
    world_matrix = obj.matrix_world.copy()
    obj.parent = controller
    obj.matrix_world = world_matrix


def create_cylinder(
    name,
    x,
    y,
    z,
    diameter,
    depth,
    display_type
):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=diameter / 2,
        depth=depth,
        location=(x, y, z),
        rotation=(0, math.radians(90), 0)
    )

    obj = bpy.context.active_object
    obj.name = name
    obj.display_type = display_type
    obj.show_in_front = True

    parent_preserve_world(obj)

    return obj


def create_connector(
    name,
    x,
    y,
    z,
    width,
    height,
    depth,
    display_type
):
    bpy.ops.mesh.primitive_cube_add(
        location=(x, y, z)
    )

    obj = bpy.context.active_object
    obj.name = name

    obj.dimensions = (
        depth,   # X: depth into car
        width,   # Y: slot width
        height   # Z: vertical size
    )

    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True
    )

    obj.display_type = display_type
    obj.show_in_front = True

    parent_preserve_world(obj)

    return obj

# ---------------------------------------------------------
# Create one keyhole preview
# ---------------------------------------------------------

def create_keyhole(label, y_position):

    # Visible outer layer
    outer_x = surface_x + OUTER_DEPTH / 2

    create_cylinder(
        f"KEYHOLE_{label}_OUTER_TOP_4MM",
        outer_x,
        y_position,
        top_z,
        OUTER_TOP_DIAMETER,
        OUTER_DEPTH,
        "SOLID"
    )

    create_cylinder(
        f"KEYHOLE_{label}_OUTER_BOTTOM_8MM",
        outer_x,
        y_position,
        bottom_z,
        OUTER_BOTTOM_DIAMETER,
        OUTER_DEPTH,
        "SOLID"
    )

    # Narrow visible slot connecting top and bottom
    create_connector(
        f"KEYHOLE_{label}_OUTER_SLOT_4MM",
        outer_x,
        y_position,
        center_z,
        OUTER_TOP_DIAMETER,
        VERTICAL_SPACING,
        OUTER_DEPTH,
        "SOLID"
    )

    # Hidden internal layer
    inner_x = (
        surface_x
        + OUTER_DEPTH
        + INNER_DEPTH / 2
    )

    create_cylinder(
        f"KEYHOLE_{label}_INNER_TOP_8MM",
        inner_x,
        y_position,
        top_z,
        INNER_TOP_DIAMETER,
        INNER_DEPTH,
        "WIRE"
    )

    create_cylinder(
        f"KEYHOLE_{label}_INNER_BOTTOM_8MM",
        inner_x,
        y_position,
        bottom_z,
        INNER_BOTTOM_DIAMETER,
        INNER_DEPTH,
        "WIRE"
    )

    # Wide internal channel for the screw head
    create_connector(
        f"KEYHOLE_{label}_INNER_CHANNEL_8MM",
        inner_x,
        y_position,
        center_z,
        INNER_TOP_DIAMETER,
        VERTICAL_SPACING,
        INNER_DEPTH,
        "WIRE"
    )

# Create both keyholes
create_keyhole("LEFT", left_y)
create_keyhole("RIGHT", right_y)

# ---------------------------------------------------------
# Select the movable preview controller
# ---------------------------------------------------------

bpy.ops.object.select_all(action="DESELECT")
controller.select_set(True)
bpy.context.view_layer.objects.active = controller

print("KEYHOLE PREVIEW CREATED — NOTHING WAS CUT")
print("Bottom outer: 8 mm")
print("Bottom inner: 8 mm")
print("Top outer: 4 mm")
print("Top inner: 8 mm")
print(f"Keyhole spacing: {safe_spacing * 1000:.1f} mm")
print("Move with G then Y or Z.")
