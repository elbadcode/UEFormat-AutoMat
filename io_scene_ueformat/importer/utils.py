from collections.abc import Collection
from typing import cast
from os import scandir
from os.path import abspath, join, isfile, dirname,basename
from json import load
from math import *
import bpy
from bpy.types import PoseBone, bpy_prop_collection
from mathutils import Vector, Quaternion

def bytes_to_str(in_bytes: bytes) -> str:
    return in_bytes.rstrip(b"\x00").decode()

def first(target, expr, default=None):
    if not target:
        return None
    return next(filter(expr, target), default)

def make_axis_vector(vec_in: Vector) -> Vector:
    x, y, z = vec_in
    vec_out = Vector()
    if abs(x) > abs(y):
        vec_out.x = 1 if x >= 0 else -1 if abs(x) > abs(z) else 0
        vec_out.z = 1 if abs(z) >= abs(x) and z >= 0 else -1 if abs(z) >= abs(x) else 0
    elif abs(y) > abs(z):
        vec_out.y = 1 if y >= 0 else -1
    else:
        vec_out.z = 1 if z >= 0 else -1
    return vec_out

def get_case_insensitive(source: bpy_prop_collection, string: str) -> PoseBone | None:
    string = string.lower()
    for item in cast(Collection[PoseBone], source):
        if item.name.lower() == string:
            return item
    return None

def get_active_armature():
    obj = bpy.context.object
    if obj is None:
        return None
    if obj.type == "ARMATURE":
        return obj
    elif obj.type == "MESH":
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE":
                return modifier.object
    return None

def get_armature_mesh(obj):
    if obj.type == "ARMATURE":
        return next((child for child in obj.children if child.type == "MESH"), None)
    if obj.type == "MESH":
        return obj
    return None

def disable_constraints(armature: bpy.types.Object) -> list[bpy.types.Constraint]:
    constraints_muted = []
    for bone in armature.pose.bones:
        for constraint in bone.constraints:
            if not constraint.mute:
                constraint.mute = True
                constraints_muted.append(constraint)
    return constraints_muted

def bone_hierarchy_has_vertex_groups(bone, vertex_groups):
    return bone.name in vertex_groups or any(child.name in vertex_groups for child in bone.children_recursive)

def bone_has_parent(child, parent):
    return child == parent or parent in child.parent_recursive

def bone_roll(bone: bpy.types.EditBone, roll: float):
    if "orig_roll" not in bone:
        bone["orig_roll"] = bone.roll
    bone.roll = roll

def bone_tail(bone: bpy.types.EditBone, tail):
    if "orig_tail" not in bone:
        bone["orig_tail"] = bone.tail
    bone.tail = tail

def bone_head(bone: bpy.types.EditBone, head):
    if "orig_head" not in bone:
        bone["orig_head"] = bone.head
    bone.head = head

def bone_parent(child: bpy.types.EditBone, parent_to: bpy.types.EditBone):
    if child != parent_to:
        if child.parent and "orig_parent" not in child:
            child["orig_parent"] = child.parent.name
        child.parent = parent_to

def bone_swap_properties(all_bones: bpy.types.ArmatureEditBones, bone: bpy.types.EditBone):
    if "orig_roll" in bone:
        bone["orig_roll"], bone.roll = bone.roll, bone["orig_roll"]
    if "orig_tail" in bone:
        bone["orig_tail"], bone.tail = bone.tail.copy(), bone["orig_tail"]
    if "orig_head" in bone:
        bone["orig_head"], bone.head = bone.head.copy(), bone["orig_head"]
    if "orig_parent" in bone:
        current = bone.parent.name if bone.parent else ""
        bone.parent = all_bones.get(bone["orig_parent"])
        bone["orig_parent"] = current

def bone_swap_orig_parents(armature_obj: bpy.types.Object):
    original_mode = bpy.context.active_object.mode
    original_selected_object = bpy.context.active_object
    try:
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode="EDIT")
        for edit_bone in armature_obj.data.edit_bones:
            bone_swap_properties(armature_obj.data.edit_bones, edit_bone)
    finally:
        bpy.ops.object.mode_set(mode=original_mode)
        bpy.context.view_layer.objects.active = original_selected_object

def make_quat(rot):
    return Quaternion((rot[3], rot[0], rot[1], rot[2]))

def make_vector(vec):
    return Vector((vec[0], vec[1], vec[2]))

def has_vertex_weights(obj, vertex_group):
    return any(vertex_group.index in [g.group for g in v.groups] for v in obj.data.vertices)

def search_path_for_props(path, filter=None):
    return [
        file.path for file in scandir(path)
        if (filter is None or filter in file.name) and file.name.endswith(".json")
    ]

def search_path_for_textures(path, ext=".png"):
    images = {
        file.name[:file.name.rfind(".")]
        for file in scandir(path)
        if file.name.endswith((".png", ".jpeg", ".tga"))
    }
    return [f"{img}.{ext}" for img in images]

