from collections.abc import Callable
from dataclasses import dataclass
from math import ceil, cos, floor, radians, sin

EXIF_ORIENTATION_TAG = 0x0112
CORNER_PRECISION = 6

Point = tuple[float, float]
Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class Region:
    corners: tuple[Point, ...]
    radius: int

    @classmethod
    def rectangle(cls, left: float, top: float, right: float, bottom: float, radius: int, rotation: float = 0) -> "Region":
        corners = ((left, top), (right, top), (right, bottom), (left, bottom))
        if not rotation:
            return cls(corners, radius)
        center_x, center_y = (left + right) / 2, (top + bottom) / 2
        angle = radians(rotation)

        def rotate(corner: Point) -> Point:
            dx, dy = corner[0] - center_x, corner[1] - center_y
            x = center_x + dx * cos(angle) - dy * sin(angle)
            y = center_y + dx * sin(angle) + dy * cos(angle)
            return round(x, CORNER_PRECISION), round(y, CORNER_PRECISION)

        return cls(tuple(rotate(corner) for corner in corners), radius)

    @property
    def bounds(self) -> Box:
        xs = [x for x, _ in self.corners]
        ys = [y for _, y in self.corners]
        return floor(min(xs)), floor(min(ys)), ceil(max(xs)), ceil(max(ys))

    def mapped(self, transform: Callable[[Point], Point]) -> "Region":
        return Region(tuple(transform(corner) for corner in self.corners), self.radius)

    def scaled(self, horizontal: float, vertical: float) -> "Region":
        corners = tuple((x * horizontal, y * vertical) for x, y in self.corners)
        return Region(corners, max(round(self.radius * (horizontal + vertical) / 2), 1))


def clamp_box(box: Box, width: int, height: int) -> Box | None:
    left, top = max(box[0], 0), max(box[1], 0)
    right, bottom = min(box[2], width), min(box[3], height)
    if left >= right or top >= bottom:
        return None
    return left, top, right, bottom


def expand_box(box: Box, margin: int) -> Box:
    return box[0] - margin, box[1] - margin, box[2] + margin, box[3] + margin


def intersects(region: Region, width: int, height: int) -> bool:
    return clamp_box(region.bounds, width, height) is not None


def to_raw(region: Region, orientation: int, raw_width: int, raw_height: int) -> Region:
    w, h = raw_width, raw_height
    transforms = {
        2: lambda p: (w - p[0], p[1]),
        3: lambda p: (w - p[0], h - p[1]),
        4: lambda p: (p[0], h - p[1]),
        5: lambda p: (p[1], p[0]),
        6: lambda p: (p[1], h - p[0]),
        7: lambda p: (w - p[1], h - p[0]),
        8: lambda p: (w - p[1], p[0]),
    }
    transform = transforms.get(orientation)
    return region.mapped(transform) if transform else region


def align_to_grid(box: Box, cell_width: int, cell_height: int, width: int, height: int) -> Box:
    return (
        box[0] // cell_width * cell_width,
        box[1] // cell_height * cell_height,
        min(ceil(box[2] / cell_width) * cell_width, width),
        min(ceil(box[3] / cell_height) * cell_height, height),
    )


def scale_regions(regions: list[Region], source: tuple[int, int], target: tuple[int, int]) -> list[Region]:
    horizontal, vertical = target[0] / source[0], target[1] / source[1]
    scaled = (r.scaled(horizontal, vertical) for r in regions)
    return [r for r in scaled if intersects(r, *target)]
