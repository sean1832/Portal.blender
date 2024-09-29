import json
import time

from ...data_struct.mesh import Mesh
from ...data_struct.payload import Payload


def is_connection_duplicated(connections, name_to_check, uuid_to_ignore=None):
    """Helper function to check if a connection name is duplicated"""
    for conn in connections:
        if conn.name == name_to_check and conn.uuid != uuid_to_ignore:
            return True
    return False


def construct_packet_dict(data_items, update_precision) -> str:
    """Helper function to construct a dictionary from a collection of dictionary items"""
    payload = Payload()
    meta = {}
    contains_mesh = False
    for item in data_items:
        if item.value_type == "STRING":
            meta[item.key] = item.value_string
        elif item.value_type == "INT":
            meta[item.key] = item.value_int
        elif item.value_type == "FLOAT":
            meta[item.key] = item.value_float
        elif item.value_type == "BOOL":
            meta[item.key] = item.value_bool
        elif item.value_type == "TIMESTAMP":
            meta[item.key] = int(time.time() * 1000)
        elif item.value_type == "SCENE_OBJECT":
            contains_mesh = True
            scene_obj = item.value_scene_object
            if scene_obj.type == "MESH":
                payload.add_items(
                    Mesh.from_obj(scene_obj).to_dict(is_float=True, precision=update_precision)
                )
            elif scene_obj.type == "CAMERA":
                raise NotImplementedError("Camera object type is not supported yet")
            elif scene_obj.type == "LIGHT":
                raise NotImplementedError("Light object type is not supported yet")
            else:
                raise ValueError(f"Unsupported object type: {scene_obj.type}")
        elif item.value_type == "PROPERTY_PATH":
            meta[item.key] = get_property_from_path(item.value_property_path)
        elif item.value_type == "UUID":
            meta[item.key] = item.value_uuid

    if contains_mesh:
        payload.set_meta(meta)
        return payload.to_json_str()
    return json.dumps(meta)


def get_property_from_path(path: str):
    # Use eval to resolve the path
    value = eval(path)
    return value
