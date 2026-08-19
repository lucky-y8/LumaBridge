import hashlib
import zlib

import pytest

from optical_transfer.models import FileMetadata, Frame
from optical_transfer.receiver.collector import ChunkCollector, ChunkConflictError
from optical_transfer.receiver.restorer import RestoreError, assemble, restore_to
from optical_transfer.sender.chunker import build_payloads
from optical_transfer.protocol import parse_frame


def make_frame(data: bytes, index=0, total=1, all_data=None, session=None):
    complete = data if all_data is None else all_data
    digest = hashlib.sha256(complete).hexdigest()
    meta = FileMetadata(session or digest[:16], total, len(complete), digest, "a.bin")
    return Frame(meta, index, f"{zlib.crc32(data) & 0xFFFFFFFF:08x}", data)


def test_chunker_and_collector_roundtrip(tmp_path):
    source = tmp_path / "中文 源.bin"
    content = bytes(range(256)) * 9 + b"last"
    source.write_bytes(content)
    meta, payloads = build_payloads(source, 700)
    collector = ChunkCollector()
    for payload in reversed(payloads): collector.add(parse_frame(payload))
    assert collector.complete
    assert assemble(collector) == content
    output = tmp_path / "result.bin"
    restore_to(collector, output)
    assert output.read_bytes() == content
    assert meta.filename == source.name


def test_duplicate_and_conflict_detection():
    collector = ChunkCollector()
    item = make_frame(b"good")
    assert collector.add(item) == "added"
    assert collector.add(item) == "duplicate"
    changed = Frame(item.metadata, item.index, f"{zlib.crc32(b'evil') & 0xFFFFFFFF:08x}", b"evil")
    with pytest.raises(ChunkConflictError): collector.add(changed)


def test_foreign_session_is_ignored():
    collector = ChunkCollector(); collector.add(make_frame(b"one"))
    foreign = make_frame(b"two")
    assert collector.add(foreign) == "foreign"
    assert len(collector.chunks) == 1


def test_incomplete_and_hash_mismatch_are_not_restored():
    content = b"abcdef"
    digest = hashlib.sha256(content).hexdigest()
    meta = FileMetadata(digest[:16], 2, len(content), digest, "x")
    collector = ChunkCollector(); collector.add(Frame(meta, 0, f"{zlib.crc32(b'abc') & 0xFFFFFFFF:08x}", b"abc"))
    with pytest.raises(RestoreError): assemble(collector)
    collector.add(Frame(meta, 1, f"{zlib.crc32(b'xxx') & 0xFFFFFFFF:08x}", b"xxx"))
    with pytest.raises(RestoreError): assemble(collector)


def test_existing_output_is_not_silently_overwritten(tmp_path):
    collector = ChunkCollector(); collector.add(make_frame(b"ok"))
    output = tmp_path / "exists.bin"; output.write_bytes(b"old")
    with pytest.raises(FileExistsError): restore_to(collector, output)
    assert output.read_bytes() == b"old"

