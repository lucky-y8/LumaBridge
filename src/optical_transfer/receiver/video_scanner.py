from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..protocol import CrcError, ProtocolError, parse_frame
from .collector import ChunkCollector

ProgressCallback = Callable[[dict[str, Any]], None]


class ScanCancelled(RuntimeError):
    pass


class VideoScanner:
    """Scan incrementally without loading a complete video into memory.

    增量扫描视频，始终不会把完整视频一次性载入内存。
    """

    def __init__(self, collector: ChunkCollector, attempts_per_second: float = 12.0):
        if not 5 <= attempts_per_second <= 30:
            raise ValueError("每秒识别次数必须在 5～30 之间")
        self.collector = collector
        self.attempts_per_second = attempts_per_second
        self._cancel = threading.Event()
        self._pause = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def set_paused(self, paused: bool) -> None:
        if paused: self._pause.set()
        else: self._pause.clear()

    def _wait_if_paused(self) -> None:
        while self._pause.is_set() and not self._cancel.is_set():
            time.sleep(0.05)

    def scan(self, path: str, callback: ProgressCallback | None = None) -> dict[str, Any]:
        try:
            import cv2
            import zxingcpp
        except ImportError as exc:
            raise RuntimeError("缺少 OpenCV 或 zxing-cpp 依赖") from exc
        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            raise RuntimeError(f"无法打开视频：{path}")
        started = time.monotonic()
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        sample_every = max(1, round(fps / self.attempts_per_second))
        attempted = decoded = invalid = crc_errors = 0
        added_before = self.collector.stats.added
        duplicates_before = self.collector.stats.duplicates
        foreign_before = self.collector.stats.foreign
        frame_number = 0
        last_update = 0.0
        try:
            while True:
                if self._cancel.is_set(): raise ScanCancelled("用户已取消扫描")
                self._wait_if_paused()
                if self._cancel.is_set(): raise ScanCancelled("用户已取消扫描")
                ok = capture.grab()
                if not ok: break
                frame_number += 1
                if frame_number % sample_every: continue
                ok, frame = capture.retrieve()
                if not ok: continue
                attempted += 1
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                for result in zxingcpp.read_barcodes(gray):
                    text = result.text
                    if not text.startswith("QRF1|"): continue
                    decoded += 1
                    try:
                        item = parse_frame(text)
                        self.collector.add(item)
                    except CrcError:
                        crc_errors += 1
                    except ProtocolError:
                        invalid += 1
                now = time.monotonic()
                if callback and (now - last_update >= 0.2 or (total_frames and frame_number >= total_frames)):
                    ratio = min(1.0, frame_number / total_frames) if total_frames else 0.0
                    elapsed = now - started
                    callback({
                        "path": path, "frame": frame_number, "total_frames": total_frames,
                        "seconds": frame_number / fps, "duration": total_frames / fps if total_frames else 0,
                        "ratio": ratio, "attempted": attempted, "decoded": decoded,
                        "added": self.collector.stats.added - added_before,
                        "duplicates": self.collector.stats.duplicates - duplicates_before,
                        "foreign": self.collector.stats.foreign - foreign_before,
                        "crc_errors": crc_errors, "invalid": invalid, "elapsed": elapsed,
                        "eta": elapsed * (1 - ratio) / ratio if ratio else None,
                    })
                    last_update = now
        finally:
            capture.release()
        return {
            "path": str(Path(path).resolve()), "name": Path(path).name, "fps": fps,
            "frame_count": total_frames, "width": width, "height": height,
            "duration": total_frames / fps if total_frames else 0, "attempted": attempted,
            "decoded": decoded, "added": self.collector.stats.added - added_before,
            "duplicates": self.collector.stats.duplicates - duplicates_before,
            "foreign": self.collector.stats.foreign - foreign_before,
            "crc_errors": crc_errors, "invalid": invalid, "status": "扫描完成",
        }
