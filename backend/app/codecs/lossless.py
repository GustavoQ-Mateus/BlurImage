from collections.abc import Callable
from io import BytesIO
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from app.blur import blur_regions
from app.codecs.base import UnsupportedImage, ensure_single_frame, raw_regions
from app.region import Region

SUPPORTED_MODES = {"L", "LA", "RGB", "RGBA"}
METADATA_KEYS = ("icc_profile", "exif", "xmp", "dpi")

SaveOptions = Callable[[Image.Image], dict]


class LosslessCodec:
    def __init__(self, format_name: str, save_options: SaveOptions):
        self._format = format_name
        self._save_options = save_options

    def apply(self, data: bytes, regions: list[Region]) -> bytes:
        with Image.open(BytesIO(data)) as image:
            ensure_single_frame(image)
            if image.mode not in SUPPORTED_MODES:
                raise UnsupportedImage(f"{self._format} em modo {image.mode} não é suportado.")
            result = blur_regions(image, raw_regions(image, regions))
            output = BytesIO()
            result.save(output, self._format, **self._save_options(image))
        return output.getvalue()


def _metadata(image: Image.Image) -> dict:
    return {key: image.info[key] for key in METADATA_KEYS if image.info.get(key)}


def png_options(image: Image.Image) -> dict:
    text = PngInfo()
    for key, value in image.text.items():
        text.add_text(key, value)
    return {"pnginfo": text, **_metadata(image)}


def webp_options(image: Image.Image) -> dict:
    # WebP lossy também sai lossless para não somar perda.
    return {"lossless": True, "exact": True, **_metadata(image)}
