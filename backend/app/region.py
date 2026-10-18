from dataclasses import dataclass
from math import ceil, floor

EXIF_ORIENTATION_TAG = 0x0112


@dataclass(frozen=True)
class Region:
    left: int
    top: int
    right: int
    bottom: int
    radius: int

    @property
    def box(self) -> tuple[int, int, int, int]:
        return self.left, self.top, self.right, self.bottom

    def with_box(self, left: int, top: int, right: int, bottom: int) -> "Region":
        return Region(left, top, right, bottom, self.radius)

    def scaled(self, horizontal: float, vertical: float) -> "Region":
        return Region(
            floor(self.left * horizontal),
            floor(self.top * vertical),
            ceil(self.right * horizontal),
            ceil(self.bottom * vertical),
            max(round(self.radius * (horizontal + vertical) / 2), 1),
        )


def clamp(region: Region, width: int, height: int) -> Region | None:
    left, top = max(region.left, 0), max(region.top, 0)
    right, bottom = min(region.right, width), min(region.bottom, height)
    if left >= right or top >= bottom:
        return None
    return region.with_box(left, top, right, bottom)


def to_raw(region: Region, orientation: int, raw_width: int, raw_height: int) -> Region:
    l, t, r, b = region.box
    w, h = raw_width, raw_height
    boxes = {
        1: (l, t, r, b),
        2: (w - r, t, w - l, b),
        3: (w - r, h - b, w - l, h - t),
        4: (l, h - b, r, h - t),
        5: (t, l, b, r),
        6: (t, h - r, b, h - l),
        7: (w - b, h - r, w - t, h - l),
        8: (w - b, l, w - t, r),
    }
    return region.with_box(*boxes.get(orientation, boxes[1]))


def align_to_grid(region: Region, cell_width: int, cell_height: int, width: int, height: int) -> Region:
    return region.with_box(
        region.left // cell_width * cell_width,
        region.top // cell_height * cell_height,
        min(ceil(region.right / cell_width) * cell_width, width),
        min(ceil(region.bottom / cell_height) * cell_height, height),
    )


def scale_regions(regions: list[Region], source: tuple[int, int], target: tuple[int, int]) -> list[Region]:
    horizontal, vertical = target[0] / source[0], target[1] / source[1]
    scaled = (clamp(r.scaled(horizontal, vertical), *target) for r in regions)
    return [r for r in scaled if r is not None]
