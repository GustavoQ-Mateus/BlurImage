from io import BytesIO
import numpy as np
from PIL import Image
from app.exif_thumbnail import blur_exif_thumbnail
from app.region import Region
from tests.conftest import SIZE, exif_with_thumbnail, photo

THUMBNAIL_SIZE = (64, 48)
LEFT_HALF = Region(0, 0, SIZE[0] // 2, SIZE[1], radius=20)


def thumbnail_of(exif: bytes) -> Image.Image:
    start = exif.index(b"\xff\xd8")
    return Image.open(BytesIO(exif[start:]))


def detail(pixels: np.ndarray) -> float:
    return float(np.abs(np.diff(pixels, axis=1)).mean())


def test_thumbnail_region_is_blurred_and_size_is_kept():
    exif = exif_with_thumbnail(photo().resize(THUMBNAIL_SIZE))

    result = blur_exif_thumbnail(exif, [LEFT_HALF], SIZE)

    before = np.asarray(thumbnail_of(exif).convert("L"), dtype=float)
    after = np.asarray(thumbnail_of(result).convert("L"), dtype=float)
    assert len(result) == len(exif)
    half = THUMBNAIL_SIZE[0] // 2
    assert detail(after[:, :half]) < detail(before[:, :half]) / 2


def test_tags_before_thumbnail_are_kept():
    exif = exif_with_thumbnail(photo().resize(THUMBNAIL_SIZE))

    result = blur_exif_thumbnail(exif, [LEFT_HALF], SIZE)

    thumbnail_start = exif.index(b"\xff\xd8")
    assert result[:thumbnail_start] == exif[:thumbnail_start]


def test_exif_without_thumbnail_is_unchanged():
    exif = Image.Exif().tobytes()

    assert blur_exif_thumbnail(exif, [LEFT_HALF], SIZE) == exif
