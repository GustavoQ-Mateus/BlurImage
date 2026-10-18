import os
import shutil
from io import BytesIO
from typing import Annotated
import pillow_heif
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from app.codecs import Codec, UnsupportedImage, build_codecs
from app.codecs.heic import heic_preview
from app.region import Region

MAX_RADIUS = 500
HEIF = "HEIF"

pillow_heif.register_heif_opener()


class RegionIn(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    radius: int = Field(gt=0, le=MAX_RADIUS)

    def to_region(self) -> Region:
        return Region(self.x, self.y, self.x + self.width, self.y + self.height, self.radius)


REGIONS = TypeAdapter(list[RegionIn])


def create_app(codecs: dict[str, Codec] | None = None) -> FastAPI:
    codecs = codecs if codecs is not None else build_codecs(_find_jpegtran())
    app = FastAPI(title="BlurImage")

    @app.post("/api/blur")
    async def blur(file: UploadFile, regions: Annotated[str, Form()]) -> Response:
        try:
            parsed = [r.to_region() for r in REGIONS.validate_json(regions)]
        except ValidationError as error:
            raise HTTPException(422, f"Regiões inválidas: {error.errors()}") from error

        data = await file.read()
        image_format = _detect_format(data)
        codec = codecs.get(image_format)
        if codec is None:
            raise HTTPException(415, f"Formato {image_format} não suportado.")

        try:
            result = codec.apply(data, parsed)
        except UnsupportedImage as error:
            raise HTTPException(422, str(error)) from error
        return Response(result, media_type=Image.MIME[image_format])

    @app.post("/api/preview")
    async def preview(file: UploadFile) -> Response:
        data = await file.read()
        if _detect_format(data) != HEIF:
            raise HTTPException(415, "Prévia só é necessária para HEIC.")
        return Response(heic_preview(data), media_type="image/jpeg")

    return app


def _detect_format(data: bytes) -> str:
    try:
        with Image.open(BytesIO(data)) as image:
            return image.format
    except UnidentifiedImageError as error:
        raise HTTPException(415, "Arquivo não é uma imagem reconhecida.") from error


def _find_jpegtran() -> str:
    path = os.environ.get("JPEGTRAN") or shutil.which("jpegtran")
    if not path:
        raise RuntimeError("jpegtran não encontrado. Instale o libjpeg-turbo e coloque-o no PATH ou defina JPEGTRAN.")
    return path