def match_names(material, path):
    textures = search_path_for_textures(dirname(path))
    if len(textures) == 0:
        textures = search_path_for_textures(join(dirname(path),"..","Texture"))
    if len(textures) == 0:
        textures = search_path_for_textures(join(dirname(path),"..","Textures"))
    if len(textures) == 0:
        return
    mat_textures = []
    for tex in textures:
        if basename(tex)[:tex.rfind(".")][tex.find("_"):tex.rfind("_")] in material.name:
            mat_textures.append(tex)
    apply_texture(material, mat_textures)

def asset_to_os(props_path, asset_path):
    if asset_path.startswith("Game"):
        asset_path = asset_path.replace("Game", "Content")
    return join(props_path[:props_path.find("Content")].replace("\\", "/"), asset_path[asset_path.find("Content/"):])

def parse_mat_props(prop):
    try:
        mat_prop = load(open(prop, "r", encoding="utf-8"))
        textures = []
        if isinstance(mat_prop, list):
            textureparams = mat_prop[0]["Properties"]["TextureParameterValues"]
            print(textureparams)
            for texp in textureparams:
                path = texp["ParameterValue"]["ObjectPath"]
                print(path)
                tex_path = f"{path[:path.rfind('.')]}.png"
                print(tex_path)
                if isfile(texture_path:=asset_to_os(abspath(prop), tex_path)):
                    textures.append(texture_path)
                    print(texture_path)
            print(textures)
            return textures
        elif isinstance(mat_prop, dict):
            for tex, path in mat_prop.get("Textures", {}).items():
                if not path.startswith("Engine"):
                    tex_path = f"{path[:path.rfind('.')]}.png"
                    if isfile(texture_path:=asset_to_os(abspath(prop), tex_path)):
                        textures.append(texture_path)
                        print(texture_path)
            print(textures)
            return textures
    except Exception as e:
        print(f"Error parsing mat_props: {e}")



def apply_texture(material, textures):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf.location = (0, 0)
    output.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Try to find and apply diffuse texture
    diff = next((tex for tex in textures if "_D" in tex or tex[:tex.rfind(".")].endswith("D")), None)
    if diff:
        dtexture = nodes.new(type="ShaderNodeTexImage")
        dtexture.image = bpy.data.images.load(diff)
        dtexture.image.alpha_mode = "CHANNEL_PACKED"
        dtexture.location = (-300, 0)
        links.new(dtexture.outputs["Color"], bsdf.inputs["Base Color"])

    # Try to find and apply normal texture
    norm = next((tex for tex in textures if "_N" in tex or tex[:tex.rfind(".")].endswith("N")), None)
    if norm:
        ntexture = nodes.new(type="ShaderNodeTexImage")
        ntexture.image = bpy.data.images.load(norm)
        ntexture.image.colorspace_settings.name = "Non-Color"
        ntexture.location = (-300, -300)
        normal_map = nodes.new(type="ShaderNodeNormalMap")
        normal_map.location = (-100, -300)
        links.new(ntexture.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])


def parse_sm_props(prop, obj = None):
    with open(prop, "r", encoding="utf-8") as f:
        props = load(f)

    props_path = abspath(prop)
    mat_dict = {}

    # Expecting the last entry to be the SkeletalMesh
    skelmesh = props[-1]
    if skelmesh.get("Type") != "SkeletalMesh":
        print(f"Unexpected type in {prop}")
        return

    materials = skelmesh.get("SkeletalMaterials", [])
    lod0_sections = skelmesh.get("LODModels", [{}])[0].get("Sections", [])

    for section in lod0_sections:
        mat_index = section.get("MaterialIndex")
        if mat_index is not None and mat_index < len(materials):
            mat = materials[mat_index]
            slot_name = mat.get("MaterialSlotName")
            mat_path = mat.get("Material", {}).get("ObjectPath")
            if slot_name and mat_path:
                mat_dict[slot_name] = mat_path

    # Convert material paths to .json files
    material_json_paths = [
        asset_to_os(props_path, f"{mat_path[:mat_path.rfind('.')]}.json")
        for mat_path in mat_dict.values()
    ]
    for mat_path in material_json_paths:
        mat_textures = []
        try:
            mat_textures = parse_mat_props(mat_path)
        except Exception as e:
            pass
        # mat_name = mat_path[mat_path.rfind("/") + 1 : mat_path.rfind(".")]
        mat_name = basename(mat_path).rsplit(".")[0]
        print(mat_name)
        if obj is None:
            obj = bpy.context.object
        print(obj)
        material = obj.data.materials.get(mat_name)
        if material is None:
            material = bpy.data.materials.new(name=mat_name)
            print(mat.name)
        # Ensure the material is assigned to the object
        if material.name not in [mat.name for mat in obj.data.materials]:
            obj.data.materials.append(material)
        if mat_textures is not None and len(mat_textures) > 0:
            apply_texture(material, mat_textures)

