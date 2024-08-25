import gzip
import io
import json

import bpy  # type: ignore


class BinaryHandler:
    @staticmethod
    def decompress_if_gzip(data: bytes) -> bytes:
        if data[:2] == b"\x1f\x8b":
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
                try:
                    return gz.read()
                except OSError:
                    return data
        return data


class DataHandler:
    @staticmethod
    def handle_str_data(data, data_type):
        try:
            if data_type == "Text":
                print(f"Received message: {data}")
            elif data_type == "Mesh":
                message_dics = json.loads(data)
                for i, item in enumerate(message_dics):
                    vertices, faces, uvs = MeshHandler.deserialize_mesh(item)
                    MeshHandler.create_or_replace_mesh(f"object_{i}", vertices, faces)
        except json.JSONDecodeError:
            print(f"Unsupported data: {data}")


class MeshHandler:
    @staticmethod
    def deserialize_mesh(data):
        vertices = [(v["X"], v["Y"], v["Z"]) for v in data["Vertices"]]
        faces = [tuple(face_list) for face_list in data["Faces"]]
        uvs = [(uv["X"], uv["Y"]) for uv in data["UVs"]]
        return vertices, faces, uvs

    @staticmethod
    def create_or_replace_mesh(object_name, vertices, faces):
        obj = bpy.data.objects.get(object_name)
        new_mesh_data = bpy.data.meshes.new(f"{object_name}_mesh")
        new_mesh_data.from_pydata(vertices, [], faces)
        new_mesh_data.update()

        if obj and obj.type == "MESH":
            old_mesh = obj.data
            obj.data = new_mesh_data
            bpy.data.meshes.remove(old_mesh)
        else:
            new_object = bpy.data.objects.new(object_name, new_mesh_data)
            bpy.context.collection.objects.link(new_object)

        new_mesh_data.update()

        new_mesh_data.update()
        new_mesh_data.update()
