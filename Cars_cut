# Code the preview where the car's cut is going to be:
# Change line 39 to move the cur arround

import bpy
from mathutils import Vector

PREVIEW_NAME = "CUT_PREVIEW"

car = bpy.context.active_object

if car is None or car.type != "MESH":
    raise Exception("Select the car mesh before running this code.")

if bpy.context.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

# Remove an older preview, if one exists
old_preview = bpy.data.objects.get(PREVIEW_NAME)

if old_preview:
    bpy.data.objects.remove(old_preview, do_unlink=True)

# Get the car's world-space bounding box
corners = [car.matrix_world @ Vector(corner) for corner in car.bound_box]

min_x = min(point.x for point in corners)
max_x = max(point.x for point in corners)

min_y = min(point.y for point in corners)
max_y = max(point.y for point in corners)

min_z = min(point.z for point in corners)
max_z = max(point.z for point in corners)

car_length = max_x - min_x
car_depth = max_y - min_y
car_height = max_z - min_z

# Initial position: approximately 75% along the car
cut_x = min_x + car_length * 0.85

center_y = (min_y + max_y) / 2
center_z = (min_z + max_z) / 2

# Preview thickness: 1 mm
preview_thickness = 0.001

# Create the visible cutting plate
bpy.ops.mesh.primitive_cube_add(
    location=(cut_x, center_y, center_z)
)

preview = bpy.context.active_object
preview.name = PREVIEW_NAME

preview.dimensions = (
    preview_thickness,
    max(car_depth * 1.4, 0.02),
    max(car_height * 1.4, 0.02)
)

bpy.ops.object.transform_apply(
    location=False,
    rotation=False,
    scale=True
)

# Make the preview easy to see
preview.display_type = "WIRE"
preview.show_in_front = True
preview.color = (1.0, 0.05, 0.05, 1.0)

# Store which car this preview belongs to
preview["target_car"] = car.name

# Select only the preview
bpy.ops.object.select_all(action="DESELECT")
preview.select_set(True)
bpy.context.view_layer.objects.active = preview

print("CUT PREVIEW CREATED")
print("Move it with G, then X.")
print("The car has not been modified.")
