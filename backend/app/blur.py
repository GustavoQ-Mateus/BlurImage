from PIL import Image, ImageDraw, ImageFilter
from app.region import Box, Region, clamp_box, expand_box

# Contexto além da região evita bordas escurecidas pelo blur.
CONTEXT_FACTOR = 3
OPAQUE = 255


def blur_regions(image: Image.Image, regions: list[Region]) -> Image.Image:
    result = image.copy()
    for region in regions:
        box = clamp_box(region.bounds, *image.size)
        if box is None:
            continue
        context = clamp_box(expand_box(box, region.radius * CONTEXT_FACTOR), *image.size)
        blurred = image.crop(context).filter(ImageFilter.GaussianBlur(region.radius))
        inner = (box[0] - context[0], box[1] - context[1], box[2] - context[0], box[3] - context[1])
        result.paste(blurred.crop(inner), box[:2], _mask(region, box))
    return result


def _mask(region: Region, box: Box) -> Image.Image:
    mask = Image.new("L", (box[2] - box[0], box[3] - box[1]))
    corners = [(x - box[0], y - box[1]) for x, y in region.corners]
    ImageDraw.Draw(mask).polygon(corners, fill=OPAQUE)
    return mask
