from __future__ import annotations

import base64
import binascii
import re
import zlib

from .models import FileMetadata, Frame

PROTOCOL = "QRF1"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_HEX16 = re.compile(r"[0-9a-f]{16}\Z")
_HEX8 = re.compile(r"[0-9a-f]{8}\Z")


class ProtocolError(ValueError):
    """Raised when a QR payload violates the QRF1 contract.

    当二维码载荷违反 QRF1 协议时抛出。
    """


class CrcError(ProtocolError):
    pass


def b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64_decode(text: str) -> bytes:
    if not isinstance(text, str) or "=" in text or not re.fullmatch(r"[A-Za-z0-9_-]*", text):
        raise ProtocolError("Base64 字段格式无效")
    try:
        return base64.b64decode(text + "=" * (-len(text) % 4), altchars=b"-_", validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ProtocolError("Base64 字段无法解码") from exc


def encode_frame(frame: Frame) -> str:
    meta = frame.metadata
    crc = f"{zlib.crc32(frame.chunk) & 0xFFFFFFFF:08x}"
    if frame.crc32.lower() != crc:
        raise CrcError("待编码分片的 CRC32 不一致")
    return "|".join((
        PROTOCOL, meta.session_id, str(frame.index), str(meta.total),
        str(meta.file_size), meta.digest, crc,
        b64_encode(meta.filename.encode("utf-8")), b64_encode(frame.chunk),
    ))


def parse_frame(text: str) -> Frame:
    fields = text.split("|")
    if len(fields) != 9 or fields[0] != PROTOCOL:
        raise ProtocolError("不是有效的 QRF1 二维码")
    _, session, index_text, total_text, size_text, digest, crc, name64, chunk64 = fields
    digest, crc, session = digest.lower(), crc.lower(), session.lower()
    if not _HEX64.fullmatch(digest) or not _HEX16.fullmatch(session) or session != digest[:16]:
        raise ProtocolError("文件标识或 SHA-256 格式无效")
    if not _HEX8.fullmatch(crc):
        raise ProtocolError("CRC32 格式无效")
    try:
        index, total, file_size = int(index_text), int(total_text), int(size_text)
    except ValueError as exc:
        raise ProtocolError("分片数字段格式无效") from exc
    if total < 1 or file_size < 0 or not 0 <= index < total:
        raise ProtocolError("分片数字段超出范围")
    try:
        filename = b64_decode(name64).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProtocolError("文件名不是 UTF-8") from exc
    if not filename or "\0" in filename:
        raise ProtocolError("文件名无效")
    chunk = b64_decode(chunk64)
    if f"{zlib.crc32(chunk) & 0xFFFFFFFF:08x}" != crc:
        raise CrcError("分片 CRC32 校验失败")
    if file_size == 0 and (total != 1 or chunk):
        raise ProtocolError("空文件元数据不一致")
    if file_size > 0 and not chunk:
        raise ProtocolError("非空文件不能包含空分片")
    return Frame(FileMetadata(session, total, file_size, digest, filename), index, crc, chunk)
