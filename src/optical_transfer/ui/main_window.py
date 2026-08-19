from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent, QDesktopServices, QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QProgressBar, QScrollArea, QSizePolicy, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from ..receiver.collector import ChunkCollector, ChunkConflictError, MetadataConflictError
from ..receiver.restorer import restore_to, safe_filename
from ..receiver.state_store import StateError, load_state, save_state
from ..receiver.video_scanner import ScanCancelled, VideoScanner
from ..sender.chunker import analyze_file, build_payloads
from ..sender.player import QRPlayerDialog
from .theme import DARK_STYLESHEET, LIGHT_STYLESHEET


def human_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB": return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    return f"{value} B"


def clock(seconds: float | None) -> str:
    if seconds is None: return "--:--"
    seconds = max(0, int(seconds)); return f"{seconds // 60:02d}:{seconds % 60:02d}"


def add_page_header(layout: QVBoxLayout, eyebrow: str, title: str, subtitle: str) -> None:
    eye = QLabel(eyebrow.upper()); eye.setObjectName("eyebrow")
    heading = QLabel(title); heading.setObjectName("pageTitle")
    detail = QLabel(subtitle); detail.setObjectName("pageSubtitle"); detail.setWordWrap(True)
    layout.addWidget(eye); layout.addWidget(heading); layout.addWidget(detail)


def scrollable_page(page: QWidget) -> QScrollArea:
    """Wrap a workspace page so controls remain reachable on short screens.

    为工作区页面增加滚动支持，确保低高度屏幕仍能访问全部控件。
    """
    area = QScrollArea(); area.setObjectName("workspaceScroll"); area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame); area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(page); return area


class ScanWorker(QObject):
    progress = Signal(dict); video_done = Signal(int, dict); finished = Signal(); failed = Signal(str)

    def __init__(self, entries: list[tuple[int, str]], collector: ChunkCollector, attempts: float):
        super().__init__(); self.entries = entries; self.collector = collector
        self.scanner = VideoScanner(collector, attempts)

    @Slot()
    def run(self) -> None:
        try:
            for row, path in self.entries:
                try:
                    result = self.scanner.scan(path, self.progress.emit)
                except ScanCancelled:
                    raise
                except (ChunkConflictError, MetadataConflictError):
                    raise
                except Exception as exc:
                    logging.exception("跳过无法扫描的视频")
                    result = {"path": path, "name": Path(path).name, "status": f"已跳过：{exc}", "added": 0, "duplicates": 0}
                self.collector.videos.append(result); self.video_done.emit(row, result)
            self.finished.emit()
        except ScanCancelled: self.finished.emit()
        except Exception as exc:
            logging.exception("扫描任务失败"); self.failed.emit(str(exc))


class AnalyzeWorker(QObject):
    done = Signal(str, int, object); failed = Signal(str, int, str)

    def __init__(self, path: str, chunk_size: int):
        super().__init__(); self.path = path; self.chunk_size = chunk_size

    @Slot()
    def run(self) -> None:
        try: self.done.emit(self.path, self.chunk_size, analyze_file(self.path, self.chunk_size))
        except Exception as exc: self.failed.emit(self.path, self.chunk_size, str(exc))


