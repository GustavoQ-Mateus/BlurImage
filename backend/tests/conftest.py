import os
import shutil
import struct
from io import BytesIO
import pillow_heif
import pytest
from PIL import Image, ImageCms

pillow_heif.register_heif_opener()

# Tamanho que não é múltiplo de 16, para exercitar blocos parciais nas bordas.
SIZE = (203, 157)


def photo(mode: str = "RGB") -> Image.Image:
    bands = [
        Image.effect_noise(SIZE, 60),
        Image.linear_gradient("L").resize(SIZE),
        Image.radial_gradient("L").resize(SIZE),
        Image.effect_noise(SIZE, 30),
    ]
    image = Image.merge("RGBA", bands)
    return image.convert(mode)


def metadata() -> dict:
    exif = Image.Exif()
    exif[0x010F] = "BlurImage Test Camera"
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    return {"exif": exif.tobytes(), "icc_profile": icc}


def encode(image: Image.Image, image_format: str, **options) -> bytes:
    output = BytesIO()
    image.save(output, image_format, **(metadata() | options))
    return output.getvalue()


def heic(image: Image.Image, tile_size: int = 64, **options) -> bytes:
    output = BytesIO()
    pillow_heif.from_pillow(image).save(output, quality=80, tile_size=tile_size, **(metadata() | options))
    return output.getvalue()


def exif_with_thumbnail(thumbnail: Image.Image, orientation: int = 1) -> bytes:
    jpeg = BytesIO()
    thumbnail.save(jpeg, "JPEG", quality=90)
    ifd1_offset = 8 + 2 + 2 * 12 + 4
    thumbnail_offset = ifd1_offset + 2 + 2 * 12 + 4
    tiff = struct.pack("<2sHI", b"II", 42, 8)
    tiff += struct.pack("<H", 2)
    tiff += struct.pack("<HHI4s", 0x010F, 2, 4, b"Cam\0")
    tiff += struct.pack("<HHIHH", 0x0112, 3, 1, orientation, 0)
    tiff += struct.pack("<I", ifd1_offset)
    tiff += struct.pack("<H", 2)
    tiff += struct.pack("<HHII", 0x0201, 4, 1, thumbnail_offset)
    tiff += struct.pack("<HHII", 0x0202, 4, 1, jpeg.tell())
    tiff += struct.pack("<I", 0)
    return b"Exif\x00\x00" + tiff + jpeg.getvalue()


def decode(data: bytes) -> Image.Image:
    image = Image.open(BytesIO(data))
    image.load()
    return image


@pytest.fixture(scope="session")
def jpegtran() -> str:
    path = os.environ.get("JPEGTRAN") or shutil.which("jpegtran")
    if not path:
        pytest.skip("jpegtran não encontrado")
    return path
