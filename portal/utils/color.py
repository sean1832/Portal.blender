from typing import Tuple

class Color:
    def __init__(self, r: int, g: int, b: int, a: float = 1.0) -> None:
        """Initialize a Color object with RGB and alpha values."""
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def to_hex(self) -> str:
        """Convert the color to a hexadecimal string."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_tuple(self) -> Tuple[int, int, int, float]:
        """Return the color as a tuple of (r, g, b, a)."""
        return (self.r, self.g, self.b, self.a)

    def to_normalized_tuple(self) -> Tuple[float, float, float, float]:
        """Return the color as a normalized tuple of (r, g, b, a)."""
        return (self.r / 255, self.g / 255, self.b / 255, self.a)

    def __str__(self) -> str:
        """Return the string representation of the color."""
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"


class ColorFactory:
    @staticmethod
    def from_hex(hex_str: str) -> Color:
        """Create a Color object from a hexadecimal string."""
        hex_str = hex_str.lstrip("#")
        return Color(*[int(hex_str[i : i + 2], 16) for i in (0, 2, 4)])

    @staticmethod
    def from_rgb(r: int, g: int, b: int, a: float = 1.0) -> Color:
        """Create a Color object from RGB and alpha values."""
        return Color(r, g, b, a)

    @staticmethod
    def from_tuple(color_tuple: Tuple[int, int, int, float]) -> Color:
        """Create a Color object from a tuple of (r, g, b, a)."""
        return Color(*color_tuple)

    @staticmethod
    def from_normalized_tuple(color_tuple: Tuple[float, float, float, float]) -> Color:
        """Create a Color object from a normalized tuple of (r, g, b, a)."""
        return Color(*(int(x * 255) for x in color_tuple))


class ColorDecorator:
    def __init__(self, color: Color) -> None:
        """Initialize a ColorDecorator with a Color object."""
        self._color = color

    def to_hex(self) -> str:
        """Convert the decorated color to a hexadecimal string."""
        return self._color.to_hex()

    def to_tuple(self) -> Tuple[int, int, int, float]:
        """Return the decorated color as a tuple of (r, g, b, a)."""
        return self._color.to_tuple()

    def __str__(self) -> str:
        """Return the string representation of the decorated color."""
        return str(self._color)


class AlphaColorDecorator(ColorDecorator):
    def __init__(self, color: Color, alpha: float) -> None:
        """Initialize an AlphaColorDecorator with a Color object and an alpha value."""
        super().__init__(color)
        self._color.a = alpha


# Example usage:
# color1 = ColorFactory.from_hex("#ff5733")
# color2 = ColorFactory.from_rgb(255, 87, 51)
# decorated_color = AlphaColorDecorator(color1, 0.5)
# print(decorated_color)