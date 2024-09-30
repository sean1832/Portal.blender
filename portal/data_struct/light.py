from typing import Any, Optional

import bpy
import mathutils
from mathutils import Vector

from .color import Color


class Light:
    def __init__(self) -> None:
        self.object_name: Optional[str] = None

        # Light properties
        self.name: Optional[str] = None
        self.rgb_color: Optional[tuple] = None
        self.energy: Optional[float] = None
        self.type: Optional[str] = None
        self.location: Optional[tuple] = None

        # Spot light properties
        self.spot_size: Optional[float] = None
        self.spot_blend: Optional[float] = None
        self.rotation_euler: Optional[Vector] = None

    def create_or_replace(self, object_name: str, layer_path: Optional[str] = None) -> None:
        self.object_name = object_name
        existing_light = bpy.data.objects.get(object_name)
        if existing_light:
            self._replace_light(existing_light)
        else:
            self._create_new(layer_path)

    def _set_light_data(
        self, name: str, color: tuple, energy: float, type: str, location: tuple
    ) -> None:
        self.name = name
        self.rgb_color = color
        self.energy = energy
        self.type = type.upper()
        self.location = location

    def _set_spot_data(self, spot_size: float, spot_blend: float, rotation_vec: Vector) -> None:
        self.spot_size = spot_size
        self.spot_blend = spot_blend
        default_direction = mathutils.Vector((0, 0, -1))
        if rotation_vec.length > 0:
            self.rotation_euler = default_direction.rotation_difference(rotation_vec).to_euler()
        else:
            self.rotation_euler = mathutils.Euler((0, 0, 0))

    def _replace_light(self, existing_obj: Any) -> None:
        existing_light_type = existing_obj.data.type
        if existing_light_type != self.type:
            existing_obj.data.type = self.type
        existing_obj.location = self.location
        light_data = existing_obj.data
        light_data.color = self.rgb_color
        light_data.energy = self.energy
        if self.type == "SPOT":
            light_data.spot_size = self.spot_size
            light_data.spot_blend = self.spot_blend
            existing_obj.rotation_euler = self.rotation_euler
        elif self.type == "POINT":
            pass
        elif self.type == "DIRECTIONAL":
            pass
        else:
            raise ValueError(f"Unsupported light type: {self.type}")

    def _create_new(self, layer_path: Optional[str] = None) -> None:
        if self.type == "SPOT":
            type = "SPOT"
        elif self.type == "POINT":
            type = "POINT"
        elif self.type == "DIRECTIONAL":
            type = "SUN"
        elif self.type == "RECTANGULAR":
            type = "AREA"
        else:
            raise ValueError(f"Unsupported light type: {self.type}")
        name = self.name if self.name else f"{self.object_name}_{type}"
        light_data = bpy.data.lights.new(name, type)
        light_data.color = self.rgb_color
        light_data.energy = self.energy
        if self.type == "SPOT":
            light_data.spot_size = self.spot_size
            light_data.spot_blend = self.spot_blend
        elif self.type == "POINT":
            pass
        elif self.type == "DIRECTIONAL":
            pass
        else:
            raise ValueError(f"Unsupported light type: {self.type}")

        light_object = bpy.data.objects.new(self.object_name, light_data)
        light_object.location = self.location
        if self.type == "SPOT":
            light_object.rotation_euler = self.rotation_euler

        bpy.context.collection.objects.link(light_object)
        self._link_object_to_collection(light_object, layer_path)

    def _link_object_to_collection(self, obj: Any, layer_path: Optional[str] = None) -> None:
        """Link the object to the appropriate Blender collection, handling nested layers."""
        if layer_path:
            layer_names = layer_path.split("::")
            parent_collection = None

            for i, layer in enumerate(layer_names):
                # If it's the last layer in the path, check for duplicates and rename if necessary
                if i == len(layer_names) - 1:
                    collection_name = layer
                    suffix = 1
                    while bpy.data.collections.get(collection_name):
                        collection_name = f"{layer}_{suffix}"
                        suffix += 1
                else:
                    collection_name = layer

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
    def from_dict(data: dict) -> "Light":
        light = Light()
        name: str = data.get("Name")
        color: tuple = Color.from_hex(data.get("Color", "#FFFFFF")).to_tuple("rgb")
        type: str = data.get("LightType")
        energy: float = data.get("Intensity")
        pos: dict = data.get("Position")
        if not all([type, energy, pos]):
            raise ValueError("Missing required light data")
        location = (pos["X"], pos["Y"], pos["Z"])
        light._set_light_data(name, color, energy, type, location)

        if type.upper() == "SPOT":
            spot_size: float = data.get("SpotAngleRadians")
            radii: dict = data.get("SpotRadii")
            spot_blend = 1 - (radii.get("Inner") / radii.get("Outer")) # FIXME: blender's spot_blend is probably not linear.
            direction: dict = data.get("Direction")
            if not all([spot_size, spot_blend, direction]):
                raise ValueError("Missing required spot light data")
            direction_vector = mathutils.Vector(
                (direction["X"], direction["Y"], direction["Z"])
            ).normalized()
            # TODO: implement spot light scale. Currently scale is default (1, 1, 1).
            light._set_spot_data(spot_size, spot_blend, direction_vector)
        elif type.upper() == "POINT":
            pass
        elif type.upper() == "DIRECTIONAL":
            pass
        elif type.upper() == "RECTANGULAR":
            raise NotImplementedError("Area light type is not supported yet")
        else:
            raise ValueError(f"Unsupported light type: {type}")

        return light
