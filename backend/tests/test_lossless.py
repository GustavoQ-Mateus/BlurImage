import pytest
from PIL import Image, ImageOps
from app.codecs.lossless import LosslessCodec, png_options, webp_options
from app.region import Region
from tests.conftest import decode, encode, photo

REGIONS = [Region(30, 25, 90, 70, radius=12), Region(170, 120, 203, 157, radius=8)]

PNG = LosslessCodec("PNG", png_options)
WEBP = LosslessCodec("WEBP", webp_options)


def assert_only_regions_changed(before: Image.Image, after: Image.Image, regions: list[Region]) -> None:
    expected = before.copy()
    for region in regions:
        expected.paste(after.crop(region.box), region.box[:2])
    assert expected.tobytes() == after.tobytes(), "pixels fora das regiões mudaram"
    assert before.tobytes() != after.tobytes(), "o blur não alterou nada"


CASES = [
    pytest.param(PNG, "PNG", "RGB", {}, id="png-rgb"),
    pytest.param(PNG, "PNG", "RGBA", {}, id="png-rgba"),
    pytest.param(PNG, "PNG", "L", {}, id="png-gray"),
    pytest.param(WEBP, "WEBP", "RGB", {"lossless": True}, id="webp-lossless"),
    pytest.param(WEBP, "WEBP", "RGB", {"quality": 80}, id="webp-lossy"),
]


@pytest.mark.parametrize(("codec", "image_format", "mode", "options"), CASES)
def test_only_regions_change_and_metadata_is_kept(codec, image_format, mode, options):
    original = encode(photo(mode), image_format, **options)
    result = codec.apply(original, REGIONS)

    before, after = decode(original), decode(result)
    assert after.format == image_format
    assert after.size == before.size
    assert after.mode == before.mode
    assert after.info["exif"] == before.info["exif"]
    assert after.info["icc_profile"] == before.info["icc_profile"]
    assert_only_regions_changed(before, after, REGIONS)


def test_png_text_chunks_are_kept():
    from PIL.PngImagePlugin import PngInfo

    text = PngInfo()
    text.add_text("Author", "Gustavo")
    original = encode(photo(), "PNG", pnginfo=text)

    assert decode(PNG.apply(original, REGIONS)).text["Author"] == "Gustavo"


def test_regions_follow_exif_orientation():
    raw = photo()
    exif = Image.Exif()
    exif[0x0112] = 6  # girada 90° na exibição
    original = encode(raw, "PNG", exif=exif.tobytes())
    displayed_region = Region(10, 20, 60, 45, radius=6)

    result = PNG.apply(original, [displayed_region])

    before = ImageOps.exif_transpose(decode(original))
    after = ImageOps.exif_transpose(decode(result))
    assert_only_regions_changed(before, after, [displayed_region])
