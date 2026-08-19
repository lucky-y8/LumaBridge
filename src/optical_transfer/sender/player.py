from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QKeyEvent, QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QSizePolicy, QVBoxLayout

from .qr_generator import make_qr_png


class QRPlayerDialog(QDialog):
    def __init__(self, payloads: list[str], filename: str, size: int, digest: str,
                 fps: float, loops: int = 0, countdown: bool = True, parent=None):
        super().__init__(parent)
        self.payloads, self.filename, self.size, self.digest = payloads, filename, size, digest
        self.index, self.round_number, self.completed_rounds = 0, 1, 0
        self.paused, self.loop_limit = False, loops
        self.countdown_value = 3 if countdown else 0
        self._pixmaps: dict[int, QPixmap] = {}
        self.setWindowTitle("LumaBridge 动态二维码播放")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setStyleSheet("background:white;color:black")
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 10, 16, 10); layout.setSpacing(6)
        self.qr = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        # Ignore the pixmap size hint so a dense QR cannot squeeze the footer off-screen.
        # 忽略图片尺寸建议，避免高密度二维码把底部文字挤出屏幕。
        self.qr.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.qr.setMinimumSize(0, 0)
        self.status = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        status_font = self.status.font()
        status_font.setPixelSize(16)
        self.status.setFont(status_font)
        footer_height = self.status.fontMetrics().lineSpacing() * 4 + 12
        self.status.setFixedHeight(footer_height)
        self.status.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.countdown = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.countdown.setStyleSheet("font-size:96px;font-weight:bold")
        layout.addWidget(self.qr, 1); layout.addWidget(self.countdown); layout.addWidget(self.status)
        self.timer = QTimer(self, interval=max(125, round(1000 / fps)))
        self.timer.timeout.connect(self.advance)
        if self.countdown_value:
            self.countdown_timer = QTimer(self, interval=1000)
            self.countdown_timer.timeout.connect(self._countdown_tick)
        else: self.countdown_timer = None

    def start(self) -> None:
        self.showFullScreen()
        if self.countdown_timer:
            self.countdown.setText(str(self.countdown_value)); self.qr.hide()
            self.countdown_timer.start()
        else:
            self.countdown.hide(); self.show_current(); self.timer.start()

    def _countdown_tick(self) -> None:
        self.countdown_value -= 1
        if self.countdown_value:
            self.countdown.setText(str(self.countdown_value)); return
        self.countdown_timer.stop(); self.countdown.hide(); self.qr.show()
        self.show_current(); self.timer.start()

    def _pixmap(self, index: int) -> QPixmap:
        if index not in self._pixmaps:
            image = QImage.fromData(make_qr_png(self.payloads[index]), "PNG")
            self._pixmaps[index] = QPixmap.fromImage(image)
            if len(self._pixmaps) > 3:
                self._pixmaps.pop(next(iter(self._pixmaps)))
        return self._pixmaps[index]

    def show_current(self) -> None:
        state = "已暂停" if self.paused else "播放中"
        available_text_width = max(100, self.width() - 48)
        filename_line = self.status.fontMetrics().elidedText(
            f"{self.filename} · {self.size} bytes", Qt.TextElideMode.ElideMiddle, available_text_width
        )
        self.status.setText(f"{filename_line}\n第 {self.round_number} 轮 · 分片 {self.index + 1}/{len(self.payloads)} · {state}\nSHA-256: {self.digest[:16]}…{self.digest[-8:]}\nEsc 退出 · 空格 暂停/继续 · ←/→ 切换分片")
        self.layout().activate()
        self._fit_pixmap()

    def _fit_pixmap(self) -> None:
        """Fit the QR into the area actually assigned above the footer.

        将二维码限制在 Qt 为底部文字上方实际分配的区域内。
        """
        if not self.qr.isVisible():
            return
        area = self.qr.contentsRect()
        available = min(area.width(), area.height())
        if available <= 0:
            return
        pixmap = self._pixmap(self.index).scaled(
            available, available, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.qr.setPixmap(pixmap)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not self.countdown.isVisible():
            QTimer.singleShot(0, self.show_current)

    def advance(self) -> None:
        if self.paused: return
        self.index += 1
        if self.index >= len(self.payloads):
            self.index = 0; self.completed_rounds += 1; self.round_number += 1
            if self.loop_limit and self.completed_rounds >= self.loop_limit:
                self.accept(); return
        self.show_current()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape: self.reject()
        elif event.key() == Qt.Key.Key_Space:
            self.paused = not self.paused; self.show_current()
        elif event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            self.paused = True
            self.index = (self.index + (-1 if event.key() == Qt.Key.Key_Left else 1)) % len(self.payloads)
            self.show_current()
        else: super().keyPressEvent(event)
