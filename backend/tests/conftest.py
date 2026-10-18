import os
import shutil
from io import BytesIO
import pytest
from PIL import Image, ImageCms

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
