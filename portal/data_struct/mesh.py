import bpy

from .color import ColorFactory
from .material import Material


class Mesh:
    def __init__(self):
        """Initialize the Mesh object without requiring object name or collection name."""
        self.vertices = []
        self.faces = []
        self.vertex_colors = []
        self.uvs = []
        self.mesh_data = None
        self.object_name = None

    def set_data(self, vertices, faces, uvs=None, vertex_colors=None):
        """Set the mesh data."""
        self.vertices = vertices
        self.faces = faces
        self.uvs = uvs or []
        self.vertex_colors = vertex_colors or []

    def create_or_replace(self, object_name, layer_path=None):
        """Create or replace the mesh in Blender."""
        self._validate_data()
        self.object_name = object_name

        existing_obj = bpy.data.objects.get(object_name)

        if existing_obj and existing_obj.type == "MESH":
            self._replace_mesh(existing_obj)
        else:
            self._create_new_mesh(object_name, layer_path)

        if self.vertex_colors:
            self._apply_vertex_colors()

        if self.uvs:
            self._apply_uv_map()

    def apply_material(self, material):
        """Apply material to the mesh object."""
        obj = bpy.data.objects.get(self.object_name)

        if not obj:
            raise ValueError(f"Object {self.object_name} not found.")

        if isinstance(material, str):
            mat = bpy.data.materials.get(material)
            if not mat:
                raise ValueError(f"Material {material} not found.")
        elif isinstance(material, Material):
            material.create_or_replace(material.name)
            mat = material.material
        else:
            raise ValueError("Material must be a string or Material object.")

        # Apply the material to the object
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

    def _apply_vertex_colors(self):
        """Apply vertex colors to the mesh."""
        if not self.mesh_data.vertex_colors:
            self.mesh_data.vertex_colors.new()

        color_layer = self.mesh_data.vertex_colors.active
        color_dict = {i: col for i, col in enumerate(self.vertex_colors)}

        for poly in self.mesh_data.polygons:
            for idx in poly.loop_indices:
                loop = self.mesh_data.loops[idx]
                vertex_index = loop.vertex_index
                if vertex_index in color_dict:
                    color_layer.data[idx].color = color_dict[vertex_index]

    def _apply_uv_map(self):
        """Apply UV map to the mesh."""
        if not self.mesh_data.uv_layers:
            self.mesh_data.uv_layers.new()

        uv_layer = self.mesh_data.uv_layers.active
        uv_dict = {i: uv for i, uv in enumerate(self.uvs)}

        for poly in self.mesh_data.polygons:
            for idx in poly.loop_indices:
                loop = self.mesh_data.loops[idx]
                vertex_index = loop.vertex_index
                if vertex_index in uv_dict:
                    uv_layer.data[idx].uv = uv_dict[vertex_index]

    def _create_new_mesh(self, object_name, layer_path=None):
        """Create a new mesh in Blender."""
        self.mesh_data = bpy.data.meshes.new(f"{object_name}_mesh")
        self.mesh_data.from_pydata(self.vertices, [], self.faces)
        self.mesh_data.update()

        new_object = bpy.data.objects.new(object_name, self.mesh_data)
        self._link_object_to_collection(new_object, layer_path)

    def _replace_mesh(self, existing_obj):
        """Replace the existing mesh data in the Blender object."""
        old_mesh = existing_obj.data
        self.mesh_data = bpy.data.meshes.new(f"{existing_obj.name}_mesh")
        self.mesh_data.from_pydata(self.vertices, [], self.faces)
        self.mesh_data.update()

        existing_obj.data = self.mesh_data
        bpy.data.meshes.remove(old_mesh)

    def _validate_data(self):
        """Ensure that the mesh data is valid before creating or replacing."""
        if not self.vertices or not self.faces:
            raise ValueError("Mesh data must include vertices and faces.")

    def _link_object_to_collection(self, obj, layer_path=None):
        """Link the object to the appropriate Blender collection, handling nested layers."""
        if layer_path:
            layer_names = layer_path.split("::")
            parent_collection = None

            for layer in layer_names:
                # Ensure unique layer names by appending suffix if duplicate exists
                collection_name = layer
                suffix = 1
                while bpy.data.collections.get(collection_name):
                    collection_name = f"{layer}_{suffix}"
                    suffix += 1

                # Create or get the collection
                collection = bpy.data.collections.get(collection_name)
                if not collection:
                    collection = bpy.data.collections.new(collection_name)
                    if parent_collection:
                        parent_collection.children.link(collection)
                    else:
                        bpy.context.scene.collection.children.link(collection)

                # Set parent for the next nested layer
                parent_collection = collection

            # Link the object to the final collection in the nested structure
            parent_collection.objects.link(obj)
        else:
            bpy.context.collection.objects.link(obj)

    @staticmethod
    def from_dict(dict):
        """Create a Mesh object from json dictionary."""
        vertices = [(v["X"], v["Y"], v["Z"]) for v in dict["Vertices"]]
        faces = [tuple(face_list) for face_list in dict["Faces"]]
        uvs = [(uv["X"], uv["Y"]) for uv in dict.get("UVs", [])]
        color_hexs = dict.get("VertexColors")

        vertex_colors = None
        if color_hexs and len(color_hexs) == len(vertices):
            vertex_colors = [
                ColorFactory.from_hex(hex_str).to_normalized_tuple() for hex_str in color_hexs
            ]

        mesh = Mesh()
        mesh.set_data(vertices, faces, uvs, vertex_colors)
        return mesh
