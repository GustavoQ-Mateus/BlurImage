from PIL import Image, ImageFilter
from app.region import Region, clamp

# Contexto além da região evita bordas escurecidas pelo blur.
CONTEXT_FACTOR = 3


def blur_regions(image: Image.Image, regions: list[Region]) -> Image.Image:
    result = image.copy()
    for region in regions:
        margin = region.radius * CONTEXT_FACTOR
        context = clamp(
            region.with_box(region.left - margin, region.top - margin, region.right + margin, region.bottom + margin),
            *image.size,
        )
        blurred = image.crop(context.box).filter(ImageFilter.GaussianBlur(region.radius))
        inner = (
            region.left - context.left,
            region.top - context.top,
            region.right - context.left,
            region.bottom - context.top,
        )
        result.paste(blurred.crop(inner), (region.left, region.top))
    return result
