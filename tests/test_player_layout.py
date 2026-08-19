import hashlib

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QLabel

from optical_transfer.models import FileMetadata, Frame
from optical_transfer.protocol import encode_frame
from optical_transfer.sender.player import QRPlayerDialog
from optical_transfer.ui.main_window import MainWindow, SendPage
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
