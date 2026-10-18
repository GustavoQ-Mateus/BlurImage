import struct
from app.heif.boxes import Box, serialize_box, serialize_full_box
from app.heif.container import Association, Extent, Location, serialize_iloc, serialize_iprp

ITEM_ID = 1


def standalone_file(item_type: str, data: bytes, properties: list[Box]) -> bytes:
    ftyp = serialize_box("ftyp", b"heic" + struct.pack(">I", 0) + b"mif1heic")

    def build(data_offset: int) -> bytes:
        hdlr = serialize_full_box("hdlr", 0, 0, struct.pack(">I", 0) + b"pict" + bytes(12) + b"\0")
        pitm = serialize_full_box("pitm", 0, 0, struct.pack(">H", ITEM_ID))
        infe = serialize_full_box("infe", 2, 0, struct.pack(">HH", ITEM_ID, 0) + item_type.encode("ascii") + b"\0")
        iinf = serialize_full_box("iinf", 0, 0, struct.pack(">H", 1) + infe)
        iloc = serialize_iloc(1, {ITEM_ID: Location(0, 0, [Extent(data_offset, len(data))])}, 4)
        associations = {ITEM_ID: [Association(index + 1, False) for index in range(len(properties))]}
        iprp = serialize_iprp(properties, associations, 0)
        return serialize_box("meta", bytes(4) + hdlr + pitm + iloc + iinf + iprp)

    meta_size = len(build(0))
    data_offset = len(ftyp) + meta_size + 8
    return ftyp + build(data_offset) + serialize_box("mdat", data)
