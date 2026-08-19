from __future__ import annotations

import hashlib
import math
import os
import zlib
from collections.abc import Iterator
from pathlib import Path

from ..models import FileMetadata, Frame
from ..protocol import encode_frame


def analyze_file(path: str | os.PathLike[str], chunk_size: int) -> FileMetadata:
    if not 200 <= chunk_size <= 1000:
        raise ValueError("分片大小必须在 200～1000 字节之间")
    file_path = Path(path)
    digest = hashlib.sha256()
    size = 0
    with file_path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            size += len(block)
            digest.update(block)
    hex_digest = digest.hexdigest()
    return FileMetadata(hex_digest[:16], max(1, math.ceil(size / chunk_size)), size, hex_digest, file_path.name)


def iter_frames(path: str | os.PathLike[str], chunk_size: int, metadata: FileMetadata | None = None) -> Iterator[Frame]:
    meta = metadata or analyze_file(path, chunk_size)
    with Path(path).open("rb") as stream:
        for index in range(meta.total):
            chunk = stream.read(chunk_size)
            crc = f"{zlib.crc32(chunk) & 0xFFFFFFFF:08x}"
            yield Frame(meta, index, crc, chunk)


def build_payloads(path: str | os.PathLike[str], chunk_size: int) -> tuple[FileMetadata, list[str]]:
    meta = analyze_file(path, chunk_size)
    return meta, [encode_frame(frame) for frame in iter_frames(path, chunk_size, meta)]

