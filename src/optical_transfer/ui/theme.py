"""Codex-inspired light and dark themes for the desktop application.

桌面应用使用的 Codex 风格浅色与深色主题。
"""

DARK_STYLESHEET = r"""
QWidget {
    color: #E5E7EB;
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 13px;
}
QMainWindow, QWidget#appRoot { background: #111827; }
QFrame#sidebar { background: #1F2937; border: none; }
QLabel#brandMark {
    background: transparent;
    min-width: 42px; min-height: 42px;
    max-width: 42px; max-height: 42px;
}
QLabel#brandName { color: #F9FAFB; font-size: 17px; font-weight: 750; }
QLabel#brandTagline { color: #9CA3AF; font-size: 11px; }
QLabel#navSection {
    color: #6B7280;
    font-size: 10px;
    font-weight: 700;
    padding: 12px 11px 5px 11px;
}
QPushButton#navButton {
    color: #B8C0CC;
    background: transparent;
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 10px 13px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#navButton:hover { color: #FFFFFF; background: #2B3646; }
QPushButton#navButton:checked {
    color: #FFFFFF;
    background: #374151;
    border-left: 2px solid #10B981;
    padding-left: 11px;
    font-weight: 650;
}
QPushButton#sidebarAction {
    color: #9CA3AF;
    background: transparent;
    border: none;
    border-radius: 7px;
    text-align: left;
    padding: 8px 11px;
}
QPushButton#sidebarAction:hover { color: #F9FAFB; background: #2B3646; }
QLabel#offlineBadge {
    color: #6EE7B7;
    background: #18352E;
    border: 1px solid #27624F;
    border-radius: 8px;
    padding: 7px 9px;
    font-size: 11px;
    font-weight: 600;
}
QFrame#contentSurface { background: #111827; border: none; }
QScrollArea#workspaceScroll, QScrollArea#workspaceScroll > QWidget > QWidget {
    background: #111827;
    border: none;
}
QLabel#eyebrow { color: #6EE7B7; font-size: 10px; font-weight: 800; }
QLabel#pageTitle { color: #F9FAFB; font-size: 27px; font-weight: 750; }
QLabel#pageSubtitle { color: #9CA3AF; font-size: 13px; }
QFrame#card, QGroupBox {
    background: #18212F;
    border: 1px solid #2E3A4B;
    border-radius: 11px;
}
QGroupBox {
    margin-top: 12px;
    padding: 18px 16px 14px 16px;
    font-size: 14px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 0 6px;
    color: #E5E7EB;
    background: #18212F;
}
QLabel#cardTitle { color: #F3F4F6; font-size: 15px; font-weight: 700; }
QLabel#muted { color: #8B95A5; font-size: 12px; }
QLabel#pathBox {
    color: #C7CFDA;
    background: #111827;
    border: 1px dashed #4B5563;
    border-radius: 8px;
    padding: 10px 12px;
}
QLabel#tipPanel {
    color: #D1FAE5;
    background: #142A24;
    border: 1px solid #245442;
    border-radius: 9px;
    padding: 11px 14px;
    font-weight: 600;
}
QLabel#infoPanel {
    color: #C9D1DC;
    background: #151E2B;
    border: 1px solid #334155;
    border-radius: 9px;
    padding: 13px 15px;
}
QPushButton {
    min-height: 32px;
    border-radius: 7px;
    padding: 1px 13px;
    border: 1px solid #3A4657;
    background: #1F2937;
    color: #E5E7EB;
    font-weight: 550;
}
QPushButton:hover { background: #2A3545; border-color: #596578; color: #FFFFFF; }
QPushButton:pressed { background: #111827; border-color: #6B7280; }
QPushButton:disabled { color: #687386; background: #192230; border-color: #293445; }
QPushButton#primaryButton {
    color: #111827;
    background: #F9FAFB;
    border: 1px solid #F9FAFB;
    min-height: 38px;
    font-size: 13px;
    font-weight: 700;
    padding: 1px 20px;
}
QPushButton#primaryButton:hover { background: #E5E7EB; border-color: #E5E7EB; }
QPushButton#primaryButton:pressed { background: #CBD5E1; border-color: #CBD5E1; }
QPushButton#primaryButton:disabled { color: #657184; background: #2B3544; border-color: #2B3544; }
QPushButton#dangerButton { color: #FDA4AF; border-color: #663845; background: #2A1C24; }
QPushButton#dangerButton:hover { color: #FFE4E6; background: #42232D; border-color: #9F5264; }
QComboBox, QSpinBox, QDoubleSpinBox {
    min-height: 32px;
    color: #E5E7EB;
    background: #111827;
    border: 1px solid #3A4657;
    border-radius: 7px;
    padding: 1px 9px;
    selection-background-color: #047857;
}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border-color: #5F6B7D; }
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #10B981; }
QComboBox::drop-down { border: none; width: 24px; }
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: #1F2937; border: none; width: 20px;
}
QCheckBox { spacing: 8px; color: #C7CFDA; }
QCheckBox::indicator { width: 16px; height: 16px; }
QProgressBar {
    min-height: 8px; max-height: 8px;
    background: #2B3544;
    border: none;
    border-radius: 4px;
    text-align: center;
}
QProgressBar::chunk { background: #10B981; border-radius: 4px; }
QLabel#progressPercent { color: #D1D5DB; font-size: 12px; font-weight: 650; }
QTableWidget {
    background: #111827;
    alternate-background-color: #151E2B;
    color: #D1D5DB;
    border: 1px solid #303C4C;
    border-radius: 8px;
    gridline-color: #263142;
    selection-background-color: #28443C;
    selection-color: #F9FAFB;
    outline: none;
}
QHeaderView::section {
    color: #9CA3AF;
    background: #1F2937;
    border: none;
    border-bottom: 1px solid #374151;
    padding: 8px 9px;
    font-size: 11px;
    font-weight: 700;
}
QTableWidget::item { padding: 7px 9px; border-bottom: 1px solid #263142; }
QTextEdit#logView {
    color: #D1D5DB;
    background: #0B1018;
    border: 1px solid #2B3544;
    border-radius: 10px;
    padding: 13px;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 12px;
    selection-background-color: #047857;
}
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #4B5563; border-radius: 4px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #6B7280; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { color: #F9FAFB; background: #1F2937; border: 1px solid #374151; padding: 5px 8px; }
"""

