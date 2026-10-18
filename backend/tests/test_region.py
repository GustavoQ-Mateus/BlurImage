import pytest
from PIL import Image
from app.region import Region, align_to_grid, clamp, to_raw
from tests.conftest import photo

TRANSPOSE = {
    2: Image.Transpose.FLIP_LEFT_RIGHT,
    3: Image.Transpose.ROTATE_180,
    4: Image.Transpose.FLIP_TOP_BOTTOM,
    5: Image.Transpose.TRANSPOSE,
    6: Image.Transpose.ROTATE_270,
    7: Image.Transpose.TRANSVERSE,
    8: Image.Transpose.ROTATE_90,
}


@pytest.mark.parametrize("orientation", range(1, 9))
def test_to_raw_maps_displayed_region_to_same_pixels(orientation):
    raw = photo()
    method = TRANSPOSE.get(orientation)
    displayed = raw.transpose(method) if method is not None else raw
    region = Region(10, 20, 60, 45, radius=5)

    raw_region = to_raw(region, orientation, *raw.size)

    raw_crop = raw.crop(raw_region.box)
    raw_crop = raw_crop.transpose(method) if method is not None else raw_crop
    assert raw_crop.tobytes() == displayed.crop(region.box).tobytes()


def test_clamp_cuts_to_image_bounds():
    assert clamp(Region(-5, -5, 50, 300, 1), 100, 100) == Region(0, 0, 50, 100, 1)


def test_clamp_returns_none_outside_image():
    assert clamp(Region(120, 0, 150, 10, 1), 100, 100) is None


def test_align_to_grid_expands_to_cells_and_stops_at_edge():
    assert align_to_grid(Region(17, 3, 40, 85, 1), 16, 16, 100, 90) == Region(16, 0, 48, 90, 1)
