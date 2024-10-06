from typing import Tuple, Union

class Color:
    def __init__(self, r: int, g: int, b: int, a: float = 1.0, color_space: str = "linear") -> None:
        """
        Initialize a Color object with RGB and optional alpha.
        Args:
            r (int): Red value [0, 255].
            g (int): Green value [0, 255].
            b (int): Blue value [0, 255].
            a (float): Alpha value [0.0, 1.0], default is 1.0.
            color_space (str): 'srgb' or 'linear', default is 'linear'.
        """
        if color_space == "srgb":
            r, g, b = [int(round(Color._to_linear(x / 255) * 255)) for x in (r, g, b)]
        elif color_space != "linear":
            raise ValueError("Invalid color space. Use 'srgb' or 'linear'.")
        self.r = self._validate_color_value(r, "r")
        self.g = self._validate_color_value(g, "g")
        self.b = self._validate_color_value(b, "b")
        self.a = self._validate_alpha_value(a)

    @staticmethod
    def _validate_color_value(value: int, component: str) -> int:
        """
        Validate a color component (r, g, b).
        Args:
            value (int): Value to validate [0, 255].
            component (str): Color component name.
        """
        if not isinstance(value, int):
            raise TypeError(f"Component '{component}' must be an integer.")
        if not 0 <= value <= 255:
            raise ValueError(f"Component '{component}' must be between 0 and 255.")
        return value

    @staticmethod
    def _validate_alpha_value(value: float) -> float:
        """
        Validate alpha value (a).
        Args:
            value (float): Alpha value [0.0, 1.0].
        """
        if not isinstance(value, (float, int)):
            raise TypeError("Alpha must be a float or int.")
        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError("Alpha must be between 0.0 and 1.0.")
        return value

    def to_hex(self, color_type: str, color_space: str = "linear") -> str:
        """
        Convert color to hexadecimal (RGB or RGBA).
        Args:
            color_type (str): 'rgb' or 'rgba'.
            color_space (str): 'srgb' or 'linear', default is 'linear'.
        """
        r, g, b, a = self.to_tuple("rgba", normalize=False, color_space=color_space)
        if color_type == "rgb":
            return f"#{r:02X}{g:02X}{b:02X}"
        elif color_type == "rgba":
            alpha_int = int(round(a * 255))
            return f"#{r:02X}{g:02X}{b:02X}{alpha_int:02X}"
        else:
            raise ValueError("Invalid color_type. Use 'rgb' or 'rgba'.")

    def to_tuple(
        self, color_type: str, normalize: bool = False, color_space: str = "linear"
    ) -> Union[Tuple[int, int, int], Tuple[int, int, int, float]]:
        """
        Return color as (r, g, b) or (r, g, b, a) tuple.
        Args:
            color_type (str): 'rgb' or 'rgba'.
            normalize (bool): Normalize values to [0.0, 1.0], default is False.
            color_space (str): 'srgb' or 'linear', default is 'linear'.
        """
        r, g, b, a = (self.r, self.g, self.b, self.a)
        if color_space == "srgb":
            r, g, b = [int(round(self._to_srgb(x / 255) * 255)) for x in (r, g, b)]
        if color_type == "rgb":
            result = (r, g, b)
        elif color_type == "rgba":
            result = (r, g, b, a)
        else:
            raise ValueError("Invalid color_type. Use 'rgb' or 'rgba'.")
        if normalize:
            return tuple(x / 255 for x in result) if color_type == "rgb" else (r / 255, g / 255, b / 255, self.a)
        return result

    def __str__(self) -> str:
        """Return a string representation of the color."""
        return f"Color(r={self.r}, g={self.g}, b={self.b}, a={self.a})"

    def __repr__(self) -> str:
        """Return a representation string of the color."""
        return self.__str__()

    @staticmethod
    def from_hex(hex_str: str, color_space="linear") -> "Color":
        """
        Create Color from a hex string (#RRGGBB or #RRGGBBAA).
        Args:
            hex_str (str): Hexadecimal string.
            color_space (str): 'srgb' or 'linear', default is 'linear'.
        """
        if not hex_str.startswith("#") or len(hex_str) not in (7, 9):
            raise ValueError("Hex string must start with '#' and be 7 or 9 characters long.")
        hex_str = hex_str.lstrip("#")
        r, g, b = (int(hex_str[i : i + 2], 16) for i in (0, 2, 4))
        a = int(hex_str[6:8], 16) / 255.0 if len(hex_str) == 8 else 1.0
        if color_space == "srgb":
            r, g, b = [int(round(Color._to_linear(x / 255) * 255)) for x in (r, g, b)]
        return Color(r, g, b, a)

    @staticmethod
    def from_tuple(
        color_tuple: Union[Tuple[int, int, int], Tuple[int, int, int, float]], color_space="linear"
    ) -> "Color":
        """
        Create Color from an (r, g, b) or (r, g, b, a) tuple.
        Args:
            color_tuple (tuple): (r, g, b) or (r, g, b, a) tuple.
            color_space (str): 'srgb' or 'linear', default is 'linear'.
        """
        if len(color_tuple) not in (3, 4):
            raise ValueError("Tuple must have 3 or 4 elements.")
        if color_space == "srgb":
            r, g, b = [int(round(Color._to_linear(x / 255) * 255)) for x in color_tuple[:3]]
        else:
            r, g, b = [Color._validate_color_value(x, f"{i}") for i, x in enumerate(color_tuple[:3])]
        a = Color._validate_alpha_value(color_tuple[3]) if len(color_tuple) == 4 else 1.0
        return Color(r, g, b, a)

    @staticmethod
    def from_normalized_tuple(
        color_tuple: Union[Tuple[float, float, float], Tuple[float, float, float, float]],
        color_space="linear",
    ) -> "Color":
        """
        Create Color from a normalized (0.0-1.0) tuple.
        Args:
            color_tuple (tuple): Tuple of 3 or 4 normalized values.
            color_space (str): 'srgb' or 'linear', default is 'linear'.
        """
        if len(color_tuple) not in (3, 4):
            raise ValueError("Normalized tuple must have 3 or 4 elements.")
        if not all(0.0 <= x <= 1.0 for x in color_tuple[:3]):
            raise ValueError("Normalized tuple values must be between 0.0 and 1.0.")
        if color_space == "srgb":
            r, g, b = [int(round(Color._to_linear(x) * 255)) for x in color_tuple[:3]]
        else:
            r, g, b = [int(round(x * 255)) for x in color_tuple[:3]]
        a = color_tuple[3] if len(color_tuple) == 4 else 1.0
        return Color(r, g, b, a)

    @staticmethod
    def _to_srgb(value: float) -> float:
        """
        Convert linear RGB value to sRGB.
        Args:
            value (float): Linear RGB value.
        """
        if value <= 0.0031308:
            return value * 12.92
        return 1.055 * (value ** (1.0 / 2.4)) - 0.055

    @staticmethod
    def _to_linear(value: float) -> float:
        """
        Convert sRGB value to linear RGB.
        Args:
            value (float): sRGB value.
        """
        if value <= 0.04045:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4