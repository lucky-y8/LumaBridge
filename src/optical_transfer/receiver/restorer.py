from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from .collector import ChunkCollector


class RestoreError(RuntimeError):
    pass


def safe_filename(name: str) -> str:
    clean = Path(name.replace("\\", "/")).name.strip().rstrip(". ")
    return clean or "restored.bin"


def assemble(collector: ChunkCollector) -> bytes:
    if not collector.complete or collector.metadata is None:
        raise RestoreError("分片尚未收齐")
    data = b"".join(collector.chunks[index] for index in range(collector.metadata.total))
    data = data[:collector.metadata.file_size]
    if len(data) != collector.metadata.file_size:
        raise RestoreError("恢复文件大小不一致")
    if hashlib.sha256(data).hexdigest() != collector.metadata.digest:
        raise RestoreError("恢复文件 SHA-256 不一致")
    return data


def restore_to(collector: ChunkCollector, output: str | os.PathLike[str], overwrite: bool = False) -> Path:
    target = Path(output)
    if target.exists() and not overwrite:
        raise FileExistsError(f"目标文件已存在：{target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    data = assemble(collector)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return target

