from pathlib import Path
from typing import Generic, TypeVar

from bpy.props import *
from bpy.types import Operator, OperatorFileListElement
from bpy_extras.io_utils import ImportHelper

from .panels import UEFORMAT_PT_Panel
from ..importer.logic import UEFormatImport
from ..options import UEAnimOptions, UEFormatOptions, UEModelOptions, UEPoseOptions
from ..typing import UFormatContext

T = TypeVar("T", bound=UEFormatOptions)


class UFImportBase(Operator, ImportHelper, Generic[T]):
    bl_context = "scene"
    files: CollectionProperty(
        type=OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"},
    )
    directory: StringProperty(subtype="DIR_PATH")

    options_class: type[T]

    def execute(self, context: UFormatContext) -> set[str]:
        options = self.options_class.from_settings(context.scene.uf_settings)

        directory = Path(self.directory)
        for file in self.files:
            file: OperatorFileListElement
            UEFormatImport(options).import_file(directory / file.name)

        return {"FINISHED"}


class UFImportUEModel(UFImportBase):
    bl_idname = "uf.import_uemodel"
    bl_label = "Import Model"

    filename_ext = ".uemodel"
    filter_glob: StringProperty(default="*.uemodel", options={"HIDDEN"}, maxlen=255)

    options_class = UEModelOptions

    def draw(self, context: UFormatContext) -> None:
        UEFORMAT_PT_Panel.draw_general_options(self, context.scene.uf_settings)
        UEFORMAT_PT_Panel.draw_model_options(
            self,
            context.scene.uf_settings,
            import_menu=True,
        )


class UFImportUEAnim(UFImportBase):
    bl_idname = "uf.import_ueanim"
    bl_label = "Import Animation"

    filename_ext = ".ueanim"
    filter_glob: StringProperty(default="*.ueanim", options={"HIDDEN"}, maxlen=255)

    options_class = UEAnimOptions

    def draw(self, context: UFormatContext) -> None:
        UEFORMAT_PT_Panel.draw_general_options(self, context.scene.uf_settings)
        UEFORMAT_PT_Panel.draw_anim_options(
            self,
            context.scene.uf_settings,
            import_menu=True,
        )


class UFImportUEPose(UFImportBase):
    bl_idname = "uf.import_uepose"
    bl_label = "Import Pose"

    filename_ext = ".uepose"
    filter_glob: StringProperty(default="*.uepose", options={"HIDDEN"}, maxlen=255)

    options_class = UEPoseOptions

    def draw(self, context: UFormatContext) -> None:
        UEFORMAT_PT_Panel.draw_general_options(self, context.scene.uf_settings)
        UEFORMAT_PT_Panel.draw_pose_options(
            self,
            context.scene.uf_settings,
            import_menu=True,
        )




    # def apply_mat_textures(self, context):
    #     # Create a new material if the object doesn't have one
    #     if not obj.data.materials:
    #         material = bpy.data.materials.new(name="mat")
    #         obj.data.materials.append(material)


    #     for material in obj.data.materials:
    #         material.use_nodes = True
    #         nodes = material.node_tree.nodes
    #         for node in nodes:
    #             nodes.remove(node)
    #         bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    #         texture = nodes.new(type='ShaderNodeTexImage')
    #         if material.name == "MI_"+basename(texture_path).replace("_D","").replace("T_","").rsplit(".")[0]:


    #             # Enable 'Use Nodes'
    #             material.use_nodes = True
    #             nodes = material.node_tree.nodes

    #             # Clear default nodes
    #             for node in nodes:
    #                 nodes.remove(node)

    #             # Create nodes
    #             bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    #             texture = nodes.new(type='ShaderNodeTexImage')
    #             try:
    #                 normtexture = nodes.new(type='ShaderNodeTexImage')
    #                 normtexture.image = bpy.data.images.load(str(texture_path).replace("_D","_N"))
    #                 normtexture.image.colorspace_settings.name = 'Non-Color'
    #             except Exception as e:
    #                 pass
    #             texture.image = bpy.data.images.load(texture_path)
    #             texture.image.alpha_mode ='PREMUL' if transparent else 'CHANNEL_PACKED'
    #             output = nodes.new(type='ShaderNodeOutputMaterial')
    #             # Position nodes
    #             texture.location = (-300, 0)
    #             bsdf.location = (0, 0)
    #             output.location = (300, 0)

    #             # Link nodes
    #             links = material.node_tree.links
    #             links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    #             links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

