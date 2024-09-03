import gzip
import io
import json
import struct
from typing import Tuple

import bpy  # type: ignore

from .data_struct.packet import PacketHeader
from .utils.color import ColorFactory


class BinaryHandler:
    @staticmethod
    def parse_header(data: bytes) -> PacketHeader:
        # see https://docs.python.org/3/library/struct.html#format-characters
        is_compressed, is_encrypted, checksum, size = struct.unpack(
            "??Hi", data[: PacketHeader.get_expected_size()]
        )
        return PacketHeader(is_encrypted, is_compressed, size, checksum)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        if not data[:2] == b"\x1f\x8b":
            raise ValueError("Data is not in gzip format.")
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
            try:
                return gz.read()
            except OSError:
                return data


class StringHandler:
    @staticmethod
    def handle_str_data(payload, data_type):
        if payload is None:
            return
        try:
            if data_type == "Text":
                print(f"Received message: {payload}")
            elif data_type == "Mesh":
                message_dics = json.loads(payload)
                for i, item in enumerate(message_dics):
                    data, metadata = StringHandler.unpack_packet(item)
                    vertices, faces, colors = MeshHandler.deserialize_mesh(data)
                    object_name = StringHandler.try_get_name(metadata)
                    material = StringHandler.try_get_material(metadata)
                    MeshHandler.create_or_replace_mesh(
                        f"{object_name}_{i}", vertices, faces, colors, material
                    )
        except json.JSONDecodeError:
            raise ValueError(f"Unsupported data: {payload}")

    def unpack_packet(packet: str) -> Tuple[str, str]:
        try:
            return packet["Data"], packet["Metadata"]
        except json.JSONDecodeError:
            raise ValueError(f"Unsupported packet data: {packet}")

    def try_get_name(metadata: str) -> str:
        try:
            return metadata["Name"]
        except Exception:
            return "object"

    def try_get_material(metadata: str) -> str | None:
        try:
            return metadata["Material"]
        except Exception:
            return None


class MeshHandler:
    @staticmethod
    def deserialize_mesh(data):
        try:
            vertices = [(v["X"], v["Y"], v["Z"]) for v in data["Vertices"]]
            faces = [tuple(face_list) for face_list in data["Faces"]]
            color_hexs = data.get("VertexColors")
            if color_hexs and len(color_hexs) == len(vertices):
                colors = [
                    ColorFactory.from_hex(hex_str).to_normalized_tuple() for hex_str in color_hexs
                ]
                return vertices, faces, colors
            return vertices, faces, None
        except KeyError:
            raise ValueError(f"Unsupported mesh data structure: {data}")

    @staticmethod
    def create_or_replace_mesh(object_name, vertices, faces, vertex_colors=None, material=None):
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
            obj = new_object

        # Assign vertex colors if provided
        if vertex_colors:
            MeshHandler.apply_vertex_colors(new_mesh_data, vertex_colors)

        # Assign material if provided
        if material:
            MeshHandler.apply_material(obj, material)

        new_mesh_data.update()

    @staticmethod
    def apply_vertex_colors(mesh_data, vertex_colors):
        if not mesh_data.vertex_colors:
            mesh_data.vertex_colors.new()

        color_layer = mesh_data.vertex_colors.active
        color_dict = {i: col for i, col in enumerate(vertex_colors)}

        for poly in mesh_data.polygons:
            for idx in poly.loop_indices:
                loop = mesh_data.loops[idx]
                vertex_index = loop.vertex_index
                if vertex_index in color_dict:
                    color_layer.data[idx].color = color_dict[vertex_index]

    @staticmethod
    def apply_material(obj, material):
        mat = bpy.data.materials.get(material)
        if mat:
            # if the object has no material slots, add one
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat

            return True
        else:
            print(f"Material {material} not found.")
            return False
