import os

import bpy

from .color import ColorFactory


class Material:
    def __init__(self):
        """Initialize the Material object."""
        self.name = None
        self.diffuse_color = None
        self.textures = []
        self.material = None

    def set_data(self, diffuse_color, textures=[]):
        """Set the material data."""
        self.diffuse_color = diffuse_color
        self.textures = textures

    def create_or_replace(self, material_name):
        """Create or replace the material in Blender."""
        if not material_name:
            raise ValueError("material_name cannot be None")

        self.name = material_name
        self.material = bpy.data.materials.get(self.name)

        if self.material:
            # Check if the existing material parameters match
            if self._is_same_material():
                # Material is the same, skip
                return
            else:
                print(
                    f"Updating material {self.name}."
                )

        if not self.material:
            self.material = bpy.data.materials.new(self.name)

        if self.diffuse_color:
            self._set_diffuse_color()

        if len(self.textures) > 0:
            self._apply_textures()

    def _is_same_material(self):
        """Check if the existing material parameters match the new ones."""
        # Check diffuse color
        current_diffuse = self.material.diffuse_color[:3]  # Compare RGB values only
        new_diffuse = ColorFactory.from_hex(self.diffuse_color).to_normalized_tuple()[:3]

        if not self._compare_colors(current_diffuse, new_diffuse):
            return False

        # If the material doesn't use nodes, skip texture comparison
        if not self.material.use_nodes or not self.material.node_tree:
            # If textures are provided for a non-node material, assume it doesn't match
            if self.textures:
                return False
            # If no textures and diffuse color matches, return True
            return True

        # Material uses nodes, proceed to check textures
        existing_textures = [
            node for node in self.material.node_tree.nodes if node.type == "TEX_IMAGE"
        ]
        if len(existing_textures) != len(self.textures):
            return False

        for tex_node, new_texture in zip(existing_textures, self.textures):
            if tex_node.image.filepath != new_texture["Path"]:
                return False

        return True

    def _compare_colors(self, color1, color2, tolerance=1e-4):
        """Compare two colors with a tolerance for floating-point precision."""
        return all(abs(a - b) <= tolerance for a, b in zip(color1, color2))

    def _set_diffuse_color(self):
        """Set the base color of the material."""
        self.material.diffuse_color = ColorFactory.from_hex(
            self.diffuse_color
        ).to_normalized_tuple()

    def _apply_textures(self):
        """Apply textures to the material."""
        # Ensure material uses nodes
        if not self.material.use_nodes:
            self.material.use_nodes = True

        # Get the node tree and the principal BSDF node
        nodes = self.material.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")

        if not bsdf:
            bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")

        # Remove existing texture nodes if any
        texture_nodes = [node for node in nodes if node.type == "TEX_IMAGE"]
        for node in texture_nodes:
            nodes.remove(node)

        for texture in self.textures:
            tex_type = texture["Type"]
            tex_path = texture["Path"]

            # Check if the texture path exists
            if not os.path.exists(tex_path):
                print(f"Texture file not found: {tex_path}")
                continue

            # Create a new texture image node
            tex_image_node = nodes.new(type="ShaderNodeTexImage")
            tex_image_node.image = bpy.data.images.load(tex_path)

            # Link the texture node based on its type
            if tex_type in (
                PTextureType.Diffuse,
                PTextureType.PBR_Metallic,
            ):
                self.material.node_tree.links.new(
                    tex_image_node.outputs["Color"], bsdf.inputs["Base Color"]
                )
            else:
                print(f"Unsupported texture type: {tex_type}")
                continue

    @staticmethod
    def from_dict(dict):
        """Create a Material object from a dictionary."""
        material = Material()
        material.set_data(
            diffuse_color=dict.get("DiffuseColor"),
            textures=dict.get("Textures"),
        )
        return material


class PTextureType:
    Null = 0
    Bitmap = 1
    Diffuse = 1
    PBR_BaseColor = 1
    Bump = 2
    Opacity = 3
    Transparency = 3
    PBR_Subsurface = 10
    PBR_SubsurfaceScattering = 11
    PBR_SubsurfaceScatteringRadius = 12
    PBR_Metallic = 13
    PBR_Specular = 14
    PBR_SpecularTint = 15
    PBR_Roughness = 16
    PBR_Anisotropic = 17
    PBR_Anisotropic_Rotation = 18
    PBR_Sheen = 19
    PBR_SheenTint = 20
    PBR_Clearcoat = 21
    PBR_ClearcoatRoughness = 22
    PBR_OpacityIor = 23
    PBR_OpacityRoughness = 24
    PBR_Emission = 25
    PBR_AmbientOcclusion = 26
    PBR_Displacement = 28
    PBR_ClearcoatBump = 29
    PBR_Alpha = 30
    Emap = 86
