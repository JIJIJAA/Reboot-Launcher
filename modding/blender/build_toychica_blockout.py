"""
Toy Chica (FNaF) blockout for Fortnite S0-14 private servers.

Generates a low-poly proxy character rigged to a UE4-mannequin-compatible
skeleton, so the whole asset pipeline can be validated before any real art
is produced. The silhouette is recognisable, the topology is throwaway.

The point of this file is the SKELETON and the EXPORT SETTINGS. Those are the
parts that break a Fortnite skin, and they are the parts that are tedious to
get right by hand. Replace the geometry, keep everything else.

Run headless:
    python3 build_toychica_blockout.py

Outputs FBX (for Unreal) and glTF (for previewing anywhere) next to the script.
"""

import math
import os
import sys

import bpy  # noqa: I001 - must precede bmesh/mathutils; it registers Blender's module paths
import bmesh
from mathutils import Euler, Matrix, Vector

# Blender works in metres. Fortnite/Unreal work in centimetres, and the FBX
# exporter bridges that automatically, so we author in metres and quote every
# measurement in centimetres for sanity.
CM = 0.01

# Fortnite characters are all ~180cm and share one skeleton. Deviating from
# these proportions is what makes custom skins T-pose, stretch or explode
# during emotes, so the blockout deliberately sticks to mannequin metrics.
CHARACTER_HEIGHT_CM = 180.0

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
MESH_NAME = "SK_ToyChica_Blockout"
ARMATURE_NAME = "Armature"

# ---------------------------------------------------------------------------
# Skeleton
# ---------------------------------------------------------------------------
# UE4 mannequin bone names. Fortnite's Skeleton_Character asset derives from
# this hierarchy, so matching the names exactly is what makes retargeting work.
# Coordinates are (X forward, Y right, Z up) in centimetres.
#
# The core chain below is hand-written; twist, finger and IK bones are
# generated further down because they are formulaic and long. The mesh does
# not have to use all of them - the blockout's hands are mitts weighted to
# hand_l/hand_r - but the SKELETON must carry them or Fortnite's animations
# and weapon sockets have nothing to bind to.
_CORE_BONES = [
    # name,          parent,        head (x, y, z),      tail (x, y, z)
    ("root",         None,          (0, 0, 0),           (0, 0, 10)),
    ("pelvis",       "root",        (0, 0, 97),          (0, 0, 105)),
    ("spine_01",     "pelvis",      (0, 0, 105),         (0, 0, 117)),
    ("spine_02",     "spine_01",    (0, 0, 117),         (0, 0, 130)),
    ("spine_03",     "spine_02",    (0, 0, 130),         (0, 0, 143)),
    ("neck_01",      "spine_03",    (0, 0, 143),         (0, 0, 152)),
    ("head",         "neck_01",     (0, 0, 152),         (0, 0, 172)),

    ("clavicle_l",   "spine_03",    (0, 3, 141),         (0, 16, 141)),
    ("upperarm_l",   "clavicle_l",  (0, 16, 141),        (0, 42, 141)),
    ("lowerarm_l",   "upperarm_l",  (0, 42, 141),        (0, 66, 141)),
    ("hand_l",       "lowerarm_l",  (0, 66, 141),        (0, 78, 141)),

    ("clavicle_r",   "spine_03",    (0, -3, 141),        (0, -16, 141)),
    ("upperarm_r",   "clavicle_r",  (0, -16, 141),       (0, -42, 141)),
    ("lowerarm_r",   "upperarm_r",  (0, -42, 141),       (0, -66, 141)),
    ("hand_r",       "lowerarm_r",  (0, -66, 141),       (0, -78, 141)),

    ("thigh_l",      "pelvis",      (0, 9, 95),          (0, 9, 53)),
    ("calf_l",       "thigh_l",     (0, 9, 53),          (0, 9, 12)),
    ("foot_l",       "calf_l",      (0, 9, 12),          (10, 9, 3)),
    ("ball_l",       "foot_l",      (10, 9, 3),          (18, 9, 2)),

    ("thigh_r",      "pelvis",      (0, -9, 95),         (0, -9, 53)),
    ("calf_r",       "thigh_r",     (0, -9, 53),         (0, -9, 12)),
    ("foot_r",       "calf_r",      (0, -9, 12),         (10, -9, 3)),
    ("ball_r",       "foot_r",      (10, -9, 3),         (18, -9, 2)),
]


