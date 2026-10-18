import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from PIL import Image, JpegImagePlugin
from app.blur import blur_regions
from app.codecs.base import UnsupportedImage, ensure_single_frame, raw_regions
from app.region import Region, align_to_grid

BLOCK_SIZE = 8


class JpegCodec:
    def __init__(self, jpegtran: str):
        self._jpegtran = jpegtran

    def apply(self, data: bytes, regions: list[Region]) -> bytes:
        with Image.open(BytesIO(data)) as image:
            ensure_single_frame(image)
            subsampling = _subsampling(image)
            progressive = bool(image.info.get("progressive"))
            cell_width, cell_height = _mcu_size(image)
            targets = raw_regions(image, regions)
            blurred = blur_regions(image, targets)
            patches = []
            for region in targets:
                cell = align_to_grid(region, cell_width, cell_height, *image.size)
                patch = BytesIO()
                blurred.crop(cell.box).save(patch, "JPEG", qtables=image.quantization, subsampling=subsampling)
                patches.append((cell.left, cell.top, patch.getvalue()))
        return self._drop(data, patches, progressive)

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
