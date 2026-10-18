import struct
from dataclasses import dataclass, field
from app.heif.boxes import (
    HEADER_SIZE,
    Box,
    full_box_header,
    list_top_level,
    parse_boxes,
    serialize_box,
    serialize_full_box,
)

FILE_OFFSET = 0
IDAT_OFFSET = 1
MAX_SHORT_INDEX = 0x7F
MAX_SHORT_ID = 0xFFFF
MAX_32_BIT = 0xFFFFFFFF


class InvalidHeif(Exception):
    pass


@dataclass
class Extent:
    offset: int
    length: int


@dataclass
class Location:
    construction_method: int
    data_reference_index: int
    extents: list[Extent]


@dataclass
class Association:
    index: int
    essential: bool


@dataclass
class Reference:
    type: str
    from_id: int
    to_ids: list[int]


@dataclass
class Grid:
    rows: int
    columns: int
    width: int
    height: int


@dataclass
class Replacement:
    data: bytes
    decoder_config: Box | None


@dataclass
class HeifContainer:
    data: bytes
    meta_offset: int
    meta_size: int
    meta_version_flags: bytes
    meta_children: list[Box]
    primary_id: int
    item_types: dict[int, str]
    locations: dict[int, Location]
    iloc_version: int
    properties: list[Box]
    associations: dict[int, list[Association]]
    ipma_version: int
    references: list[Reference]
    idat: bytes
    replacements: dict[int, Replacement] = field(default_factory=dict)

    @classmethod
    def parse(cls, data: bytes) -> "HeifContainer":
        meta_entry = next((box for box in list_top_level(data) if box.type == "meta"), None)
        if meta_entry is None:
            raise InvalidHeif("Arquivo HEIF sem caixa meta.")
        meta_payload = parse_boxes(data, meta_entry.offset, meta_entry.offset + meta_entry.size)[0].payload
        children = parse_boxes(meta_payload, 4)
        meta = Box("meta", meta_payload, children)
        iprp = _required(meta, "iprp")
        iprp.children = parse_boxes(iprp.payload)
        iloc_version, locations = _parse_iloc(_required(meta, "iloc").payload)
        ipma_version, associations = _parse_ipma([box for box in iprp.children if box.type == "ipma"])
        iref = meta.child("iref")
        idat = meta.child("idat")
        return cls(
            data=data,
            meta_offset=meta_entry.offset,
            meta_size=meta_entry.size,
            meta_version_flags=meta_payload[:4],
            meta_children=children,
            primary_id=_parse_pitm(_required(meta, "pitm").payload),
            item_types=_parse_iinf(_required(meta, "iinf").payload),
            locations=locations,
            iloc_version=iloc_version,
            properties=parse_boxes(_required(iprp, "ipco").payload),
            associations=associations,
            ipma_version=ipma_version,
            references=_parse_iref(iref.payload) if iref else [],
            idat=idat.payload if idat else b"",
        )

    def item_data(self, item_id: int) -> bytes:
        location = self.locations[item_id]
        if location.data_reference_index != 0:
            raise InvalidHeif("Dados em arquivo externo não são suportados.")
        source = self.idat if location.construction_method == IDAT_OFFSET else self.data
        return b"".join(source[e.offset : e.offset + (e.length or len(source))] for e in location.extents)

    def property(self, item_id: int, property_type: str) -> Box | None:
        for association in self.associations.get(item_id, []):
            candidate = self.properties[association.index - 1]
            if candidate.type == property_type:
                return candidate
        return None

    def referenced(self, reference_type: str, from_id: int) -> list[int]:
        return [i for r in self.references if r.type == reference_type and r.from_id == from_id for i in r.to_ids]

    def referencing(self, reference_type: str, to_id: int) -> list[int]:
        return [r.from_id for r in self.references if r.type == reference_type and to_id in r.to_ids]

    def grid(self, item_id: int) -> Grid:
        payload = self.item_data(item_id)
        flags, rows_minus_one, columns_minus_one = payload[1], payload[2], payload[3]
        size_format = ">II" if flags & 1 else ">HH"
        width, height = struct.unpack_from(size_format, payload, 4)
        return Grid(rows_minus_one + 1, columns_minus_one + 1, width, height)

    def size(self, item_id: int) -> tuple[int, int]:
        ispe = self.property(item_id, "ispe")
        if ispe is None:
            raise InvalidHeif(f"Item {item_id} sem dimensões.")
        return struct.unpack_from(">II", ispe.payload, 4)

    def replace(self, item_id: int, data: bytes, decoder_config: Box | None) -> None:
        self.replacements[item_id] = Replacement(data, decoder_config)

    def serialize(self) -> bytes:
        properties, associations = self._properties_with_replacements()
        appended, new_offsets = self._appended_data()
        offset_size = 8 if len(self.data) + len(appended) > MAX_32_BIT else 4

        def build_meta(layout: "_Layout | None") -> bytes:
            locations = self._relocated(layout, new_offsets)
            return self._serialize_meta(properties, associations, locations, offset_size)

        layout = _Layout(self.data, len(build_meta(None)), self._replaced_ranges())
        return layout.build(self.data, build_meta(layout)) + serialize_box("mdat", appended)

    def _properties_with_replacements(self) -> tuple[list[Box], dict[int, list[Association]]]:
        properties = list(self.properties)
        associations = {item: list(values) for item, values in self.associations.items()}
        for item_id, replacement in self.replacements.items():
            config = replacement.decoder_config
            if config is None:
                continue
            existing = next(
                (i for i, p in enumerate(properties) if p.type == config.type and p.payload == config.payload),
                None,
            )
            if existing is None:
                properties.append(config)
                existing = len(properties) - 1
            associations[item_id] = [
                Association(existing + 1, a.essential) if properties[a.index - 1].type == config.type else a
                for a in associations[item_id]
            ]
        return properties, associations

    def _appended_data(self) -> tuple[bytes, dict[int, Extent]]:
        chunks = []
        offsets = {}
        position = 0
        for item_id, replacement in self.replacements.items():
            offsets[item_id] = Extent(position, len(replacement.data))
            chunks.append(replacement.data)
            position += len(replacement.data)
        return b"".join(chunks), offsets

    def _relocated(self, layout: "_Layout | None", new_offsets: dict[int, Extent]) -> dict[int, Location]:
        appended_start = layout.size + HEADER_SIZE if layout else 0
        locations = {}
        for item_id, location in self.locations.items():
            if item_id in new_offsets:
                extent = new_offsets[item_id]
                locations[item_id] = Location(FILE_OFFSET, 0, [Extent(appended_start + extent.offset, extent.length)])
            elif location.construction_method == FILE_OFFSET and layout:
                extents = [Extent(layout.new_offset(e.offset), e.length) for e in location.extents]
                locations[item_id] = Location(FILE_OFFSET, location.data_reference_index, extents)
            else:
                locations[item_id] = location
        return locations

    def _replaced_ranges(self) -> list[tuple[int, int]]:
        ranges = [
            (extent.offset, extent.offset + extent.length)
            for item_id in self.replacements
            if self.locations[item_id].construction_method == FILE_OFFSET
            for extent in self.locations[item_id].extents
        ]
        return sorted(ranges)

    def _serialize_meta(
        self,
        properties: list[Box],
        associations: dict[int, list[Association]],
        locations: dict[int, Location],
        offset_size: int,
    ) -> bytes:
        children = []
        for child in self.meta_children:
            if child.type == "iloc":
                children.append(serialize_iloc(self.iloc_version, locations, offset_size))
            elif child.type == "iprp":
                children.append(serialize_iprp(properties, associations, self.ipma_version))
            else:
                children.append(serialize_box(child.type, child.payload))
        return serialize_box("meta", self.meta_version_flags + b"".join(children))


