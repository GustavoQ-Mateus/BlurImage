import struct
from io import BytesIO
from PIL import Image
from app.blur import blur_regions
from app.region import Region, scale_regions

EXIF_HEADER = b"Exif\x00\x00"
IFD_ENTRY_SIZE = 12
THUMBNAIL_OFFSET_TAG = 0x0201
THUMBNAIL_LENGTH_TAG = 0x0202
QUALITY_STEPS = range(90, 9, -10)


def blur_exif_thumbnail(exif: bytes, regions: list[Region], image_size: tuple[int, int]) -> bytes:
    header = EXIF_HEADER if exif.startswith(EXIF_HEADER) else b""
    tiff = bytearray(exif[len(header) :])
    location = _thumbnail_location(tiff)
    if location is None or not regions:
        return exif
    offset, length = location
    thumbnail = Image.open(BytesIO(bytes(tiff[offset : offset + length])))
    scaled = scale_regions(regions, image_size, thumbnail.size)
    tiff[offset : offset + length] = _encode_within(blur_regions(thumbnail, scaled), length)
    return header + bytes(tiff)


def _thumbnail_location(tiff: bytes) -> tuple[int, int] | None:
    if len(tiff) < 8 or tiff[:2] not in (b"II", b"MM"):
        return None
    order = "<" if tiff[:2] == b"II" else ">"
    ifd0 = struct.unpack_from(order + "I", tiff, 4)[0]
    count = struct.unpack_from(order + "H", tiff, ifd0)[0]
    ifd1 = struct.unpack_from(order + "I", tiff, ifd0 + 2 + count * IFD_ENTRY_SIZE)[0]
    if ifd1 == 0:
        return None
    values = {}
    for index in range(struct.unpack_from(order + "H", tiff, ifd1)[0]):
        tag, _, _, value = struct.unpack_from(order + "HHII", tiff, ifd1 + 2 + index * IFD_ENTRY_SIZE)
        values[tag] = value
    if THUMBNAIL_OFFSET_TAG not in values or THUMBNAIL_LENGTH_TAG not in values:
        return None
    return values[THUMBNAIL_OFFSET_TAG], values[THUMBNAIL_LENGTH_TAG]


def _encode_within(thumbnail: Image.Image, length: int) -> bytes:
    for quality in QUALITY_STEPS:
        output = BytesIO()
        thumbnail.save(output, "JPEG", quality=quality)
        if output.tell() <= length:
            return output.getvalue().ljust(length, b"\x00")
    return bytes(length)
