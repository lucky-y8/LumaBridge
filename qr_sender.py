#!/usr/bin/env python3
"""Display a file as a looping stream of QR-code chunks.

把文件显示为循环播放的二维码分片流。
"""

import argparse
import base64
import hashlib
import math
import os
import tkinter as tk
import zlib

import qrcode
from PIL import ImageTk
from qrcode.constants import ERROR_CORRECT_M


PROTOCOL = "QRF1"


def b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def build_payloads(path: str, chunk_size: int):
    with open(path, "rb") as file_handle:
        file_data = file_handle.read()

    digest = hashlib.sha256(file_data).hexdigest()
    session_id = digest[:16]
    filename = os.path.basename(path)
    encoded_name = b64_encode(filename.encode("utf-8"))
    total = max(1, math.ceil(len(file_data) / chunk_size))
    payloads = []

    for index in range(total):
        chunk = file_data[index * chunk_size : (index + 1) * chunk_size]
        crc32 = f"{zlib.crc32(chunk) & 0xffffffff:08x}"
        payloads.append(
            "|".join(
                (
                    PROTOCOL,
                    session_id,
                    str(index),
                    str(total),
                    str(len(file_data)),
                    digest,
                    crc32,
                    encoded_name,
                    b64_encode(chunk),
                )
            )
        )

    return payloads, filename, len(file_data), digest


class QRPlayer:
    def __init__(self, payloads, filename: str, size: int, digest: str, fps: float):
        self.payloads = payloads
        self.filename = filename
        self.size = size
        self.digest = digest
        self.delay_ms = max(100, round(1000 / fps))
        self.index = 0
        self.round_number = 1
        self.paused = False

        self.root = tk.Tk()
        self.root.title("动态二维码文件传输")
        self.root.configure(bg="white")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self.root.bind("<space>", self.toggle_pause)
        self.root.bind("<Right>", lambda _event: self.step(1))
        self.root.bind("<Left>", lambda _event: self.step(-1))

        self.image_label = tk.Label(self.root, bg="white")
        self.image_label.pack(expand=True)
        self.status_label = tk.Label(
            self.root,
            bg="white",
            fg="black",
            font=("Arial", 18),
            justify="center",
        )
        self.status_label.pack(pady=(0, 20))

    def make_image(self, payload: str):
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=7,
            border=4,
        )
        qr.add_data(payload, optimize=0)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").convert("RGB")

    def show_current(self):
        image = self.make_image(self.payloads[self.index])
        self.tk_image = ImageTk.PhotoImage(image)
        self.image_label.configure(image=self.tk_image)
        state = "已暂停" if self.paused else "播放中"
        self.status_label.configure(
            text=(
                f"{self.filename}  {self.size} bytes\n"
                f"第 {self.round_number} 轮 · 分片 {self.index + 1}/{len(self.payloads)} · {state}\n"
                f"SHA-256: {self.digest}\n"
                "Esc退出 · 空格暂停 · 左右键切换"
            )
        )

    def advance(self):
        if not self.paused:
            self.index += 1
            if self.index >= len(self.payloads):
                self.index = 0
                self.round_number += 1
            self.show_current()
        self.root.after(self.delay_ms, self.advance)

    def toggle_pause(self, _event=None):
        self.paused = not self.paused
        self.show_current()

    def step(self, amount: int):
        self.paused = True
        self.index = (self.index + amount) % len(self.payloads)
        self.show_current()

    def run(self):
        self.show_current()
        self.root.after(self.delay_ms, self.advance)
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="把文件循环显示为动态二维码")
    parser.add_argument("file", help="需要传输的文件")
    parser.add_argument("--chunk-size", type=int, default=700, help="每帧原始字节数，默认700")
    parser.add_argument("--fps", type=float, default=3.0, help="每秒二维码数量，默认3")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        parser.error(f"文件不存在：{args.file}")
    if not 200 <= args.chunk_size <= 1000:
        parser.error("--chunk-size 建议设置为200到1000")
    if not 0.5 <= args.fps <= 8:
        parser.error("--fps 建议设置为0.5到8")

    payloads, filename, size, digest = build_payloads(args.file, args.chunk_size)
    print(f"文件：{filename}")
    print(f"大小：{size} bytes")
    print(f"分片：{len(payloads)}")
    print(f"SHA-256：{digest}")
    print("建议手机横屏、1080p/60fps录像，并至少录制两个完整循环。")
    QRPlayer(payloads, filename, size, digest, args.fps).run()


if __name__ == "__main__":
    main()
