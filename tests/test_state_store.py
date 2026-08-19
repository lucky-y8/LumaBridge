import hashlib
import json
import zlib

import pytest

from optical_transfer.models import FileMetadata, RecoverySnapshot
from optical_transfer.receiver.state_store import StateError, load_state, save_state


def test_state_roundtrip_and_unicode(tmp_path):
    data = b"partial"
    digest = hashlib.sha256(data + b"later").hexdigest()
    meta = FileMetadata(digest[:16], 2, len(data) + 5, digest, "测试 文件.7z")
    snapshot = RecoverySnapshot(meta, {0: data}, [{"path": "a.mp4", "status": "扫描完成"}])
    path = tmp_path / "任务.qrstate"
    save_state(path, snapshot)
    loaded = load_state(path)
    assert loaded.metadata == meta
    assert loaded.chunks == {0: data}
    assert loaded.videos[0]["path"] == "a.mp4"
    document = json.loads(path.read_text("utf-8"))
    assert document["missing"] == [1]
    assert document["chunks"]["0"]["crc32"] == f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"


def test_corrupt_state_is_rejected(tmp_path):
    path = tmp_path / "bad.qrstate"; path.write_text("not json", encoding="utf-8")
    with pytest.raises(StateError): load_state(path)


def test_tampered_chunk_is_rejected(tmp_path):
    digest = hashlib.sha256(b"a").hexdigest(); meta = FileMetadata(digest[:16], 1, 1, digest, "a")
    path = tmp_path / "state.qrstate"; save_state(path, RecoverySnapshot(meta, {0: b"a"}))
    doc = json.loads(path.read_text("utf-8")); doc["chunks"]["0"]["crc32"] = "00000000"
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(StateError): load_state(path)

