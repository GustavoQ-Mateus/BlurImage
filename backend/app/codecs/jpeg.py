import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from PIL import Image, JpegImagePlugin
from app.blur import blur_regions
from app.codecs.base import UnsupportedImage, ensure_single_frame, raw_regions
from app.exif_thumbnail import blur_exif_thumbnail
from app.region import Region, align_to_grid, clamp_box

BLOCK_SIZE = 8
APP1 = 0xE1
START_OF_SCAN = 0xDA


class JpegCodec:
    def __init__(self, jpegtran: str):
        self._jpegtran = jpegtran

    def apply(self, data: bytes, regions: list[Region]) -> bytes:
        with Image.open(BytesIO(data)) as image:
            ensure_single_frame(image)
            subsampling = _subsampling(image)
            progressive = bool(image.info.get("progressive"))
            exif = image.info.get("exif", b"")
            cell_width, cell_height = _mcu_size(image)
            targets = raw_regions(image, regions)
            blurred = blur_regions(image, targets)
            patches = []
            for region in targets:
                cell = align_to_grid(clamp_box(region.bounds, *image.size), cell_width, cell_height, *image.size)
                patch = BytesIO()
                blurred.crop(cell).save(patch, "JPEG", qtables=image.quantization, subsampling=subsampling)
                patches.append((cell[0], cell[1], patch.getvalue()))
            blurred_exif = blur_exif_thumbnail(exif, targets, image.size)
        return _replace_segment(self._drop(data, patches, progressive), exif, blurred_exif)

    def _drop(self, data: bytes, patches: list[tuple[int, int, bytes]], progressive: bool) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            current = Path(tmp, "source.jpg")
            current.write_bytes(data)
            for index, (x, y, patch) in enumerate(patches):
                patch_path = Path(tmp, f"patch{index}.jpg")
                patch_path.write_bytes(patch)
                output = Path(tmp, f"out{index}.jpg")
                command = [self._jpegtran, "-copy", "all", "-drop", f"+{x}+{y}", str(patch_path)]
                if progressive:
                    command.append("-progressive")
                command += ["-outfile", str(output), str(current)]
                subprocess.run(command, check=True, capture_output=True)
                current = output
            return current.read_bytes()


def _replace_segment(jpeg: bytes, original: bytes, replacement: bytes) -> bytes:
    if original == replacement:
        return jpeg
    position = 2
    while jpeg[position + 1] != START_OF_SCAN:
        length = int.from_bytes(jpeg[position + 2 : position + 4], "big")
        payload_start = position + 4
        if jpeg[position + 1] == APP1 and jpeg[payload_start : payload_start + length - 2] == original:
            return jpeg[:payload_start] + replacement + jpeg[payload_start + length - 2 :]
        position += 2 + length
    return jpeg


def _mcu_size(image: Image.Image) -> tuple[int, int]:
    if image.mode == "L":
        return BLOCK_SIZE, BLOCK_SIZE
    horizontal = max(h for _, h, _, _ in image.layer)
    vertical = max(v for _, _, v, _ in image.layer)
    return BLOCK_SIZE * horizontal, BLOCK_SIZE * vertical


def _subsampling(image: Image.Image) -> int:
    if image.mode == "L":
        return -1
    if image.mode != "RGB":
        raise UnsupportedImage(f"JPEG em modo {image.mode} não é suportado.")
    subsampling = JpegImagePlugin.get_sampling(image)
    if subsampling == -1:
        raise UnsupportedImage("Subsampling de cor do JPEG não suportado.")
    return subsampling
