import struct
from dataclasses import dataclass, field

HEADER_SIZE = 8
LARGE_HEADER_SIZE = 16
FULL_BOX_HEADER_SIZE = 4


@dataclass
class Box:
    type: str
    payload: bytes
    children: list["Box"] = field(default_factory=list)

    def child(self, box_type: str) -> "Box | None":
        return next((box for box in self.children if box.type == box_type), None)


@dataclass
class TopLevelBox:
    type: str
    offset: int
    size: int


def parse_boxes(data: bytes, start: int = 0, end: int | None = None) -> list[Box]:
    end = len(data) if end is None else end
    boxes = []
    position = start
    while position < end:
        box_type, header, size = _header(data, position, end)
        boxes.append(Box(box_type, data[position + header : position + size]))
        position += size
    return boxes


def list_top_level(data: bytes) -> list[TopLevelBox]:
    boxes = []
    position = 0
    while position < len(data):
        box_type, _, size = _header(data, position, len(data))
        boxes.append(TopLevelBox(box_type, position, size))
        position += size
    return boxes


def serialize_box(box_type: str, payload: bytes) -> bytes:
    return struct.pack(">I4s", HEADER_SIZE + len(payload), box_type.encode("ascii")) + payload


def serialize_full_box(box_type: str, version: int, flags: int, payload: bytes) -> bytes:
    return serialize_box(box_type, struct.pack(">I", (version << 24) | flags) + payload)


def full_box_header(payload: bytes) -> tuple[int, int, bytes]:
    version_and_flags = struct.unpack_from(">I", payload)[0]
    return version_and_flags >> 24, version_and_flags & 0xFFFFFF, payload[FULL_BOX_HEADER_SIZE:]


def _header(data: bytes, position: int, end: int) -> tuple[str, int, int]:
    size, raw_type = struct.unpack_from(">I4s", data, position)
    header = HEADER_SIZE
    if size == 1:
        size = struct.unpack_from(">Q", data, position + HEADER_SIZE)[0]
        header = LARGE_HEADER_SIZE
    elif size == 0:
        size = end - position
    return raw_type.decode("latin-1"), header, size
