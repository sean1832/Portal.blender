from enum import Enum
from typing import Tuple, Union


class ColorType(Enum):
    RGB = "rgb"
    RGBA = "rgba"


class Color:
    def __init__(self, r: int, g: int, b: int, a: float = 1.0) -> None:
        """Initialize a Color object with RGB and optional alpha values."""
        self.r = self._validate_color_value(r, "r")
        self.g = self._validate_color_value(g, "g")
        self.b = self._validate_color_value(b, "b")
        self.a = self._validate_alpha_value(a)

    @staticmethod
    def _validate_color_value(value: int, component: str) -> int:
        """Ensure color component (r, g, b) is a valid integer in range [0, 255]."""
        if not isinstance(value, int):
            raise TypeError(f"Component '{component}' must be an integer.")
        if not 0 <= value <= 255:
            raise ValueError(f"Component '{component}' must be between 0 and 255.")
        return value

    @staticmethod
    def _validate_alpha_value(value: float) -> float:
        """Ensure alpha component (a) is a valid float in range [0.0, 1.0]."""
        if not isinstance(value, (float, int)):
            raise TypeError("Alpha must be a float or int.")
        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError("Alpha must be between 0.0 and 1.0.")
        return value

    def to_hex(self, type: Union[ColorType, str] = ColorType.RGBA) -> str:
        """Convert color to hexadecimal string (RGB or RGBA)."""
        type = type.lower() if isinstance(type, str) else type.value
        if type == "rgb":
            return f"#{self.r:02X}{self.g:02X}{self.b:02X}"
        elif type == "rgba":
            alpha_int = int(round(self.a * 255))
            return f"#{self.r:02X}{self.g:02X}{self.b:02X}{alpha_int:02X}"
        else:
            raise ValueError("Invalid color type. Use 'rgb' or 'rgba'.")

    def to_tuple(self, type: Union[ColorType, str] = ColorType.RGBA, normalize: bool = False) -> Union[Tuple[int, int, int], Tuple[int, int, int, float]]:
        """Return the color as an (r, g, b) or (r, g, b, a) tuple, optionally normalized."""
        type = type.lower() if isinstance(type, str) else type.value
        if type == "rgb":
            result = (self.r, self.g, self.b)
        else:
            result = (self.r, self.g, self.b, self.a)

        if normalize:
            return tuple(x / 255 for x in result) if type == "rgb" else (result[0] / 255, result[1] / 255, result[2] / 255, self.a)

        return result

    def __str__(self) -> str:
        return f"Color(r={self.r}, g={self.g}, b={self.b}, a={self.a})"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def from_hex(hex_str: str) -> "Color":
        """Create a Color from a hexadecimal string (#RRGGBB or #RRGGBBAA)."""
        if not hex_str.startswith("#") or len(hex_str) not in (7, 9):
            raise ValueError("Hex string must start with '#' and be 7 or 9 characters long.")
        hex_str = hex_str.lstrip("#")
        r, g, b = (int(hex_str[i:i + 2], 16) for i in (0, 2, 4))
        a = int(hex_str[6:8], 16) / 255.0 if len(hex_str) == 8 else 1.0
        return Color(r, g, b, a)

    @staticmethod
    def from_tuple(color_tuple: Union[Tuple[int, int, int], Tuple[int, int, int, float]]) -> "Color":
        """Create a Color from an (r, g, b) or (r, g, b, a) tuple."""
        if len(color_tuple) not in (3, 4):
            raise ValueError("Tuple must have 3 or 4 elements.")
        return Color(*color_tuple) if len(color_tuple) == 3 else Color(*color_tuple[:3], color_tuple[3])

    @staticmethod
    def from_normalized_tuple(color_tuple: Union[Tuple[float, float, float], Tuple[float, float, float, float]]) -> "Color":
        """Create a Color from a normalized (0.0-1.0) tuple."""
        if len(color_tuple) not in (3, 4):
            raise ValueError("Normalized tuple must have 3 or 4 elements.")
        r, g, b = (int(round(x * 255)) for x in color_tuple[:3])
        a = color_tuple[3] if len(color_tuple) == 4 else 1.0
        return Color(r, g, b, a)
