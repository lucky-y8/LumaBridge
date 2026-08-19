from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QTimer, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


def configure_logging() -> Path:
    directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "logs"
    try:
        directory.mkdir(parents=True, exist_ok=True); path = directory / "lumabridge.log"
        handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    except OSError:
        # Keep the application usable when the regular Windows log is temporarily locked.
        # Windows 常规日志被临时占用时，回退到临时目录以保证应用仍可启动。
        directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation)) / "LumaBridge" / "logs"
        directory.mkdir(parents=True, exist_ok=True); path = directory / "lumabridge.log"
        handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=2, encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[handler], format="%(asctime)s %(levelname)s %(name)s %(message)s")
    return path


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv); app.setApplicationName("LumaBridge"); app.setOrganizationName("LumaBridge")
    icon_path = Path(__file__).resolve().parent / "assets" / "lumabridge.png"
    if icon_path.exists(): app.setWindowIcon(QIcon(str(icon_path)))
    configure_logging()
    from .ui.main_window import MainWindow
    window = MainWindow(); window.show()
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(500, app.quit)
    return app.exec()


if __name__ == "__main__": raise SystemExit(main())
