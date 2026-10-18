from app.codecs.base import Codec, UnsupportedImage
from app.codecs.jpeg import JpegCodec
from app.codecs.lossless import LosslessCodec, png_options, webp_options


def build_codecs(jpegtran: str) -> dict[str, Codec]:
    return {
        "JPEG": JpegCodec(jpegtran),
        "PNG": LosslessCodec("PNG", png_options),
        "WEBP": LosslessCodec("WEBP", webp_options),
    }


__all__ = ["Codec", "UnsupportedImage", "build_codecs"]
