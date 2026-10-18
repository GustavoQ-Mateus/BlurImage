import math
from io import BytesIO
import numpy as np
import pillow_heif
import pytest
from PIL import Image
from app.codecs.heic import HeicCodec, heic_preview
from app.heif.container import HeifContainer
from app.region import Region
from tests.conftest import decode, heic, photo

REGIONS = [Region.rectangle(30, 25, 90, 70, radius=12), Region.rectangle(170, 120, 203, 157, radius=8)]
TOUCHED_TILES = {0, 1, 4, 5, 6, 7, 10, 11}
MIN_PSNR = 40


def displayed(data: bytes) -> np.ndarray:
    heif = pillow_heif.open_heif(BytesIO(data))
    return np.asarray(heif[heif.primary_index].to_pillow(), dtype=float)


def outside_mask(shape: tuple[int, ...], regions: list[Region]) -> np.ndarray:
    mask = np.ones(shape[:2], dtype=bool)
    for region in regions:
        left, top, right, bottom = region.bounds
        mask[top:bottom, left:right] = False
    return mask


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = np.mean((a - b) ** 2)
    return math.inf if mse == 0 else 10 * math.log10(255**2 / mse)


def tiles(data: bytes) -> list[bytes]:
    container = HeifContainer.parse(data)
    return [container.item_data(tile) for tile in container.referenced("dimg", container.primary_id)]


def test_tiles_outside_regions_are_bit_identical():
    original = heic(photo())

    result = HeicCodec().apply(original, REGIONS)

    for index, (before, after) in enumerate(zip(tiles(original), tiles(result))):
        assert (before != after) == (index in TOUCHED_TILES), index


def test_keeps_format_size_and_metadata():
    original = heic(photo())

    result = HeicCodec().apply(original, REGIONS)

    before, after = decode(original), decode(result)
    assert after.format == "HEIF"
    assert after.size == before.size
    assert after.info["exif"] == before.info["exif"]
    assert after.info["icc_profile"] == before.info["icc_profile"]


def test_touched_tiles_keep_colors_outside_regions():
    original = heic(photo())

    result = HeicCodec().apply(original, REGIONS)

    before, after = displayed(original), displayed(result)
    outside = outside_mask(before.shape, REGIONS)
    assert psnr(before[outside], after[outside]) > MIN_PSNR
    assert np.abs(before[~outside] - after[~outside]).mean() > 5


@pytest.mark.parametrize("orientation", [3, 6, 8])
def test_regions_follow_heif_rotation(orientation):
    exif = Image.Exif()
    exif[0x0112] = orientation
    original = heic(photo(), exif=exif.tobytes())
    region = Region.rectangle(20, 30, 70, 80, radius=10)

    result = HeicCodec().apply(original, [region])

    before, after = displayed(original), displayed(result)
    outside = outside_mask(before.shape, [region])
    assert psnr(before[outside], after[outside]) > MIN_PSNR
    assert np.abs(before[~outside] - after[~outside]).mean() > 5


def test_thumbnail_is_blurred_too():
    original = heic(photo(), thumbnails=[64])
    container = HeifContainer.parse(original)
    thumbnail = container.referencing("thmb", container.primary_id)[0]

    result = HeicCodec().apply(original, REGIONS)

    assert HeifContainer.parse(result).item_data(thumbnail) != container.item_data(thumbnail)


def test_replaced_data_does_not_remain_in_file():
    original = heic(photo())

    result = HeicCodec().apply(original, REGIONS)

    assert all(tile not in result for index, tile in enumerate(tiles(original)) if index in TOUCHED_TILES)


def test_preview_has_displayed_size():
    exif = Image.Exif()
    exif[0x0112] = 6
    original = heic(photo(), exif=exif.tobytes())

    preview = Image.open(BytesIO(heic_preview(original)))

    assert preview.format == "JPEG"
    assert preview.size == (photo().height, photo().width)
