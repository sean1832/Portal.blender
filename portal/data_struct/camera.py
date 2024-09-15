import math

import bpy
import mathutils


class Camera:
    def __init__(self):
        """Initialize the Camera object without requiring a name or other details."""
        self.position = (0, 0, 0)
        self.look_direction = (0, 0, -1)
        self.resolution_x = 1920
        self.resolution_y = 1080
        self.aspect_ratio = self.resolution_x / self.resolution_y
        self.focal_length = 50.0
        self.vertical_fov = 35.0
        self.horizontal_fov = 50.0
        self.camera_object = None

    def set_data(
        self,
        position=None,
        look_direction=None,
        resolution=None,
        focal_length=50.0,
        vertical_fov=35.0,
        horizontal_fov=50.0,
    ):
        """Set the camera data."""
        self.position = position or (0, 0, 0)
        self.look_direction = look_direction or (0, 0, -1)
        self.resolution_x, self.resolution_y = resolution or (1920, 1080)
        self.aspect_ratio = self.resolution_x / self.resolution_y
        self.focal_length = focal_length
        self.vertical_fov = vertical_fov
        self.horizontal_fov = horizontal_fov

    def sync_camera(self, name, collection_name=None):
        """Synchronize camera data with the Blender camera object."""
        self.camera_object = self._get_or_create_camera(name, collection_name)
        cam = self.camera_object
        cam.location = self.position

        # Calculate the target point the camera should look at
        look_vector = mathutils.Vector(self.look_direction)
        target_point = mathutils.Vector(self.position) + look_vector
        direction = target_point - cam.location

        # Set the rotation of the camera to look at the target point
        cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = direction.to_track_quat("-Z", "Y")

        self._set_camera_resolution()
        self._set_camera_fov_and_lens()
    
    def set_cliping(self, near, far):
        cam = self.camera_object
        cam.data.clip_start = near
        cam.data.clip_end = far

    def _set_camera_resolution(self):
        """Set the resolution of the camera's render."""
        bpy.context.scene.render.resolution_x = self.resolution_x
        bpy.context.scene.render.resolution_y = self.resolution_y
        self.aspect_ratio = self.resolution_x / self.resolution_y

    def _set_camera_fov_and_lens(self):
        """Set the field of view (FOV) and lens of the camera."""
        cam = self.camera_object
        cam.data.lens = self.focal_length

        if self.aspect_ratio >= 1.0:
            # Use vertical FOV for landscape orientation
            cam.data.sensor_fit = "VERTICAL"
            vertical_fov_rad = math.radians(self.vertical_fov)
            sensor_height = 2 * self.focal_length * math.tan(vertical_fov_rad / 2)
            sensor_width = sensor_height * self.aspect_ratio
        else:
            # Use horizontal FOV for portrait orientation
            cam.data.sensor_fit = "HORIZONTAL"
            horizontal_fov_rad = math.radians(self.horizontal_fov)
            sensor_width = 2 * self.focal_length * math.tan(horizontal_fov_rad / 2)
            sensor_height = sensor_width / self.aspect_ratio

        # Set sensor size
        cam.data.sensor_width = sensor_width
        cam.data.sensor_height = sensor_height

    def _get_or_create_camera(self, name, collection_name=None):
        """Get an existing camera or create a new one in the scene."""
        cam = bpy.data.objects.get(name)
        if not cam or cam.type != "CAMERA":
            # Create a new camera if it doesn't exist
            cam_data = bpy.data.cameras.new(name)
            cam = bpy.data.objects.new(name, cam_data)
            self._link_object_to_collection(cam, collection_name)
            bpy.context.scene.camera = cam
        return cam

    def _link_object_to_collection(self, obj, collection_name=None):
        """Link the camera object to the appropriate Blender collection."""
        if collection_name:
            collection = bpy.data.collections.get(collection_name)
            if not collection:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)
            collection.objects.link(obj)
        else:
            bpy.context.collection.objects.link(obj)

    @staticmethod
    def from_dict(camera_dict):
        """Create a Camera object from raw data."""
        position = (
            camera_dict["Position"]["X"],
            camera_dict["Position"]["Y"],
            camera_dict["Position"]["Z"],
        )
        look_direction = (
            camera_dict["LookDirection"]["X"],
            camera_dict["LookDirection"]["Y"],
            camera_dict["LookDirection"]["Z"],
        )
        resolution = (camera_dict["Resolution"]["X"], camera_dict["Resolution"]["Y"])
        focal_length = camera_dict.get("FocalLength", 50.0)
        vertical_fov = camera_dict.get("VerticalFov", 35.0)
        horizontal_fov = camera_dict.get("HorizontalFov", 50.0)

        camera = Camera()
        camera.set_data(
            position, look_direction, resolution, focal_length, vertical_fov, horizontal_fov
        )
        return camera
