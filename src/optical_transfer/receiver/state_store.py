from __future__ import annotations

import base64
import json
import os
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path

from ..models import FileMetadata, RecoverySnapshot

STATE_FORMAT = "LumaBridge-QRF1-State"
STATE_VERSION = 1


class StateError(RuntimeError):
    pass


def save_state(path: str | os.PathLike[str], snapshot: RecoverySnapshot) -> None:
    target = Path(path)
    now = datetime.now(timezone.utc).isoformat()
    created = snapshot.created_at or now
    meta = snapshot.metadata
    document = {
        "format": STATE_FORMAT, "version": STATE_VERSION, "created_at": created, "updated_at": now,
        "metadata": None if meta is None else {
            "session_id": meta.session_id, "total": meta.total, "file_size": meta.file_size,
            "digest": meta.digest, "filename": meta.filename,
        },
        "chunks": {str(i): {
            "data": base64.b64encode(data).decode("ascii"),
            "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
        } for i, data in sorted(snapshot.chunks.items())},
        "missing": [] if meta is None else [i for i in range(meta.total) if i not in snapshot.chunks],
        "videos": snapshot.videos,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, separators=(",", ":"))
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temp_name, target)
    except BaseException:
        try: os.unlink(temp_name)
        except FileNotFoundError: pass
        raise


def load_state(path: str | os.PathLike[str]) -> RecoverySnapshot:
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            doc = json.load(stream)
        if doc.get("format") != STATE_FORMAT or doc.get("version") != STATE_VERSION:
            raise StateError("恢复状态版本不兼容")
        raw_meta = doc.get("metadata")
        meta = None if raw_meta is None else FileMetadata(
            str(raw_meta["session_id"]), int(raw_meta["total"]), int(raw_meta["file_size"]),
            str(raw_meta["digest"]), str(raw_meta["filename"]),
        )
        chunks = {}
        for index_text, item in doc.get("chunks", {}).items():
            data = base64.b64decode(item["data"], validate=True)
            if f"{zlib.crc32(data) & 0xFFFFFFFF:08x}" != str(item["crc32"]).lower():
                raise StateError("恢复状态分片 CRC32 校验失败")
            chunks[int(index_text)] = data
        if meta and (any(i < 0 or i >= meta.total for i in chunks) or len(chunks) > meta.total):
            raise StateError("恢复状态包含越界分片")
        return RecoverySnapshot(meta, chunks, list(doc.get("videos", [])), str(doc.get("created_at", "")), str(doc.get("updated_at", "")))
    except StateError:
        raise
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise StateError("恢复状态文件损坏或无法读取") from exc
