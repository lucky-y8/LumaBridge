#!/usr/bin/env python3
"""Recover a file from a phone video of qr_sender.py.

从拍摄 qr_sender.py 的手机录像中恢复文件。
"""

import argparse
import base64
import hashlib
import os
import sys
import zlib

import cv2
import zxingcpp


PROTOCOL = "QRF1"


def b64_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def parse_payload(text: str):
    fields = text.split("|", 8)
    if len(fields) != 9 or fields[0] != PROTOCOL:
        return None

    _, session_id, index, total, file_size, digest, crc32, encoded_name, encoded_data = fields
    try:
        chunk = b64_decode(encoded_data)
        if f"{zlib.crc32(chunk) & 0xffffffff:08x}" != crc32.lower():
            return None
        filename = b64_decode(encoded_name).decode("utf-8")
        return {
            "session_id": session_id,
            "index": int(index),
            "total": int(total),
            "file_size": int(file_size),
            "digest": digest.lower(),
            "filename": filename,
            "chunk": chunk,
        }
    except (ValueError, UnicodeDecodeError, base64.binascii.Error):
        return None


def safe_filename(name: str) -> str:
    name = os.path.basename(name.replace("\\", "/"))
    return name or "restored.bin"


def decode_video(video_path: str, attempts_per_second: float):
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    sample_every = max(1, round(fps / attempts_per_second))
    chunks = {}
    metadata = None
    frame_number = 0
    last_report = -1

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frame_number += 1
        if frame_number % sample_every:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        results = zxingcpp.read_barcodes(gray)
        for result in results:
            item = parse_payload(result.text)
            if item is None:
                continue
            if metadata is None:
                metadata = {key: item[key] for key in (
                    "session_id", "total", "file_size", "digest", "filename"
                )}
            if item["session_id"] != metadata["session_id"]:
                continue
            if not 0 <= item["index"] < metadata["total"]:
                continue
            previous = chunks.get(item["index"])
            if previous is not None and previous != item["chunk"]:
                raise RuntimeError(f"分片 {item['index']} 出现冲突")
            chunks[item["index"]] = item["chunk"]

        if metadata:
            percent = len(chunks) * 100 // metadata["total"]
            if percent != last_report and (percent % 2 == 0 or len(chunks) == metadata["total"]):
                print(f"已取得 {len(chunks)}/{metadata['total']} 个分片（{percent}%）")
                last_report = percent

    capture.release()
    return metadata, chunks, frame_count, fps


def main():
    parser = argparse.ArgumentParser(description="从动态二维码录像恢复文件")
    parser.add_argument("video", help="手机录像文件，例如 qr_video.mp4")
    parser.add_argument("-o", "--output", help="输出文件名；默认 restored_原文件名")
    parser.add_argument(
        "--attempts-per-second",
        type=float,
        default=12.0,
        help="每秒尝试识别的录像帧数，默认12；漏帧时可提高到20",
    )
    args = parser.parse_args()

    metadata, chunks, frame_count, fps = decode_video(args.video, args.attempts_per_second)
    if metadata is None:
        print("失败：视频中没有识别到本工具生成的二维码。", file=sys.stderr)
        print("请检查清晰度、对焦、反光、拍摄角度，或提高 --attempts-per-second。", file=sys.stderr)
        raise SystemExit(2)

    missing = [index for index in range(metadata["total"]) if index not in chunks]
    if missing:
        preview = ", ".join(str(index + 1) for index in missing[:30])
        suffix = " ..." if len(missing) > 30 else ""
        print(f"恢复未完成：缺少 {len(missing)} 个分片。", file=sys.stderr)
        print(f"缺少的分片编号（从1开始）：{preview}{suffix}", file=sys.stderr)
        print("请补录一个完整循环后重新识别；也可以把多段视频先合并。", file=sys.stderr)
        raise SystemExit(3)

    file_data = b"".join(chunks[index] for index in range(metadata["total"]))
    file_data = file_data[: metadata["file_size"]]
    actual_digest = hashlib.sha256(file_data).hexdigest()
    if len(file_data) != metadata["file_size"] or actual_digest != metadata["digest"]:
        print("失败：最终文件的大小或 SHA-256 不一致。", file=sys.stderr)
        raise SystemExit(4)

    output = args.output or f"restored_{safe_filename(metadata['filename'])}"
    if os.path.exists(output):
        print(f"失败：输出文件已存在，不会覆盖：{output}", file=sys.stderr)
        raise SystemExit(5)
    with open(output, "wb") as file_handle:
        file_handle.write(file_data)

    print(f"恢复成功：{output}")
    print(f"文件大小：{len(file_data)} bytes")
    print(f"SHA-256：{actual_digest}")
    print(f"视频信息：约 {frame_count} 帧，{fps:.2f} FPS")


if __name__ == "__main__":
    main()
