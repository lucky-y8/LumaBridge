import hashlib

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QLabel

from optical_transfer.models import FileMetadata, Frame
from optical_transfer.protocol import encode_frame
from optical_transfer.sender.player import QRPlayerDialog
from optical_transfer.ui.main_window import MainWindow, RecoverPage, SendPage
from optical_transfer.ui.theme import APP_STYLESHEET, DARK_STYLESHEET, LIGHT_STYLESHEET


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


@pytest.mark.parametrize("width,height", [(1366, 768), (1093, 614), (900, 600)])
def test_footer_stays_visible_and_qr_uses_remaining_space(app, width, height):
    data = b"layout-test" * 20
    digest = hashlib.sha256(data).hexdigest()
    meta = FileMetadata(digest[:16], 1, len(data), digest, "很长的中文文件名_" * 20 + ".bin")
    import zlib
    frame = Frame(meta, 0, f"{zlib.crc32(data) & 0xFFFFFFFF:08x}", data)
    dialog = QRPlayerDialog([encode_frame(frame)], meta.filename, meta.file_size, meta.digest, 3, countdown=False)
    dialog.resize(width, height); dialog.show(); app.processEvents(); dialog.show_current(); app.processEvents()
    assert dialog.status.isVisible()
    assert dialog.status.geometry().bottom() <= dialog.contentsRect().bottom()
    assert dialog.status.height() >= dialog.status.fontMetrics().lineSpacing() * 4
    assert dialog.qr.pixmap() is not None
    assert dialog.qr.pixmap().width() <= dialog.qr.contentsRect().width()
    assert dialog.qr.pixmap().height() <= dialog.qr.contentsRect().height()
    dialog.close()


def test_light_default_dark_option_and_recording_tip(app):
    assert APP_STYLESHEET == LIGHT_STYLESHEET
    assert "#FFFFFF" in LIGHT_STYLESHEET
    assert "#1F2937" in DARK_STYLESHEET
    assert "#111827" in DARK_STYLESHEET
    page = SendPage()
    texts = [label.text() for label in page.findChildren(type(page.info))]
    assert any("手机横屏、1080p/60fps录像" in text and "两个完整循环" in text for text in texts)
    page.close()


def test_brand_logo_is_loaded(app):
    window = MainWindow()
    mark = window.findChild(QLabel, "brandMark")
    assert mark is not None
    assert mark.pixmap() is not None and not mark.pixmap().isNull()
    window.close()


def test_progress_percent_is_separate_from_bar(app):
    page = RecoverPage()
    assert not page.video_progress.isTextVisible()
    assert not page.chunk_progress.isTextVisible()
    assert page.video_percent.text() == "0%"
    assert page.chunk_percent.text() == "0%"
    assert "color: transparent" not in APP_STYLESHEET
    page.close()


def test_send_and_recover_restore_defaults(app):
    send = SendPage(); send.mode.setCurrentText("自定义"); send.chunk.setValue(930); send.fps.setValue(7.5); send.loops.setCurrentText("无限循环"); send.countdown.setChecked(False)
    send.reset_defaults()
    assert send.mode.currentText() == "标准（推荐）" and send.chunk.value() == 700 and send.fps.value() == 3.0
    assert send.loops.currentText() == "2 次" and send.countdown.isChecked()
    recover = RecoverPage(); recover.attempts.setValue(27); recover.reset_defaults(); assert recover.attempts.value() == 12
    send.close(); recover.close()
