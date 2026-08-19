from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileMetadata:
    session_id: str
    total: int
    file_size: int
    digest: str
    filename: str


@dataclass(frozen=True, slots=True)
class Frame:
    metadata: FileMetadata
    index: int
    crc32: str
    chunk: bytes


@dataclass(slots=True)
class ScanStats:
    decoded: int = 0
    added: int = 0
    duplicates: int = 0
    crc_errors: int = 0
    invalid: int = 0
    foreign: int = 0


@dataclass(slots=True)
class VideoInfo:
    path: str
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    frame_count: int = 0
    status: str = "等待扫描"
    progress: float = 0.0

    @property
    def name(self) -> str:
        return Path(self.path).name


@dataclass(slots=True)
class RecoverySnapshot:
    metadata: FileMetadata | None = None
    chunks: dict[int, bytes] = field(default_factory=dict)
    videos: list[dict[str, object]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