def _twist_bones():
    """Twist bones distribute forearm/thigh rotation so limbs do not candy-wrap.

    Fortnite's animations drive these, so a skeleton without them deforms
    badly on any emote that rotates the wrist or knee.
    """
    bones = []
    for side in (1, -1):
        suffix = "l" if side > 0 else "r"
        bones += [
            (f"upperarm_twist_01_{suffix}", f"upperarm_{suffix}",
             (0, 29 * side, 141), (0, 35 * side, 141)),
            (f"lowerarm_twist_01_{suffix}", f"lowerarm_{suffix}",
             (0, 54 * side, 141), (0, 60 * side, 141)),
            (f"thigh_twist_01_{suffix}", f"thigh_{suffix}",
             (0, 9 * side, 74), (0, 9 * side, 68)),
            (f"calf_twist_01_{suffix}", f"calf_{suffix}",
             (0, 9 * side, 32), (0, 9 * side, 26)),
        ]
    return bones


# Finger spread across the palm. In this T-pose the arms run along +/-Y, so
# fingers extend along Y and fan out along X. The thumb also drops in Z.
_FINGERS = [
    # name,    x offset, z offset, start y, joint lengths
    ("thumb",     4.5,  -1.5, 70, (4.5, 3.5, 3.0)),
    ("index",     3.5,   0.0, 77, (4.5, 3.0, 2.5)),
    ("middle",    1.2,   0.0, 77, (4.8, 3.2, 2.6)),
    ("ring",     -1.2,   0.0, 77, (4.4, 3.0, 2.4)),
    ("pinky",    -3.5,   0.0, 77, (3.8, 2.6, 2.2)),
]


def _finger_bones():
    """The five three-joint chains UE4 expects on each hand.

    Weapons are held via sockets on these bones. A mesh with mitts is fine;
    a skeleton without the chains is not.
    """
    bones = []
    for side in (1, -1):
        suffix = "l" if side > 0 else "r"
        for name, x_offset, z_offset, start_y, lengths in _FINGERS:
            parent = f"hand_{suffix}"
            cursor = start_y
            for index, length in enumerate(lengths, start=1):
                bone = f"{name}_0{index}_{suffix}"
                head = (x_offset, cursor * side, 141 + z_offset)
                cursor += length
                tail = (x_offset, cursor * side, 141 + z_offset)
                bones.append((bone, parent, head, tail))
                parent = bone
    return bones


def _ik_bones():
    """Animation-only helper bones. They deform nothing but must exist.

    Unreal's retargeting and the weapon-aiming rig both reference these by
    name; a missing ik_hand_gun in particular breaks weapon poses.
    """
    return [
        ("ik_foot_root", "root",         (0, 0, 0),      (10, 0, 0)),
        ("ik_foot_l",    "ik_foot_root", (0, 9, 12),     (10, 9, 12)),
        ("ik_foot_r",    "ik_foot_root", (0, -9, 12),    (10, -9, 12)),
        ("ik_hand_root", "root",         (0, 0, 0),      (10, 0, 0)),
        # ik_hand_gun follows the right hand; both ik_hand_l/r hang off it.
        ("ik_hand_gun",  "ik_hand_root", (0, -78, 141),  (10, -78, 141)),
        ("ik_hand_l",    "ik_hand_gun",  (0, 78, 141),   (10, 78, 141)),
        ("ik_hand_r",    "ik_hand_gun",  (0, -78, 141),  (10, -78, 141)),
    ]