class SendPage(QWidget):
    log = Signal(str)
    MODES = {"稳定": (500, 2.0), "标准（推荐）": (700, 3.0), "快速": (800, 4.0)}

    def __init__(self):
        super().__init__(); self.path = ""; self.meta = None; self.analysis_thread = None; self.analysis_worker = None; self.analysis_pending = False; self.setAcceptDrops(True)
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(13)
        add_page_header(root, "SEND · OPTICAL STREAM", "发送文件", "把任意文件编码成动态二维码；手机只需录制屏幕，无需连接任何网络。")
        recording_tip = QLabel("拍摄建议  ·  建议手机横屏、1080p/60fps录像，并至少录制两个完整循环。")
        recording_tip.setObjectName("tipPanel"); recording_tip.setWordWrap(True); root.addWidget(recording_tip)
        choose_card = QFrame(); choose_card.setObjectName("card"); choose_box = QVBoxLayout(choose_card); choose_box.setContentsMargins(17, 14, 17, 15); choose_box.setSpacing(8)
        choose_title = QLabel("选择源文件"); choose_title.setObjectName("cardTitle")
        choose_hint = QLabel("支持拖放任意单个文件到此窗口"); choose_hint.setObjectName("muted")
        choose_box.addWidget(choose_title); choose_box.addWidget(choose_hint)
        choose = QHBoxLayout(); self.path_label = QLabel("尚未选择文件"); self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.path_label.setObjectName("pathBox"); button = QPushButton("浏览文件…"); button.clicked.connect(self.choose_file)
        choose.addWidget(self.path_label, 1); choose.addWidget(button); choose_box.addLayout(choose); root.addWidget(choose_card)
        settings = QGroupBox("传输参数"); form = QFormLayout(settings); form.setHorizontalSpacing(20); form.setVerticalSpacing(10)
        self.mode = QComboBox(); self.mode.addItems([*self.MODES, "自定义"]); self.mode.setCurrentText("标准（推荐）")
        self.chunk = QSpinBox(minimum=200, maximum=1000, value=700, suffix=" 字节")
        self.fps = QDoubleSpinBox(minimum=0.5, maximum=8, value=3, singleStep=0.5, suffix=" fps")
        self.loops = QComboBox(); self.loops.addItems(["无限循环", "1 次", "2 次", "3 次"]); self.loops.setCurrentText("2 次")
        self.countdown = QCheckBox("播放前 3 秒倒计时"); self.countdown.setChecked(True)
        self.reset_settings = QPushButton("恢复默认设置"); self.reset_settings.setObjectName("resetButton"); self.reset_settings.clicked.connect(self.reset_defaults)
        form.addRow("模式", self.mode); form.addRow("分片大小", self.chunk); form.addRow("播放速度", self.fps); form.addRow("循环次数", self.loops); form.addRow("", self.countdown); form.addRow("", self.reset_settings)
        self.mode.currentTextChanged.connect(self.apply_mode); self.chunk.valueChanged.connect(self.refresh); self.fps.valueChanged.connect(self.refresh)
        self.analysis_timer = QTimer(self, singleShot=True, interval=200); self.analysis_timer.timeout.connect(self._start_analysis)
        root.addWidget(settings)
        self.info = QLabel("选择文件后显示 SHA-256、分片数和预计时长。")
        self.info.setObjectName("infoPanel"); self.info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); root.addWidget(self.info)
        self.start_btn = QPushButton("开始全屏播放  →"); self.start_btn.setObjectName("primaryButton"); self.start_btn.setEnabled(False); self.start_btn.clicked.connect(self.play)
        root.addWidget(self.start_btn); root.addStretch()

    def reset_defaults(self) -> None:
        self.mode.setCurrentText("标准（推荐）"); self.chunk.setValue(700); self.fps.setValue(3.0)
        self.loops.setCurrentText("2 次"); self.countdown.setChecked(True); self.refresh()

    def apply_mode(self, name: str) -> None:
        if name in self.MODES:
            chunk, fps = self.MODES[name]; self.chunk.setValue(chunk); self.fps.setValue(fps)
            self.chunk.setEnabled(False); self.fps.setEnabled(False)
        else: self.chunk.setEnabled(True); self.fps.setEnabled(True)
        self.refresh()

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择要发送的文件")
        if path: self.set_file(path)

    def set_file(self, path: str) -> None:
        try:
            self.path = path; self.path_label.setText(path); self.refresh()
            if Path(path).stat().st_size > 10 * 1024 * 1024:
                QMessageBox.information(self, "大文件提示", "文件超过 10 MB，二维码传输可能需要很长时间。")
        except OSError as exc: QMessageBox.critical(self, "读取失败", str(exc))

    def refresh(self) -> None:
        if not self.path: return
        self.meta = None; self.start_btn.setEnabled(False); self.info.setText("正在后台计算文件 SHA-256 和分片信息…")
        self.analysis_timer.start()

    def _start_analysis(self) -> None:
        if not self.path: return
        if self.analysis_thread is not None:
            self.analysis_pending = True; return
        path, chunk_size = self.path, self.chunk.value()
        self.analysis_thread = QThread(self); self.analysis_worker = AnalyzeWorker(path, chunk_size); self.analysis_worker.moveToThread(self.analysis_thread)
        self.analysis_thread.started.connect(self.analysis_worker.run); self.analysis_worker.done.connect(self._analysis_done); self.analysis_worker.failed.connect(self._analysis_failed)
        self.analysis_worker.done.connect(self.analysis_thread.quit); self.analysis_worker.failed.connect(self.analysis_thread.quit); self.analysis_thread.finished.connect(self._analysis_cleanup)
        self.analysis_thread.start()

    @Slot(str, int, object)
    def _analysis_done(self, path: str, chunk_size: int, meta: object) -> None:
        if path != self.path or chunk_size != self.chunk.value():
            self.analysis_pending = True; return
        self.meta = meta
        duration = self.meta.total / self.fps.value()
        self.info.setText(f"文件名：{self.meta.filename}\n大小：{human_size(self.meta.file_size)}\nSHA-256：{self.meta.digest}\n分片：{self.meta.total} × {chunk_size} 字节\n单循环：约 {clock(duration)} · 推荐录像：约 {clock(duration * 2 + 6)}")
        self.start_btn.setEnabled(True); self.log.emit(f"已分析文件：{self.meta.filename}，{self.meta.total} 个分片")

    @Slot(str, int, str)
    def _analysis_failed(self, path: str, chunk_size: int, message: str) -> None:
        if path == self.path and chunk_size == self.chunk.value():
            self.start_btn.setEnabled(False); self.info.setText(f"分析失败：{message}")

    @Slot()
    def _analysis_cleanup(self) -> None:
        self.analysis_thread.deleteLater(); self.analysis_thread = None; self.analysis_worker = None
        if self.analysis_pending:
            self.analysis_pending = False; self.analysis_timer.start()

    def play(self) -> None:
        try:
            meta, payloads = build_payloads(self.path, self.chunk.value())
            loops = self.loops.currentIndex()
            dialog = QRPlayerDialog(payloads, meta.filename, meta.file_size, meta.digest, self.fps.value(), loops, self.countdown.isChecked(), self)
            self.log.emit("开始播放动态二维码"); dialog.start(); dialog.exec(); self.log.emit("二维码播放已停止")
        except Exception as exc: logging.exception("播放失败"); QMessageBox.critical(self, "无法播放", str(exc))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1: event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        path = event.mimeData().urls()[0].toLocalFile()
        if Path(path).is_file(): self.set_file(path)


