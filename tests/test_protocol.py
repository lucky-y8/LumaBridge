import hashlib
import zlib

import pytest

from optical_transfer.models import FileMetadata, Frame
from optical_transfer.protocol import CrcError, ProtocolError, b64_decode, b64_encode, encode_frame, parse_frame


def frame(data=b"hello", filename="中文 file.bin"):
    digest = hashlib.sha256(data).hexdigest()
    meta = FileMetadata(digest[:16], 1, len(data), digest, filename)
    return Frame(meta, 0, f"{zlib.crc32(data) & 0xFFFFFFFF:08x}", data)


def test_urlsafe_base64_roundtrip():
    raw = bytes(range(256))
    assert b64_decode(b64_encode(raw)) == raw
    assert "=" not in b64_encode(raw)


def test_qrf1_roundtrip_with_unicode_filename():
    original = frame()
    assert parse_frame(encode_frame(original)) == original


def test_crc_error_is_rejected():
    payload = encode_frame(frame()).split("|")
    payload[6] = "00000000"
    with pytest.raises(CrcError): parse_frame("|".join(payload))


@pytest.mark.parametrize("payload", ["", "QRF2|x", "QRF1|too|short", "QRF1|a|0|1|0|b|c|d|e"])
def test_malformed_payload_is_rejected(payload):
    with pytest.raises(ProtocolError): parse_frame(payload)


def test_empty_file_frame():
    assert parse_frame(encode_frame(frame(b"", "empty.txt"))).chunk == b""

