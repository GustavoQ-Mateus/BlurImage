import struct
from io import BytesIO
import pillow_heif
from PIL import Image
from app.blur import CONTEXT_FACTOR, blur_regions
from app.codecs.base import UnsupportedImage
from app.exif_thumbnail import blur_exif_thumbnail
from app.heif.boxes import Box
from app.heif.container import HeifContainer, InvalidHeif
from app.heif.standalone import standalone_file
from app.region import Region, clamp_box, expand_box, intersects, scale_regions, to_raw

TILE_QUALITY = 92
PREVIEW_QUALITY = 90
CHROMA_BY_FORMAT = {1: "420", 2: "422", 3: "444"}
MONOCHROME = 0
CHROMA_FORMAT_BYTE = 16
LUMA_DEPTH_BYTE = 17
DEFAULT_NCLX = {"color_primaries": 1, "transfer_characteristics": 13, "matrix_coefficients": 6, "full_range_flag": 1}
ORIENTATION_BY_ROTATION = {0: 1, 1: 8, 2: 3, 3: 6}
ORIENTATION_BY_MIRROR = {0: 2, 1: 4}
SWAPS_AXES = {5, 6, 7, 8}


class HeicCodec:
    def apply(self, data: bytes, regions: list[Region]) -> bytes:
        try:
            container = HeifContainer.parse(data)
        except (InvalidHeif, struct.error, IndexError) as error:
            raise UnsupportedImage("Estrutura HEIC não suportada.") from error
        primary = container.primary_id
        primary_size = _image_size(container, primary)
        targets = _display_to_raw(container, primary, regions, primary_size)
        if not targets:
            return data
        _blur_item(container, primary, targets)
        for item_id in container.referencing("thmb", primary) + container.referencing("auxl", primary):
            _blur_item(container, item_id, scale_regions(targets, primary_size, _image_size(container, item_id)))
        for item_id in container.referencing("cdsc", primary):
            if container.item_types.get(item_id) == "Exif":
                _blur_exif_item(container, item_id, targets, primary_size)
        return container.serialize()


def heic_preview(data: bytes) -> bytes:
    heif = pillow_heif.open_heif(BytesIO(data))
    output = BytesIO()
    heif[heif.primary_index].to_pillow().convert("RGB").save(output, "JPEG", quality=PREVIEW_QUALITY)
    return output.getvalue()


def _image_size(container: HeifContainer, item_id: int) -> tuple[int, int]:
    if container.item_types.get(item_id) == "grid":
        grid = container.grid(item_id)
        return grid.width, grid.height
    return container.size(item_id)


def _display_to_raw(
    container: HeifContainer,
    item_id: int,
    regions: list[Region],
    raw_size: tuple[int, int],
) -> list[Region]:
    orientations = _orientations(container, item_id)
    sizes = [raw_size]
    for orientation in orientations:
        width, height = sizes[-1]
        sizes.append((height, width) if orientation in SWAPS_AXES else (width, height))
    converted = []
    for region in regions:
        for orientation, size in zip(reversed(orientations), reversed(sizes[:-1])):
            region = to_raw(region, orientation, *size)
        converted.append(region)
    return [r for r in converted if intersects(r, *raw_size)]


def _orientations(container: HeifContainer, item_id: int) -> list[int]:
    orientations = []
    for association in container.associations.get(item_id, []):
        box = container.properties[association.index - 1]
        if box.type == "clap":
            raise UnsupportedImage("HEIC com recorte (clap) não é suportado.")
        if box.type == "irot":
            orientations.append(ORIENTATION_BY_ROTATION[box.payload[0] & 0b11])
        if box.type == "imir":
            orientations.append(ORIENTATION_BY_MIRROR[box.payload[0] & 0b1])
    return orientations


def _blur_item(container: HeifContainer, item_id: int, regions: list[Region]) -> None:
    item_type = container.item_types.get(item_id)
    if item_type == "grid":
        _blur_grid(container, item_id, regions)
    elif item_type == "hvc1":
        image = _decode_coded_item(container, item_id)
        _encode_into(container, item_id, blur_regions(image, regions))
    else:
        raise UnsupportedImage(f"Imagem HEIF do tipo {item_type} não é suportada.")