def _required(parent: Box, box_type: str) -> Box:
    box = parent.child(box_type)
    if box is None:
        raise InvalidHeif(f"Arquivo HEIF sem caixa {box_type}.")
    return box


def _parse_pitm(payload: bytes) -> int:
    version, _, body = full_box_header(payload)
    return struct.unpack_from(">H" if version == 0 else ">I", body)[0]


def _parse_iinf(payload: bytes) -> dict[int, str]:
    version, _, body = full_box_header(payload)
    count_size = 2 if version == 0 else 4
    item_types = {}
    for infe in parse_boxes(body, count_size):
        infe_version, _, infe_body = full_box_header(infe.payload)
        if infe_version < 2:
            continue
        id_format = ">H" if infe_version == 2 else ">I"
        item_id = struct.unpack_from(id_format, infe_body)[0]
        type_offset = struct.calcsize(id_format) + 2
        item_types[item_id] = infe_body[type_offset : type_offset + 4].decode("latin-1")
    return item_types


def _parse_iref(payload: bytes) -> list[Reference]:
    version, _, body = full_box_header(payload)
    id_format = ">H" if version == 0 else ">I"
    id_size = struct.calcsize(id_format)
    references = []
    for box in parse_boxes(body):
        from_id = struct.unpack_from(id_format, box.payload)[0]
        count = struct.unpack_from(">H", box.payload, id_size)[0]
        to_ids = [struct.unpack_from(id_format, box.payload, id_size + 2 + i * id_size)[0] for i in range(count)]
        references.append(Reference(box.type, from_id, to_ids))
    return references