BONES = _CORE_BONES + _twist_bones() + _finger_bones() + _ik_bones()

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
# One material slot per Toy Chica colour region. In Unreal these become the
# material slots of the skeletal mesh, so the names are what an artist will
# later bind real materials to. Keep the order stable: slot indices are
# referenced by the geometry below.
MATERIALS = [
    ("M_ToyChica_Body",    (0.98, 0.83, 0.22, 1.0)),  # 0 yellow plastic
    ("M_ToyChica_Beak",    (0.96, 0.55, 0.13, 1.0)),  # 1 orange beak + feet
    ("M_ToyChica_Bib",     (0.95, 0.95, 0.93, 1.0)),  # 2 white "LET'S PARTY" bib
    ("M_ToyChica_Briefs",  (0.93, 0.36, 0.62, 1.0)),  # 3 pink briefs + cheeks
    ("M_ToyChica_EyeWhite",(1.00, 1.00, 1.00, 1.0)),  # 4 sclera
    ("M_ToyChica_EyeIris", (0.16, 0.44, 0.85, 1.0)),  # 5 blue iris
]

MAT_BODY, MAT_BEAK, MAT_BIB, MAT_BRIEFS, MAT_EYE_W, MAT_EYE_I = range(6)


def clear_scene():
    """Wipe the default startup scene so repeated runs stay deterministic."""
    for collection in (bpy.data.objects, bpy.data.meshes,
                       bpy.data.armatures, bpy.data.materials):
        for item in list(collection):
            collection.remove(item)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _tag(geom, material_index, group):
    """Record which bone and material every new face belongs to.

    Returns the vertices so the caller can register them against a vertex
    group. Rigid skinning (one bone per part) is all a blockout needs.
    """
    verts = set()
    for face in geom.get("geom", []):
        if isinstance(face, bmesh.types.BMFace):
            face.material_index = material_index
            for vert in face.verts:
                verts.add(vert)
    return verts


def add_sphere(bm, center_cm, radius_cm, material_index, scale=(1, 1, 1),
               segments=16, rings=8):
    kwargs = dict(u_segments=segments, v_segments=rings)
    # The keyword was renamed between Blender versions; support both.
    try:
        result = bmesh.ops.create_uvsphere(bm, radius=radius_cm * CM, **kwargs)
    except TypeError:
        result = bmesh.ops.create_uvsphere(bm, diameter=radius_cm * CM, **kwargs)

    verts = [v for v in result["verts"]]
    matrix = (Matrix.Translation(Vector(center_cm) * CM)
              @ Matrix.Diagonal(Vector(scale)).to_4x4())
    bmesh.ops.transform(bm, matrix=matrix, verts=verts)
    for vert in verts:
        for face in vert.link_faces:
            face.material_index = material_index
    return verts


def add_box(bm, center_cm, size_cm, material_index, rotation=(0, 0, 0)):
    result = bmesh.ops.create_cube(bm, size=1.0)
    verts = [v for v in result["verts"]]
    matrix = (Matrix.Translation(Vector(center_cm) * CM)
              @ Euler(rotation).to_matrix().to_4x4()
              @ Matrix.Diagonal(Vector(size_cm) * CM).to_4x4())
    bmesh.ops.transform(bm, matrix=matrix, verts=verts)
    for vert in verts:
        for face in vert.link_faces:
            face.material_index = material_index
    return verts


def add_capsule(bm, start_cm, end_cm, radius_cm, material_index, segments=12):
    """A tapered cylinder spanning two points; used for limbs."""
    start = Vector(start_cm) * CM
    end = Vector(end_cm) * CM
    axis = end - start
    length = axis.length

    result = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segments,
        radius1=radius_cm * CM, radius2=radius_cm * CM * 0.85, depth=length,
    )
    verts = [v for v in result["verts"]]

    rotation = Vector((0, 0, 1)).rotation_difference(axis.normalized()).to_matrix().to_4x4()
    matrix = Matrix.Translation(start + axis * 0.5) @ rotation
    bmesh.ops.transform(bm, matrix=matrix, verts=verts)
    for vert in verts:
        for face in vert.link_faces:
            face.material_index = material_index
    return verts


def add_cone(bm, base_cm, height_cm, radius_cm, material_index, rotation=(0, 0, 0)):
    result = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=8,
        radius1=radius_cm * CM, radius2=0.0, depth=height_cm * CM,
    )
    verts = [v for v in result["verts"]]
    matrix = (Matrix.Translation(Vector(base_cm) * CM)
              @ Euler(rotation).to_matrix().to_4x4())
    bmesh.ops.transform(bm, matrix=matrix, verts=verts)
    for vert in verts:
        for face in vert.link_faces:
            face.material_index = material_index
    return verts


