from typing import Protocol
from PIL import Image
from app.region import EXIF_ORIENTATION_TAG, Region, intersects, to_raw


class UnsupportedImage(Exception):
    ...


class Codec(Protocol):
    def apply(self, data: bytes, regions: list[Region]) -> bytes:
        ...


def raw_regions(image: Image.Image, regions: list[Region]) -> list[Region]:
    orientation = image.getexif().get(EXIF_ORIENTATION_TAG, 1)
    converted = (to_raw(r, orientation, *image.size) for r in regions)
    return [r for r in converted if intersects(r, *image.size)]


def ensure_single_frame(image: Image.Image) -> None:
    if getattr(image, "n_frames", 1) > 1:
        raise UnsupportedImage("Imagens animadas não são suportadas.")
