import jpeglib
import numpy as np
import pytest
from app.codecs.jpeg import JpegCodec
from app.region import Region, align_to_grid
from tests.conftest import decode, encode, exif_with_thumbnail, photo

REGIONS = [
    Region.rectangle(30, 25, 90, 70, radius=12),
    Region.rectangle(170, 120, 203, 157, radius=8),  # encosta na borda
]

CASES = [
    pytest.param({"subsampling": 0}, 8, id="444"),
    pytest.param({"subsampling": 2}, 16, id="420"),
    pytest.param({"subsampling": 2, "progressive": True}, 16, id="420-progressive"),
]


def changed_blocks(component: np.ndarray, block_px: int, mcu: int) -> np.ndarray:
    mask = np.zeros(component.shape[:2], dtype=bool)
    for region in REGIONS:
        left, top, right, bottom = align_to_grid(region.bounds, mcu, mcu, 10**6, 10**6)
        mask[top // block_px : -(-bottom // block_px), left // block_px : -(-right // block_px)] = True
    return mask


@pytest.mark.parametrize(("options", "mcu"), CASES)
def test_blocks_outside_regions_are_bit_identical(jpegtran, tmp_path, options, mcu):
    original = encode(photo(), "JPEG", quality=85, **options)
    result = JpegCodec(jpegtran).apply(original, REGIONS)

    (tmp_path / "a.jpg").write_bytes(original)
    (tmp_path / "b.jpg").write_bytes(result)
    before, after = jpeglib.read_dct(tmp_path / "a.jpg"), jpeglib.read_dct(tmp_path / "b.jpg")

    for name in ("Y", "Cb", "Cr"):
        a, b = getattr(before, name), getattr(after, name)
        block_px = 8 * before.Y.shape[1] // a.shape[1]
        outside = ~changed_blocks(a, block_px, mcu)
        assert np.array_equal(a[outside], b[outside]), name
    assert not np.array_equal(before.Y, after.Y), "o blur não alterou nada"


@pytest.mark.parametrize(("options", "mcu"), CASES)
def test_keeps_format_size_and_metadata(jpegtran, options, mcu):
    original = encode(photo(), "JPEG", quality=85, **options)
    result = JpegCodec(jpegtran).apply(original, REGIONS)

    before, after = decode(original), decode(result)
    assert after.format == "JPEG"
    assert after.size == before.size
    assert after.info["exif"] == before.info["exif"]
    assert after.info["icc_profile"] == before.info["icc_profile"]
    assert after.quantization == before.quantization
    assert bool(after.info.get("progressive")) == bool(before.info.get("progressive"))


def test_grayscale(jpegtran):
    original = encode(photo("L"), "JPEG", quality=90)
    result = JpegCodec(jpegtran).apply(original, REGIONS)
    assert decode(result).mode == "L"
    assert result != original


def test_exif_thumbnail_does_not_keep_original_pixels(jpegtran):
    exif = exif_with_thumbnail(photo().resize((64, 48)))
    original = encode(photo(), "JPEG", quality=85, exif=exif)

    result = JpegCodec(jpegtran).apply(original, REGIONS)

    after = decode(result).info["exif"]
    thumbnail_start = exif.index(b"\xff\xd8")
    assert len(after) == len(exif)
    assert after[:thumbnail_start] == exif[:thumbnail_start]
    assert exif[thumbnail_start:] not in result