# Keep the dark palette available, then override its colors for the default light appearance.
# 保留深色配色，并通过后置规则覆盖为默认浅色外观。
LIGHT_STYLESHEET = DARK_STYLESHEET + r"""
QWidget { color: #1F2937; }
QMainWindow, QWidget#appRoot { background: #FFFFFF; }
QFrame#sidebar { background: #F3F4F6; }
QLabel#brandMark { background: transparent; }
QLabel#brandName { color: #111827; }
QLabel#brandTagline { color: #6B7280; }
QLabel#navSection { color: #9CA3AF; }
QPushButton#navButton { color: #4B5563; background: transparent; }
QPushButton#navButton:hover { color: #111827; background: #E5E7EB; }
QPushButton#navButton:checked {
    color: #111827; background: #E5E7EB; border-left: 2px solid #10A37F;
}
QPushButton#sidebarAction { color: #6B7280; background: transparent; }
QPushButton#sidebarAction:hover { color: #111827; background: #E5E7EB; }
QLabel#offlineBadge { color: #047857; background: #ECFDF5; border-color: #A7F3D0; }
QFrame#contentSurface { background: #FFFFFF; }
QScrollArea#workspaceScroll, QScrollArea#workspaceScroll > QWidget > QWidget { background: #FFFFFF; }
QLabel#eyebrow { color: #0E8F71; }
QLabel#pageTitle { color: #111827; }
QLabel#pageSubtitle { color: #6B7280; }
QFrame#card, QGroupBox { background: #FAFAFA; border-color: #E5E7EB; }
QGroupBox::title { color: #1F2937; background: #FAFAFA; }
QLabel#cardTitle { color: #111827; }
QLabel#muted { color: #6B7280; }
QLabel#pathBox { color: #4B5563; background: #FFFFFF; border-color: #D1D5DB; }
QLabel#tipPanel { color: #065F46; background: #ECFDF5; border-color: #A7F3D0; }
QLabel#infoPanel { color: #374151; background: #F9FAFB; border-color: #E5E7EB; }
QPushButton {
    color: #1F2937; background: #FFFFFF; border-color: #D1D5DB;
}
QPushButton:hover { color: #111827; background: #F3F4F6; border-color: #9CA3AF; }
QPushButton:pressed { background: #E5E7EB; border-color: #6B7280; }
QPushButton:disabled { color: #9CA3AF; background: #F3F4F6; border-color: #E5E7EB; }
QPushButton#primaryButton { color: #FFFFFF; background: #111827; border-color: #111827; }
QPushButton#primaryButton:hover { color: #FFFFFF; background: #2F3744; border-color: #2F3744; }
QPushButton#primaryButton:pressed { color: #FFFFFF; background: #000000; border-color: #000000; }
QPushButton#primaryButton:disabled { color: #9CA3AF; background: #E5E7EB; border-color: #E5E7EB; }
QPushButton#dangerButton { color: #BE123C; border-color: #FECDD3; background: #FFF1F2; }
QPushButton#dangerButton:hover { color: #9F1239; background: #FFE4E6; border-color: #FDA4AF; }
QComboBox, QSpinBox, QDoubleSpinBox {
    color: #1F2937; background: #FFFFFF; border-color: #D1D5DB; selection-background-color: #10A37F;
}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border-color: #9CA3AF; }
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #10A37F; }
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { background: #F3F4F6; }
QCheckBox { color: #374151; }
QProgressBar { background: #E5E7EB; }
QProgressBar::chunk { background: #10A37F; }
QLabel#progressPercent { color: #374151; }
QTableWidget {
    color: #374151; background: #FFFFFF; alternate-background-color: #FAFAFA;
    border-color: #E5E7EB; gridline-color: #F3F4F6;
    selection-background-color: #D1FAE5; selection-color: #111827;
}
QHeaderView::section { color: #6B7280; background: #F3F4F6; border-bottom-color: #E5E7EB; }
QTableWidget::item { border-bottom-color: #F3F4F6; }
QScrollBar::handle:vertical { background: #D1D5DB; }
QScrollBar::handle:vertical:hover { background: #9CA3AF; }
QToolTip { color: #F9FAFB; background: #1F2937; border-color: #374151; }
"""

APP_STYLESHEET = LIGHT_STYLESHEET
