from enum import Enum, auto

class PGeoType(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count  # Start at 0 instead of 1
    UNDEFINED = auto()
    MESH = auto()
    CURVE = auto()
    PLANE = auto()

class PCurveType(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count  # Start at 0 instead of 1
    BASE = auto()
    LINE = auto()
    ARC = auto()
    CIRCLE = auto()
    POLYLINE = auto()
    NURBS = auto()

class PTextureType(Enum):
    NONE = 0
    BITMAP = 1
    DIFFUSE = 1
    PBR_BASECOLOR = 1
    BUMP = 2
    OPACITY = 3
    TRANSPARENCY = 3
    PBR_SUBSURFACE = 10
    PBR_SUBSURFACE_SCATTERING = 11
    PBR_SUBSURFACE_SCATTERING_RADIUS = 12
    PBR_METALLIC = 13
    PBR_SPECULAR = 14
    PBR_SPECULAR_TINT = 15
    PBR_ROUGHNESS = 16
    PBR_ANISOTROPIC = 17
    PBR_ANISOTROPIC_ROTATION = 18
    PBR_SHEEN = 19
    PBR_SHEEN_TINT = 20
    PBR_CLEARCOAT = 21
    PBR_CLEARCOAT_ROUGHNESS = 22
    PBR_OPACITY_IOR = 23
    PBR_OPACITY_ROUGHNESS = 24
    PBR_EMISSION = 25
    PBR_AMBIENT_OCCLUSION = 26
    PBR_DISPLACEMENT = 28
    PBR_CLEARCOAT_BUMP = 29
    PBR_ALPHA = 30
    EMAP = 86