def _blur_grid(container: HeifContainer, grid_id: int, regions: list[Region]) -> None:
    grid = container.grid(grid_id)
    tiles = container.referenced("dimg", grid_id)
    tile_width, tile_height = container.size(tiles[0])
    canvas_size = (grid.columns * tile_width, grid.rows * tile_height)
    boxes = [clamp_box(r.bounds, *canvas_size) for r in regions]
    context = [clamp_box(expand_box(box, r.radius * CONTEXT_FACTOR), *canvas_size) for r, box in zip(regions, boxes)]
    canvas = None
    for index in _tiles_touching(context, grid.columns, tile_width, tile_height):
        tile = _decode_coded_item(container, tiles[index])
        canvas = canvas or Image.new(tile.mode, canvas_size)
        canvas.paste(tile, _tile_box(index, grid.columns, tile_width, tile_height)[:2])
    blurred = blur_regions(canvas, regions)
    for index in _tiles_touching(boxes, grid.columns, tile_width, tile_height):
        _encode_into(container, tiles[index], blurred.crop(_tile_box(index, grid.columns, tile_width, tile_height)))


def _tiles_touching(boxes: list[tuple[int, int, int, int]], columns: int, tile_width: int, tile_height: int) -> list[int]:
    indexes = set()
    for left, top, right, bottom in boxes:
        for row in range(top // tile_height, (bottom - 1) // tile_height + 1):
            for column in range(left // tile_width, (right - 1) // tile_width + 1):
                indexes.add(row * columns + column)
    return sorted(indexes)


def _tile_box(index: int, columns: int, tile_width: int, tile_height: int) -> tuple[int, int, int, int]:
    left, top = (index % columns) * tile_width, (index // columns) * tile_height
    return left, top, left + tile_width, top + tile_height


def _decode_coded_item(container: HeifContainer, item_id: int) -> Image.Image:
    decoder_config = _decoder_config(container, item_id)
    properties = [decoder_config, container.property(item_id, "ispe")]
    nclx = _nclx_box(container, item_id)
    if nclx is not None:
        properties.append(nclx)
    heif = pillow_heif.open_heif(BytesIO(standalone_file("hvc1", container.item_data(item_id), properties)))
    image = heif[heif.primary_index].to_pillow()
    return image.convert("L") if decoder_config.payload[CHROMA_FORMAT_BYTE] & 0b11 == MONOCHROME else image


def _encode_into(container: HeifContainer, item_id: int, image: Image.Image) -> None:
    original_config = _decoder_config(container, item_id)
    chroma_format = original_config.payload[CHROMA_FORMAT_BYTE] & 0b11
    options = {"quality": TILE_QUALITY, "tile_size": 0, **_nclx_values(container, item_id)}
    if chroma_format != MONOCHROME:
        options["chroma"] = CHROMA_BY_FORMAT[chroma_format]
    output = BytesIO()
    pillow_heif.from_pillow(image).save(output, **options)
    encoded = HeifContainer.parse(output.getvalue())
    config = encoded.property(encoded.primary_id, "hvcC")
    if config.payload[CHROMA_FORMAT_BYTE] & 0b11 != chroma_format:
        raise UnsupportedImage("Não foi possível recodificar o bloco no mesmo formato de cor.")
    container.replace(item_id, encoded.item_data(encoded.primary_id), config)


def _decoder_config(container: HeifContainer, item_id: int) -> Box:
    config = container.property(item_id, "hvcC")
    if config is None:
        raise UnsupportedImage("Bloco HEIC sem configuração HEVC.")
    if config.payload[LUMA_DEPTH_BYTE] & 0b111:
        raise UnsupportedImage("HEIC com mais de 8 bits por canal ainda não é suportado.")
    return config


def _nclx_box(container: HeifContainer, item_id: int) -> Box | None:
    owners = [item_id] + container.referencing("dimg", item_id)
    for owner in owners:
        for association in container.associations.get(owner, []):
            box = container.properties[association.index - 1]
            if box.type == "colr" and box.payload[:4] == b"nclx":
                return box
    return None


def _nclx_values(container: HeifContainer, item_id: int) -> dict:
    box = _nclx_box(container, item_id)
    if box is None:
        return DEFAULT_NCLX
    primaries, transfer, matrix = struct.unpack_from(">HHH", box.payload, 4)
    return {
        "color_primaries": primaries,
        "transfer_characteristics": transfer,
        "matrix_coefficients": matrix,
        "full_range_flag": box.payload[10] >> 7,
    }


def _blur_exif_item(
    container: HeifContainer,
    item_id: int,
    regions: list[Region],
    image_size: tuple[int, int],
) -> None:
    data = container.item_data(item_id)
    tiff_start = 4 + struct.unpack_from(">I", data)[0]
    blurred = blur_exif_thumbnail(data[tiff_start:], regions, image_size)
    if blurred != data[tiff_start:]:
        container.replace(item_id, data[:tiff_start] + blurred, None)
