import json
import pytest
from fastapi.testclient import TestClient
from app.api import create_app
from app.codecs import build_codecs
from tests.conftest import decode, encode, photo

REGIONS = json.dumps([{"x": 10, "y": 10, "width": 50, "height": 40, "radius": 10}])


@pytest.fixture
def client(jpegtran) -> TestClient:
    return TestClient(create_app(build_codecs(jpegtran)))


@pytest.mark.parametrize(("image_format", "mime"), [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")])
def test_returns_same_format(client, image_format, mime):
    original = encode(photo(), image_format)

    response = client.post("/api/blur", files={"file": ("foto", original)}, data={"regions": REGIONS})

    assert response.status_code == 200
    assert response.headers["content-type"] == mime
    assert decode(response.content).size == decode(original).size


def test_rejects_non_image(client):
    response = client.post("/api/blur", files={"file": ("a.txt", b"hello")}, data={"regions": REGIONS})
    assert response.status_code == 415


def test_rejects_unsupported_format(client):
    response = client.post("/api/blur", files={"file": ("a.gif", encode(photo("P"), "GIF"))}, data={"regions": REGIONS})
    assert response.status_code == 415


def test_rejects_invalid_regions(client):
    bad = json.dumps([{"x": 0, "y": 0, "width": 0, "height": 10, "radius": 5}])
    response = client.post("/api/blur", files={"file": ("a.png", encode(photo(), "PNG"))}, data={"regions": bad})
    assert response.status_code == 422
