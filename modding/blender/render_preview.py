"""
Render a turnaround of the Toy Chica blockout.

Uses Cycles on CPU so it runs on headless boxes with no GPU. The blockout is
tiny, so a handful of samples is plenty to check the silhouette.

    python3 render_preview.py
"""

import math
import os

import bpy  # noqa: I001 - must precede mathutils
from mathutils import Vector

import build_toychica_blockout as blockout

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOLUTION = (420, 640)
SAMPLES = 24

# (filename suffix, camera angle around Z in degrees). The character faces +X
# following Unreal's convention, so 0 degrees puts the camera dead in front.
VIEWS = [("front", 0), ("three_quarter", 40), ("side", 90)]


def setup_world():
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.06, 0.09, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    bpy.context.scene.world = world


def setup_lights():
    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", type="AREA"))
    key.data.energy = 900
    key.data.size = 4
    key.location = (4.0, -3.0, 3.4)
    bpy.context.scene.collection.objects.link(key)

    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", type="AREA"))
    fill.data.energy = 320
    fill.data.size = 6
    fill.location = (-3.5, -2.5, 2.0)
    bpy.context.scene.collection.objects.link(fill)

    for light in (key, fill):
        track = light.constraints.new("TRACK_TO")
        track.target = bpy.data.objects[blockout.MESH_NAME]
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"


def setup_camera():
    camera = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    camera.data.lens = 70
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera

    # Aim at the character's midpoint rather than its feet.
    target = bpy.data.objects.new("CamTarget", None)
    target.location = (0, 0, 0.95)
    bpy.context.scene.collection.objects.link(target)

    track = camera.constraints.new("TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    return camera


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"


def main():
    # Rebuild the character in this fresh session.
    blockout.clear_scene()
    armature = blockout.build_armature()
    mesh_obj, groups = blockout.build_character_mesh()
    blockout.bind(mesh_obj, armature, groups)

    setup_world()
    setup_lights()
    camera = setup_camera()
    setup_render()

    radius, height = 5.2, 1.35
    written = []
    for name, angle in VIEWS:
        theta = math.radians(angle)
        camera.location = Vector((radius * math.cos(theta),
                                  radius * math.sin(theta),
                                  height))
        path = os.path.join(OUT_DIR, f"preview_{name}.png")
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        written.append(path)

    for path in written:
        print("rendered:", path)


if __name__ == "__main__":
    main()
