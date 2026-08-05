# code to actually cut

import bpy
import bmesh
from mathutils import Vector

PREVIEW_NAME = "CUT_PREVIEW"

car = bpy.context.active_object
preview = bpy.data.objects.get(PREVIEW_NAME)

if car is None or car.type != "MESH":
    raise Exception("Select the car mesh before approving the cut.")

if car.name == PREVIEW_NAME:
    raise Exception("You selected CUT_PREVIEW. Select the car instead.")

if preview is None:
    raise Exception("CUT_PREVIEW was not found. Run the preview code first.")

if bpy.context.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

# Confirm that this is the original target car
target_name = preview.get("target_car")

if target_name and car.name != target_name:
    raise Exception(
        f"This preview was created for '{target_name}', "
        f"but you selected '{car.name}'."
    )

# Create a full hidden backup
backup = car.copy()
backup.data = car.data.copy()
backup.animation_data_clear()
backup.name = car.name + "_BACKUP_BEFORE_CUT"

bpy.context.collection.objects.link(backup)

backup.hide_set(True)
backup.hide_render = True

# Preview position determines the world-space cutting plane
plane_point_world = preview.matrix_world.translation.copy()
plane_normal_world = Vector((1.0, 0.0, 0.0))

# Convert cutting plane into the car's local coordinates
plane_point_local = car.matrix_world.inverted() @ plane_point_world

plane_normal_local = (
    car.matrix_world.to_3x3().transposed()
    @ plane_normal_world
).normalized()

# Edit the mesh safely with BMesh
mesh = car.data
bm = bmesh.new()
bm.from_mesh(mesh)

geometry = (
    list(bm.verts) +
    list(bm.edges) +
    list(bm.faces)
)

result = bmesh.ops.bisect_plane(
    bm,
    geom=geometry,
    plane_co=plane_point_local,
    plane_no=plane_normal_local,
    clear_inner=True,
    clear_outer=False
)

# Fill the open cutting boundary
cut_edges = [
    element
    for element in result.get("geom_cut", [])
    if isinstance(element, bmesh.types.BMEdge)
]

if cut_edges:
    try:
        bmesh.ops.edgenet_fill(
            bm,
            edges=cut_edges
        )
    except Exception:
        print("The cut was applied, but Blender could not automatically fill every opening.")

bm.normal_update()
bm.to_mesh(mesh)
bm.free()

mesh.update()

car.name = car.name + "_REAR_CUT"

# Delete only the preview plate
bpy.data.objects.remove(preview, do_unlink=True)

# Select the finished car
bpy.ops.object.select_all(action="DESELECT")
car.select_set(True)
bpy.context.view_layer.objects.active = car

print("CUT APPROVED")
print("The right/rear side was kept.")
print("Hidden backup created:", backup.name)