def _parse_iloc(payload: bytes) -> tuple[int, dict[int, Location]]:
    version, _, body = full_box_header(payload)
    offset_size, length_size = body[0] >> 4, body[0] & 0xF
    base_offset_size, index_size = body[1] >> 4, (body[1] & 0xF if version in (1, 2) else 0)
    reader = _Reader(body, 2)
    count = reader.uint(2 if version < 2 else 4)
    locations = {}
    for _ in range(count):
        item_id = reader.uint(2 if version < 2 else 4)
        construction_method = reader.uint(2) & 0xF if version in (1, 2) else FILE_OFFSET
        data_reference_index = reader.uint(2)
        base_offset = reader.uint(base_offset_size)
        extents = []
        for _ in range(reader.uint(2)):
            reader.uint(index_size)
            extents.append(Extent(base_offset + reader.uint(offset_size), reader.uint(length_size)))
        locations[item_id] = Location(construction_method, data_reference_index, extents)
    return version, locations


def serialize_iloc(version: int, locations: dict[int, Location], offset_size: int) -> bytes:
    version = max(version, 2 if max(locations) > MAX_SHORT_ID else 1)
    id_format = ">H" if version < 2 else ">I"
    offset_format = ">I" if offset_size == 4 else ">Q"
    body = bytearray([(offset_size << 4) | 4, 0])
    body += struct.pack(id_format, len(locations))
    for item_id, location in locations.items():
        body += struct.pack(id_format, item_id)
        body += struct.pack(">HHH", location.construction_method, location.data_reference_index, len(location.extents))
        for extent in location.extents:
            body += struct.pack(offset_format, extent.offset) + struct.pack(">I", extent.length)
    return serialize_full_box("iloc", version, 0, bytes(body))


def _parse_ipma(boxes: list[Box]) -> tuple[int, dict[int, list[Association]]]:
    associations: dict[int, list[Association]] = {}
    highest_version = 0
    for box in boxes:
        version, flags, body = full_box_header(box.payload)
        highest_version = max(highest_version, version)
        reader = _Reader(body, 0)
        for _ in range(reader.uint(4)):
            item_id = reader.uint(2 if version < 1 else 4)
            for _ in range(reader.uint(1)):
                value = reader.uint(2 if flags & 1 else 1)
                essential_bit = 0x8000 if flags & 1 else 0x80
                associations.setdefault(item_id, []).append(Association(value & (essential_bit - 1), bool(value & essential_bit)))
    return highest_version, associations


def serialize_iprp(properties: list[Box], associations: dict[int, list[Association]], ipma_version: int) -> bytes:
    ipco = serialize_box("ipco", b"".join(serialize_box(p.type, p.payload) for p in properties))
    version = max(ipma_version, 1 if max(associations) > MAX_SHORT_ID else 0)
    long_index = len(properties) > MAX_SHORT_INDEX
    body = bytearray(struct.pack(">I", len(associations)))
    for item_id, values in associations.items():
        body += struct.pack(">H" if version < 1 else ">I", item_id)
        body.append(len(values))
        for association in values:
            if long_index:
                body += struct.pack(">H", (0x8000 if association.essential else 0) | association.index)
            else:
                body.append((0x80 if association.essential else 0) | association.index)
    ipma = serialize_full_box("ipma", version, 1 if long_index else 0, bytes(body))
    return serialize_box("iprp", ipco + ipma)


class _Layout:
    def __init__(self, data: bytes, meta_size: int, removed: list[tuple[int, int]]):
        self._segments = []
        position = 0
        for box in list_top_level(data):
            end = box.offset + box.size
            cuts = [] if box.type == "meta" else [(s, e) for s, e in removed if box.offset <= s and e <= end]
            size = meta_size if box.type == "meta" else box.size - sum(e - s for s, e in cuts)
            self._segments.append((box, position, cuts, size))
            position += size
        self.size = position

    def new_offset(self, offset: int) -> int:
        for box, start, cuts, _ in self._segments:
            if box.offset <= offset < box.offset + box.size:
                return start + offset - box.offset - sum(e - s for s, e in cuts if e <= offset)
        return offset

    def build(self, data: bytes, meta: bytes) -> bytes:
        parts = []
        for box, _, cuts, size in self._segments:
            if box.type == "meta":
                parts.append(meta)
                continue
            content = bytearray()
            position = box.offset
            for start, end in cuts:
                content += data[position:start]
                position = end
            content += data[position : box.offset + box.size]
            parts.append(_with_size(content, size) if cuts else bytes(content))
        return b"".join(parts)


def _with_size(box: bytearray, size: int) -> bytes:
    declared = struct.unpack_from(">I", box)[0]
    if declared == 1:
        struct.pack_into(">Q", box, HEADER_SIZE, size)
    elif declared != 0:
        struct.pack_into(">I", box, 0, size)
    return bytes(box)


class _Reader:
    def __init__(self, data: bytes, position: int):
        self._data = data
        self._position = position

    def uint(self, size: int) -> int:
        if size == 0:
            return 0
        value = int.from_bytes(self._data[self._position : self._position + size], "big")
        self._position += size
        return value
