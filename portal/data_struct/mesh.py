import bpy

from ..data_struct.color import ColorFactory


class Mesh:
    def __init__(self):
        """Initialize the Mesh object without requiring object name or collection name."""
        self.vertices = []
        self.faces = []
        self.vertex_colors = []
        self.material = None
        self.mesh_data = None

    def set_data(self, vertices, faces, vertex_colors=None, material=None):
        """Set the mesh data."""
        self.vertices = vertices
        self.faces = faces
        self.vertex_colors = vertex_colors or []
        self.material = material

    def create_or_replace(self, object_name, collection_name=None):
        """Create or replace the mesh in Blender."""
        self._validate_data()

        existing_obj = bpy.data.objects.get(object_name)

        if existing_obj and existing_obj.type == "MESH":
            self._replace_mesh(existing_obj)
        else:
            self._create_new_mesh(object_name, collection_name)

        if self.vertex_colors:
            self.apply_vertex_colors()

        if self.material:
            self.apply_material(object_name)

    def apply_vertex_colors(self):
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

    def apply_material(self, object_name):
        """Apply material to the mesh object."""
        mat = bpy.data.materials.get(self.material)
        if mat:
            obj = bpy.data.objects.get(object_name)
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat
        else:
            print(f"Material {self.material} not found.")

    def _create_new_mesh(self, object_name, collection_name=None):
        """Create a new mesh in Blender."""
        self.mesh_data = bpy.data.meshes.new(f"{object_name}_mesh")
        self.mesh_data.from_pydata(self.vertices, [], self.faces)
        self.mesh_data.update()

        new_object = bpy.data.objects.new(object_name, self.mesh_data)
        self._link_object_to_collection(new_object, collection_name)

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

    def _link_object_to_collection(self, obj, collection_name=None):
        """Link the object to the appropriate Blender collection."""
        if collection_name:
            collection = bpy.data.collections.get(collection_name)
            if not collection:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)
            collection.objects.link(obj)
        else:
            bpy.context.collection.objects.link(obj)

    @staticmethod
    def from_dict(dict):
        """Create a Mesh object from json dictionary."""
        vertices = [(v["X"], v["Y"], v["Z"]) for v in dict["Vertices"]]
        faces = [tuple(face_list) for face_list in dict["Faces"]]
        color_hexs = dict.get("VertexColors")

        vertex_colors = None
        if color_hexs and len(color_hexs) == len(vertices):
            vertex_colors = [
                ColorFactory.from_hex(hex_str).to_normalized_tuple() for hex_str in color_hexs
            ]

        material = dict.get("Material")
        mesh = Mesh()
        mesh.set_data(vertices, faces, vertex_colors, material)
        return mesh
