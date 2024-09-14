import gzip
import io
import json
import math
import struct
from typing import Tuple

import bpy  # type: ignore
import mathutils

from ..data_struct.packet import PacketHeader
from ..data_struct.color import ColorFactory


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
    def handle_str_data(payload, data_type, index):
        if payload is None:
            return
        try:
            if data_type == "Text":
                print(f"Received message: {payload}")
            elif data_type == "Mesh":
                message_dics, global_metadata = StringHandler.unpack_packet(json.loads(payload))
                StringHandler.try_handle_camera(global_metadata)  # set camera properties if available

                for i, item in enumerate(message_dics):
                    data, metadata = StringHandler.unpack_packet(item)
                    vertices, faces, colors = MeshHandler.deserialize_mesh(data)
                    object_name = StringHandler.try_get_name(metadata)
                    material = StringHandler.try_get_material(metadata)
                    MeshHandler.create_or_replace_mesh(
                        f"{object_name}_{i}-con-{index}",
                        vertices,
                        faces,
                        colors,
                        material,
                        collection_name=f"connection-{index}",
                    )
        except json.JSONDecodeError:
            raise ValueError(f"Unsupported data: {payload}")

    def unpack_packet(packet: str) -> Tuple[str, str]:
        try:
            return packet["Items"], packet["Meta"]
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

    @staticmethod
    def try_handle_camera(metadata):
        if not metadata:
            return
        try:
            camera_data = metadata["Camera"]
        except KeyError:
            return  # skip if no camera data available

        try:
            # Extract position
            position = camera_data["Position"]
            cam_location = (position["X"], position["Y"], position["Z"])

            # Extract look direction
            look_direction = camera_data["LookDirection"]
            look_vector = mathutils.Vector(
                (look_direction["X"], look_direction["Y"], look_direction["Z"])
            )

            # Calculate the target point the camera should look at
            target_point = mathutils.Vector(cam_location) + look_vector

            # Set camera location
            cam = bpy.context.scene.camera
            cam.location = cam_location

            # Set camera rotation to look at the target point
            direction = target_point - cam.location
            cam.rotation_mode = "QUATERNION"
            cam.rotation_quaternion = direction.to_track_quat("-Z", "Y")

            # Set render resolution
            resolution_x = camera_data["Resolution"]["X"]
            resolution_y = camera_data["Resolution"]["Y"]
            bpy.context.scene.render.resolution_x = resolution_x
            bpy.context.scene.render.resolution_y = resolution_y

            # Calculate aspect ratio
            aspect_ratio = resolution_x / resolution_y

            # Get Focal Length
            focal_length = camera_data.get("FocalLength", 50.0)
            cam.data.lens = focal_length

            # Get FOVs
            vertical_fov_deg = camera_data["VerticalFov"]
            horizontal_fov_deg = camera_data["HorizontalFov"]

            # Decide whether to use vertical or horizontal FOV based on aspect ratio
            if aspect_ratio >= 1.0:
                # Landscape orientation: use vertical FOV
                cam.data.sensor_fit = "VERTICAL"
                vertical_fov_rad = math.radians(vertical_fov_deg)
                sensor_height = 2 * focal_length * math.tan(vertical_fov_rad / 2)
                sensor_width = sensor_height * aspect_ratio
            else:
                # Portrait orientation: use horizontal FOV
                cam.data.sensor_fit = "HORIZONTAL"
                horizontal_fov_rad = math.radians(horizontal_fov_deg)
                sensor_width = 2 * focal_length * math.tan(horizontal_fov_rad / 2)
                sensor_height = sensor_width / aspect_ratio

            # Set sensor size
            cam.data.sensor_width = sensor_width
            cam.data.sensor_height = sensor_height

        except KeyError:
            return  # skip if camera data is incomplete


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
    def create_or_replace_mesh(
        object_name, vertices, faces, vertex_colors=None, material=None, collection_name=None
    ):
        # Check if the collection_name is provided and if the collection exists, if not, create it
        collection = None
        if collection_name:
            collection = bpy.data.collections.get(collection_name)
            if not collection:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)

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
            if collection:
                collection.objects.link(new_object)  # Link to the specified collection
            else:
                bpy.context.collection.objects.link(
                    new_object
                )  # Link to the current context collection
            obj = new_object

        # Assign vertex colors if provided
        if vertex_colors:
            MeshHandler.apply_vertex_colors(new_mesh_data, vertex_colors)

        # Assign material if provided
        if material:
            MeshHandler.apply_material(obj, material)

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