class RecoverPage(QWidget):
    log = Signal(str)
    VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm"}

    def __init__(self):
        super().__init__(); self.setAcceptDrops(True); self.paths: list[str] = []; self.collector = ChunkCollector()
        self.thread = None; self.worker = None; self.state_path = ""; self.started_at = 0.0
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(11)
        add_page_header(root, "RECOVER · VERIFY · RESTORE", "恢复文件", "合并多段手机录像，自动去重；只有大小与 SHA-256 全部通过才允许保存。")
        queue_card = QFrame(); queue_card.setObjectName("card"); queue_box = QVBoxLayout(queue_card); queue_box.setContentsMargins(15, 12, 15, 14); queue_box.setSpacing(9)
        queue_head = QHBoxLayout(); queue_title_box = QVBoxLayout(); queue_title = QLabel("录像队列"); queue_title.setObjectName("cardTitle")
        queue_hint = QLabel("可按顺序扫描多段录像，并用补录视频补齐缺失分片"); queue_hint.setObjectName("muted")
        queue_title_box.addWidget(queue_title); queue_title_box.addWidget(queue_hint); queue_head.addLayout(queue_title_box); queue_head.addStretch()
        tools = QHBoxLayout()
        for text, slot in (("添加录像…", self.add_dialog), ("移除", self.remove), ("上移", lambda: self.move(-1)), ("下移", lambda: self.move(1)), ("加载状态…", self.load_state_dialog), ("保存状态…", self.save_state_dialog)):
            b = QPushButton(text); b.clicked.connect(slot); tools.addWidget(b)
        queue_box.addLayout(queue_head); queue_box.addLayout(tools)
        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["录像", "状态", "扫描进度", "本段新增"])
        self.table.setAlternatingRowColors(True); self.table.verticalHeader().setVisible(False); self.table.verticalHeader().setDefaultSectionSize(39)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.table.horizontalHeader().setStretchLastSection(True); queue_box.addWidget(self.table); root.addWidget(queue_card, 1)
        controls = QHBoxLayout(); self.attempts = QSpinBox(minimum=5, maximum=30, value=12, suffix=" 次/秒")
        self.reset_settings = QPushButton("恢复默认设置"); self.reset_settings.setObjectName("resetButton"); self.reset_settings.clicked.connect(self.reset_defaults)
        self.start = QPushButton("开始扫描"); self.pause = QPushButton("暂停"); self.cancel = QPushButton("取消")
        self.start.setObjectName("primaryButton"); self.cancel.setObjectName("dangerButton")
        self.pause.setEnabled(False); self.cancel.setEnabled(False); self.start.clicked.connect(self.start_scan); self.pause.clicked.connect(self.toggle_pause); self.cancel.clicked.connect(self.cancel_scan)
        controls.addWidget(QLabel("识别频率")); controls.addWidget(self.attempts); controls.addWidget(self.reset_settings); controls.addStretch(); controls.addWidget(self.start); controls.addWidget(self.pause); controls.addWidget(self.cancel); root.addLayout(controls)
        progress_card = QFrame(); progress_card.setObjectName("card"); progress_box = QVBoxLayout(progress_card); progress_box.setContentsMargins(16, 11, 16, 12); progress_box.setSpacing(6)
        self.video_progress = QProgressBar(); self.chunk_progress = QProgressBar(); self.video_progress.setTextVisible(False); self.chunk_progress.setTextVisible(False)
        self.video_percent = QLabel("0 %"); self.chunk_percent = QLabel("0 %"); self.video_percent.setObjectName("progressPercent"); self.chunk_percent.setObjectName("progressPercent")
        for percent in (self.video_percent, self.chunk_percent): percent.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); percent.setFixedWidth(64)
        video_label = QLabel("当前视频扫描进度"); video_label.setObjectName("muted"); chunk_label = QLabel("唯一分片收集进度"); chunk_label.setObjectName("muted")
        video_row = QHBoxLayout(); video_row.setSpacing(10); video_row.addWidget(self.video_progress, 1); video_row.addWidget(self.video_percent)
        chunk_row = QHBoxLayout(); chunk_row.setSpacing(10); chunk_row.addWidget(self.chunk_progress, 1); chunk_row.addWidget(self.chunk_percent)
        progress_box.addWidget(video_label); progress_box.addLayout(video_row); progress_box.addSpacing(3); progress_box.addWidget(chunk_label); progress_box.addLayout(chunk_row); root.addWidget(progress_card)
        self.status = QLabel("等待添加录像"); self.status.setObjectName("infoPanel"); self.status.setWordWrap(True); self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); root.addWidget(self.status)
        out = QHBoxLayout(); self.restore = QPushButton("恢复并保存文件…"); self.restore.setEnabled(False); self.restore.clicked.connect(self.restore_file)
        self.restore.setObjectName("primaryButton")
        self.copy_missing = QPushButton("复制缺失编号"); self.copy_missing.clicked.connect(self.copy_missing_numbers)
        out.addWidget(self.restore); out.addWidget(self.copy_missing); out.addStretch(); root.addLayout(out)

    def reset_defaults(self) -> None:
        if self.thread is None: self.attempts.setValue(12)

    def add_dialog(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "添加手机录像", filter="视频 (*.mp4 *.mov *.avi *.mkv *.m4v *.webm);;所有文件 (*)")
        self.add_paths(paths)

    def add_paths(self, paths: list[str]) -> None:
        existing = {os.path.normcase(os.path.abspath(p)) for p in self.paths}
        duplicate = False
        for path in paths:
            normalized = os.path.normcase(os.path.abspath(path))
            if normalized in existing: duplicate = True; continue
            if not Path(path).is_file(): continue
            existing.add(normalized); self.paths.append(path)
            row = self.table.rowCount(); self.table.insertRow(row)
            for col, value in enumerate((Path(path).name, "等待扫描", "0%", "—")): self.table.setItem(row, col, QTableWidgetItem(value))
        if duplicate: QMessageBox.information(self, "重复录像", "重复添加的录像已忽略。")
        self.start.setEnabled(bool(self.paths) and self.thread is None)

    def remove(self) -> None:
        row = self.table.currentRow()
        if row >= 0 and self.thread is None: self.table.removeRow(row); self.paths.pop(row)

    def move(self, offset: int) -> None:
        row = self.table.currentRow(); target = row + offset
        if self.thread is not None or row < 0 or not 0 <= target < len(self.paths): return
        self.paths[row], self.paths[target] = self.paths[target], self.paths[row]
        values = [[self.table.item(r, c).text() for c in range(4)] for r in (row, target)]
        for c in range(4): self.table.item(row, c).setText(values[1][c]); self.table.item(target, c).setText(values[0][c])
        self.table.selectRow(target)

    def start_scan(self) -> None:
        entries = [(row, path) for row, path in enumerate(self.paths)
                   if self.table.item(row, 1).text() != "扫描完成" and not self.table.item(row, 1).text().startswith("已跳过")]
        if not entries:
            QMessageBox.information(self, "没有待扫描录像", "请添加补录视频后继续。")
            return
        self.started_at = time.monotonic(); self.thread = QThread(self); self.worker = ScanWorker(entries, self.collector, self.attempts.value())
        self.worker.moveToThread(self.thread); self.thread.started.connect(self.worker.run); self.worker.progress.connect(self.on_progress)
        self.worker.video_done.connect(self.on_video_done); self.worker.finished.connect(self.on_finished); self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit); self.worker.failed.connect(self.thread.quit); self.thread.finished.connect(self.cleanup_thread)
        self.video_progress.setValue(0); self.video_percent.setText("0 %")
        self.start.setEnabled(False); self.pause.setEnabled(True); self.cancel.setEnabled(True); self.attempts.setEnabled(False); self.reset_settings.setEnabled(False)
        self.log.emit(f"开始扫描 {len(entries)} 个待处理录像"); self.thread.start()

    @Slot(dict)
    def on_progress(self, p: dict) -> None:
        ratio = p["ratio"]; video_value = round(ratio * 100); self.video_progress.setValue(video_value); self.video_percent.setText(f"{video_value} %")
        total = self.collector.metadata.total if self.collector.metadata else 0
        collected = len(self.collector.chunks); chunk_value = round(collected * 100 / total) if total else 0; self.chunk_progress.setValue(chunk_value); self.chunk_percent.setText(f"{chunk_value} %")
        self.status.setText(f"正在扫描：{Path(p['path']).name}\n视频 {clock(p['seconds'])}/{clock(p['duration'])}（{ratio * 100:.1f}%），帧 {p['frame']}/{p['total_frames']}\n唯一分片 {collected}/{total or '?'}，本段新增 {p['added']}，重复 {p['duplicates']}，二维码 {p['decoded']}，CRC 错误 {p['crc_errors']}，其他文件 {p['foreign']}\n已运行 {clock(time.monotonic() - self.started_at)}，本段预计剩余 {clock(p['eta'])}")
        for row, path in enumerate(self.paths):
            if os.path.normcase(path) == os.path.normcase(p["path"]):
                self.table.item(row, 1).setText("正在扫描"); self.table.item(row, 2).setText(f"{ratio * 100:.1f}%"); break

    @Slot(int, dict)
    def on_video_done(self, index: int, result: dict) -> None:
        if index < self.table.rowCount():
            status = result.get("status", "扫描完成")
            self.table.item(index, 1).setText(status); self.table.item(index, 2).setText("100%" if status == "扫描完成" else "—"); self.table.item(index, 3).setText(str(result["added"]))
            if status == "扫描完成": self.video_progress.setValue(100); self.video_percent.setText("100 %")
        self.log.emit(f"录像扫描完成：{result['name']}，新增 {result['added']}，重复 {result['duplicates']}")
        self._auto_save()

    @Slot()
    def on_finished(self) -> None:
        meta = self.collector.metadata
        if meta is None: self.status.setText("扫描结束：录像中未识别到 QRF1 二维码。")
        elif self.collector.complete:
            self.status.setText(f"所有 {meta.total} 个分片已收齐，SHA-256 将在保存前再次校验。")
            self.restore.setEnabled(True)
        else:
            missing = self.collector.missing
            preview = ", ".join(str(i + 1) for i in missing[:80]) + (" …" if len(missing) > 80 else "")
            self.status.setText(f"扫描结束：已收集 {len(self.collector.chunks)}/{meta.total}，缺少 {len(missing)} 个分片。\n缺失编号（从 1 开始）：{preview}\n请保存状态并添加补录视频继续扫描。")
        self._auto_save(); self.log.emit("扫描任务结束")

    @Slot(str)
    def on_failed(self, message: str) -> None:
        self.status.setText(f"扫描失败：{message}"); self.log.emit(f"扫描失败：{message}"); QMessageBox.critical(self, "扫描失败", message)

    @Slot()
    def cleanup_thread(self) -> None:
        self.thread.deleteLater(); self.thread = None; self.worker = None
        self.start.setEnabled(bool(self.paths)); self.pause.setEnabled(False); self.cancel.setEnabled(False); self.attempts.setEnabled(True); self.reset_settings.setEnabled(True); self.pause.setText("暂停")

    def toggle_pause(self) -> None:
        if not self.worker: return
        paused = self.pause.text() == "暂停"; self.worker.scanner.set_paused(paused); self.pause.setText("继续" if paused else "暂停")
        self.status.setText("扫描已暂停，已识别分片保留。" if paused else "继续扫描…")

    def cancel_scan(self) -> None:
        if self.worker: self.worker.scanner.cancel(); self.cancel.setEnabled(False); self.status.setText("正在安全取消…")

    def save_state_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "保存恢复状态", self.state_path or "recovery.qrstate", "LumaBridge 状态 (*.qrstate)")
        if path:
            if not path.lower().endswith(".qrstate"): path += ".qrstate"
            self.state_path = path; self._auto_save(show=True)

    def _auto_save(self, show: bool = False) -> None:
        if not self.collector.metadata: return
        if not self.state_path:
            base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
            self.state_path = str(Path(base) / f"{self.collector.metadata.session_id}.qrstate")
        try:
            save_state(self.state_path, self.collector.snapshot())
            if show: QMessageBox.information(self, "状态已保存", self.state_path)
        except Exception as exc: logging.exception("状态保存失败"); self.log.emit(f"状态保存失败：{exc}")

    def load_state_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "加载恢复状态", filter="LumaBridge 状态 (*.qrstate)")
        if not path: return
        try:
            self.collector = ChunkCollector(load_state(path)); self.state_path = path
            meta = self.collector.metadata; chunk_value = round(len(self.collector.chunks) * 100 / meta.total) if meta else 0; self.chunk_progress.setValue(chunk_value); self.chunk_percent.setText(f"{chunk_value} %")
            self.status.setText(f"状态已加载：{meta.filename if meta else '空任务'}，已有 {len(self.collector.chunks)}/{meta.total if meta else '?'} 个分片")
            self.restore.setEnabled(self.collector.complete); self.log.emit(f"已加载恢复状态：{path}")
        except StateError as exc: QMessageBox.critical(self, "状态文件无效", str(exc))

    def restore_file(self) -> None:
        if not self.collector.metadata: return
        name = safe_filename(self.collector.metadata.filename)
        path, _ = QFileDialog.getSaveFileName(self, "保存恢复文件", name)
        if not path: return
        overwrite = False
        if Path(path).exists():
            answer = QMessageBox.question(self, "文件已存在", "目标文件已存在，是否覆盖？")
            if answer != QMessageBox.StandardButton.Yes: return
            overwrite = True
        try:
            saved = restore_to(self.collector, path, overwrite); self.log.emit(f"恢复成功：{saved}")
            QMessageBox.information(self, "恢复成功", f"文件：{saved}\n大小：{human_size(self.collector.metadata.file_size)}\nSHA-256：{self.collector.metadata.digest}")
        except Exception as exc: logging.exception("恢复失败"); QMessageBox.critical(self, "恢复失败", str(exc))

    def copy_missing_numbers(self) -> None:
        QApplication.clipboard().setText(", ".join(str(i + 1) for i in self.collector.missing))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = [u.toLocalFile() for u in event.mimeData().urls()]
        states = [p for p in urls if p.lower().endswith(".qrstate")]
        if states:
            try: self.collector = ChunkCollector(load_state(states[0])); self.state_path = states[0]
            except StateError as exc: QMessageBox.critical(self, "状态文件无效", str(exc))
        self.add_paths([p for p in urls if Path(p).suffix.lower() in self.VIDEO_EXT])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("LumaBridge 光码传输 1.0.1"); self.resize(1080, 740); self.setMinimumSize(940, 650)
        self.dark_mode = False; self.setStyleSheet(LIGHT_STYLESHEET)
        central = QWidget(); central.setObjectName("appRoot"); shell = QHBoxLayout(central); shell.setContentsMargins(0, 0, 0, 0); shell.setSpacing(0)

        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(218)
        side = QVBoxLayout(sidebar); side.setContentsMargins(17, 20, 17, 17); side.setSpacing(6)
        brand_row = QHBoxLayout(); brand_row.setSpacing(10)
        mark = QLabel(alignment=Qt.AlignmentFlag.AlignCenter); mark.setObjectName("brandMark")
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "lumabridge.png"
        if logo_path.exists():
            mark.setPixmap(QPixmap(str(logo_path)).scaled(42, 42, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        brand_copy = QVBoxLayout(); brand_copy.setSpacing(0); brand = QLabel("LumaBridge"); brand.setObjectName("brandName")
        tagline = QLabel("光码离线传输"); tagline.setObjectName("brandTagline"); brand_copy.addWidget(brand); brand_copy.addWidget(tagline)
        brand_row.addWidget(mark); brand_row.addLayout(brand_copy); brand_row.addStretch(); side.addLayout(brand_row); side.addSpacing(22)
        section = QLabel("工作区"); section.setObjectName("navSection"); side.addWidget(section)

        self.stack = QStackedWidget(); self.tabs = self.stack
        self.send_page = SendPage(); self.recover_page = RecoverPage()
        log_page = QWidget(); log_layout = QVBoxLayout(log_page); log_layout.setContentsMargins(0, 0, 0, 0); log_layout.setSpacing(14)
        add_page_header(log_layout, "ACTIVITY · LOCAL ONLY", "任务日志", "运行记录仅保存在本机，不包含原始文件内容或完整二维码载荷。")
        self.log_view = QTextEdit(readOnly=True); self.log_view.setObjectName("logView"); self.log_view.document().setMaximumBlockCount(2000); log_layout.addWidget(self.log_view, 1)
        log_tools = QHBoxLayout(); export_hint = QLabel("日志自动滚动并按大小轮转"); export_hint.setObjectName("muted"); open_log_button = QPushButton("打开日志目录"); open_log_button.clicked.connect(self.open_logs)
        log_tools.addWidget(export_hint); log_tools.addStretch(); log_tools.addWidget(open_log_button); log_layout.addLayout(log_tools)
        self.stack.addWidget(scrollable_page(self.send_page)); self.stack.addWidget(scrollable_page(self.recover_page)); self.stack.addWidget(log_page)

        self.nav_buttons: list[QPushButton] = []
        for index, text in enumerate(("发送文件", "恢复文件", "任务日志")):
            nav = QPushButton(text); nav.setObjectName("navButton"); nav.setCheckable(True); nav.setAutoExclusive(True)
            nav.clicked.connect(lambda _checked=False, page=index: self.navigate(page)); self.nav_buttons.append(nav); side.addWidget(nav)
        self.nav_buttons[0].setChecked(True)
        side.addStretch()
        offline = QLabel("●  完全离线 · 无遥测"); offline.setObjectName("offlineBadge"); offline.setAlignment(Qt.AlignmentFlag.AlignCenter); side.addWidget(offline); side.addSpacing(5)
        self.theme_button = QPushButton("切换深色模式"); self.theme_button.setObjectName("sidebarAction"); self.theme_button.clicked.connect(self.toggle_theme)
        open_logs = QPushButton("打开日志目录"); open_logs.setObjectName("sidebarAction"); open_logs.clicked.connect(self.open_logs)
        about = QPushButton("关于 LumaBridge"); about.setObjectName("sidebarAction"); about.clicked.connect(self.about)
        side.addWidget(self.theme_button); side.addWidget(open_logs); side.addWidget(about)

        content = QFrame(); content.setObjectName("contentSurface"); content_box = QVBoxLayout(content); content_box.setContentsMargins(30, 23, 30, 24); content_box.addWidget(self.stack)
        shell.addWidget(sidebar); shell.addWidget(content, 1); self.setCentralWidget(central)
        self.send_page.log.connect(self.append_log); self.recover_page.log.connect(self.append_log); self.append_log("LumaBridge 已启动（完全离线模式）")

    def navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if 0 <= index < len(self.nav_buttons): self.nav_buttons[index].setChecked(True)

    def toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(DARK_STYLESHEET if self.dark_mode else LIGHT_STYLESHEET)
        self.theme_button.setText("切换浅色模式" if self.dark_mode else "切换深色模式")

    @Slot(str)
    def append_log(self, message: str) -> None:
        self.log_view.append(time.strftime("[%H:%M:%S] ") + message)

    def open_logs(self) -> None:
        path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "logs"; path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def about(self) -> None:
        QMessageBox.about(self, "关于 LumaBridge", "LumaBridge 1.0\n动态二维码离线文件传输工具\n\n不联网、不上传，使用 QRF1 + CRC32 + SHA-256 保证完整性。")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.send_page.analysis_thread is not None:
            answer = QMessageBox.question(self, "文件分析仍在运行", "文件 SHA-256 仍在计算。是否在分析完成后退出？")
            if answer == QMessageBox.StandardButton.Yes:
                self.send_page.analysis_thread.finished.connect(lambda: QTimer.singleShot(0, self.close))
            event.ignore(); return
        busy = self.recover_page.thread is not None
        unsaved = self.recover_page.collector.metadata is not None
        if busy or unsaved:
            answer = QMessageBox.question(self, "确认退出", "存在运行中或可继续的恢复任务。退出前将自动保存状态，是否继续？")
            if answer != QMessageBox.StandardButton.Yes: event.ignore(); return
            if busy and self.recover_page.worker:
                self.recover_page.worker.scanner.cancel()
                self.recover_page.thread.finished.connect(lambda: QTimer.singleShot(0, self.close))
                event.ignore(); return
            self.recover_page._auto_save()
        event.accept()