# ---------------------------------------------------------------------------
# Character construction
# ---------------------------------------------------------------------------

def build_character_mesh():
    """Build every body part, remembering which bone drives each one.

    Returns the mesh object and a {bone_name: [vertex_index, ...]} map.
    """
    bm = bmesh.new()
    # bone -> list of BMVert, resolved to indices once the mesh is finalised.
    groups = {}

    def part(bone, verts):
        groups.setdefault(bone, []).extend(verts)

    # --- Head ------------------------------------------------------------
    # Toy Chica's head is a rounded plastic shell. Kept deliberately close to
    # mannequin head size: an oversized head clips through Fortnite emotes.
    part("head", add_sphere(bm, (0, 0, 161), 14.5, MAT_BODY, scale=(1.0, 1.05, 1.0)))

    # Beak. Two wedges, upper and lower, pushed forward along +X. It has to
    # over-protrude to read at all from the front, which is the angle players
    # see most in the lobby.
    part("head", add_box(bm, (13, 0, 158.5), (16, 15, 6), MAT_BEAK))
    part("head", add_box(bm, (12, 0, 153), (14, 13, 4), MAT_BEAK))

    # Eyes: sclera plus iris, set wide and high like the Toy models.
    for side in (1, -1):
        part("head", add_sphere(bm, (8, 6 * side, 166), 5.0, MAT_EYE_W, rings=8))
        part("head", add_sphere(bm, (12, 6 * side, 166), 2.4, MAT_EYE_I, rings=6))
        # Rosy cheeks, the most recognisable Toy-series detail. Pushed wide so
        # they stay visible in silhouette instead of hiding behind the beak.
        part("head", add_sphere(bm, (7, 12 * side, 156), 3.6, MAT_BRIEFS,
                                scale=(0.6, 1.0, 1.0), rings=6))

    # Three head feathers, fanned backwards.
    for index, offset in enumerate((-6, 0, 6)):
        part("head", add_cone(bm, (-2, offset, 176), 12, 3.0, MAT_BEAK,
                              rotation=(math.radians(-18), 0, 0)))

    # --- Torso -----------------------------------------------------------
    # Overlapping spheres rather than stacked ones: two tangent spheres read
    # as a snowman, which is the classic blockout failure for round characters.
    part("spine_03", add_sphere(bm, (0, 0, 137), 15.5, MAT_BODY,
                                scale=(0.82, 1.0, 0.92)))
    part("spine_02", add_sphere(bm, (0, 0, 126), 15.0, MAT_BODY,
                                scale=(0.85, 1.05, 0.95)))
    # Toy Chica's rounded belly sits low and slightly forward.
    part("spine_01", add_sphere(bm, (1.5, 0, 114), 14.5, MAT_BODY,
                                scale=(0.88, 1.02, 1.0)))

    # The bib. A flat slab on the chest; the "LET'S PARTY!" text belongs in
    # the texture, not the geometry.
    part("spine_02", add_box(bm, (11, 0, 130), (3, 23, 26), MAT_BIB))

    # Pink briefs at the hips.
    part("pelvis", add_box(bm, (0, 0, 99), (19, 22, 13), MAT_BRIEFS))

    # --- Arms ------------------------------------------------------------
    for side, suffix in ((1, "l"), (-1, "r")):
        part(f"upperarm_{suffix}",
             add_capsule(bm, (0, 16 * side, 141), (0, 42 * side, 141), 5.5, MAT_BODY))
        part(f"lowerarm_{suffix}",
             add_capsule(bm, (0, 42 * side, 141), (0, 66 * side, 141), 4.6, MAT_BODY))
        # Four-fingered mitts, in keeping with the animatronic look.
        part(f"hand_{suffix}",
             add_box(bm, (0, 72 * side, 141), (5, 12, 9), MAT_BODY))

    # --- Legs ------------------------------------------------------------
    for side, suffix in ((1, "l"), (-1, "r")):
        part(f"thigh_{suffix}",
             add_capsule(bm, (0, 9 * side, 95), (0, 9 * side, 53), 8.0, MAT_BODY))
        part(f"calf_{suffix}",
             add_capsule(bm, (0, 9 * side, 53), (0, 9 * side, 12), 6.0, MAT_BEAK))
        # Three-toed bird feet.
        part(f"foot_{suffix}", add_box(bm, (5, 9 * side, 5), (22, 12, 7), MAT_BEAK))
        for toe in (-4.5, 0, 4.5):
            part(f"ball_{suffix}",
                 add_cone(bm, (17, 9 * side + toe, 4), 9, 2.2, MAT_BEAK,
                          rotation=(0, math.radians(90), 0)))

    # Finalise into a real mesh datablock.
    mesh = bpy.data.meshes.new(MESH_NAME)
    bm.verts.index_update()

    # Resolve BMVerts to stable indices before the bmesh is freed.
    index_groups = {bone: [v.index for v in verts] for bone, verts in groups.items()}
    bm.to_mesh(mesh)
    bm.free()

    for name, colour in MATERIALS:
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        material.diffuse_color = colour
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = colour
        mesh.materials.append(material)

    mesh.shade_smooth()

    obj = bpy.data.objects.new(MESH_NAME, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj, index_groups


def build_armature():
    armature_data = bpy.data.armatures.new(ARMATURE_NAME)
    armature = bpy.data.objects.new(ARMATURE_NAME, armature_data)
    bpy.context.scene.collection.objects.link(armature)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")

    for name, parent, head, tail in BONES:
        bone = armature_data.edit_bones.new(name)
        bone.head = Vector(head) * CM
        bone.tail = Vector(tail) * CM
        if parent:
            bone.parent = armature_data.edit_bones[parent]
            # Do NOT auto-connect: Fortnite bones have offsets between joints
            # and connecting them silently moves the heads.
            bone.use_connect = False

    bpy.ops.object.mode_set(mode="OBJECT")
    return armature


def bind(mesh_obj, armature, index_groups):
    """Rigid-bind each body part to its driving bone."""
    for bone, indices in index_groups.items():
        group = mesh_obj.vertex_groups.new(name=bone)
        group.add(indices, 1.0, "REPLACE")

    modifier = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    modifier.object = armature
    mesh_obj.parent = armature


def export(armature, mesh_obj):
    for obj in bpy.context.scene.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = armature

    fbx_path = os.path.join(OUT_DIR, "SK_ToyChica_Blockout.fbx")
    # These flags are the ones that matter for Unreal. Getting add_leaf_bones
    # or the axis conversion wrong produces a mesh that imports rotated or
    # with phantom bones that break retargeting.
    bpy.ops.export_scene.fbx(
        filepath=fbx_path,
        use_selection=True,
        apply_scale_options="FBX_SCALE_NONE",
        object_types={"ARMATURE", "MESH"},
        # Export every bone, not just weighted ones. IK and finger bones carry
        # no weights, and filtering by "deform" would silently drop them - the
        # skeleton has to be complete even where the blockout mesh is not.
        use_armature_deform_only=False,
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        bake_anim=False,
        mesh_smooth_type="FACE",
        axis_forward="-Z",
        axis_up="Y",
    )

    gltf_path = os.path.join(OUT_DIR, "SK_ToyChica_Blockout.glb")
    bpy.ops.export_scene.gltf(filepath=gltf_path, export_format="GLB",
                              use_selection=True)
    return fbx_path, gltf_path


def main():
    clear_scene()
    armature = build_armature()
    mesh_obj, index_groups = build_character_mesh()
    bind(mesh_obj, armature, index_groups)
    fbx_path, gltf_path = export(armature, mesh_obj)

    mesh = mesh_obj.data
    height = max(v.co.z for v in mesh.vertices) / CM
    print("=" * 62)
    print(f"  vertices      : {len(mesh.vertices)}")
    print(f"  polygons      : {len(mesh.polygons)}")
    print(f"  material slots: {len(mesh.materials)}")
    print(f"  bones         : {len(armature.data.bones)}")
    print(f"  vertex groups : {len(mesh_obj.vertex_groups)}")
    print(f"  height        : {height:.1f} cm (target {CHARACTER_HEIGHT_CM:.0f})")
    print(f"  FBX  -> {fbx_path}")
    print(f"  glTF -> {gltf_path}")
    print("=" * 62)


if __name__ == "__main__":
    main()
