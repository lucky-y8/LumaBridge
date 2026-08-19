from __future__ import annotations

from ..models import FileMetadata, Frame, RecoverySnapshot, ScanStats


class MetadataConflictError(RuntimeError):
    pass


class ChunkConflictError(RuntimeError):
    pass


class ChunkCollector:
    def __init__(self, snapshot: RecoverySnapshot | None = None):
        snapshot = snapshot or RecoverySnapshot()
        self.metadata = snapshot.metadata
        self.chunks = dict(snapshot.chunks)
        self.videos = list(snapshot.videos)
        self.created_at = snapshot.created_at
        self.stats = ScanStats()

    def add(self, frame: Frame) -> str:
        if self.metadata is None:
            self.metadata = frame.metadata
        elif frame.metadata.session_id != self.metadata.session_id:
            self.stats.foreign += 1
            return "foreign"
        elif frame.metadata != self.metadata:
            raise MetadataConflictError("同一文件标识出现不一致的元数据")
        previous = self.chunks.get(frame.index)
        if previous is not None:
            if previous != frame.chunk:
                raise ChunkConflictError(f"分片 {frame.index + 1} 出现内容冲突")
            self.stats.duplicates += 1
            return "duplicate"
        self.chunks[frame.index] = frame.chunk
        self.stats.added += 1
        return "added"

    @property
    def complete(self) -> bool:
        return self.metadata is not None and len(self.chunks) == self.metadata.total

    @property
    def missing(self) -> list[int]:
        if self.metadata is None:
            return []
        return [i for i in range(self.metadata.total) if i not in self.chunks]

    def snapshot(self) -> RecoverySnapshot:
        return RecoverySnapshot(self.metadata, dict(self.chunks), list(self.videos), self.created_at)

