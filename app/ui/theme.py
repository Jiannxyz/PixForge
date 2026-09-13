"""Dark professional theme for PixForge."""

APP_STYLESHEET = """
QWidget {
    background-color: #12141a;
    color: #e8eaed;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}
QMainWindow, QScrollArea, QFrame#card, QListWidget {
    background-color: #12141a;
}
QFrame#header {
    background-color: #12141a;
    border: none;
}
QLabel#title {
    font-size: 22px;
    font-weight: 700;
    color: #f4f6fb;
}
QLabel#subtitle {
    font-size: 13px;
    color: #9aa3b2;
}
QLabel#muted {
    color: #9aa3b2;
}
QLabel#section {
    font-size: 12px;
    font-weight: 600;
    color: #c5cdd8;
}
QFrame#dropZone {
    background-color: #1a1d26;
    border: 1.5px dashed #3b4252;
    border-radius: 14px;
}
QFrame#dropZone[active="true"] {
    border-color: #6b8cff;
    background-color: #1c2438;
}
QFrame#row {
    background-color: #1a1d26;
    border: 1px solid #2a2f3c;
    border-radius: 10px;
}
QListWidget {
    border: none;
    outline: none;
    padding: 2px;
}
QListWidget::item {
    margin: 4px 0;
    padding: 0;
    border: none;
}
QListWidget::item:selected QFrame#row {
    border-color: #6b8cff;
    background-color: #20263a;
}
QPushButton {
    background-color: #262a35;
    color: #e8eaed;
    border: 1px solid #343b4b;
    border-radius: 8px;
    padding: 8px 14px;
    min-height: 32px;
}
QPushButton:hover {
    background-color: #303645;
}
QPushButton:disabled {
    color: #6d7482;
    background-color: #1d212a;
}
QPushButton#primary {
    background-color: #4f7cff;
    border: none;
    color: white;
    font-weight: 700;
    min-height: 42px;
    font-size: 14px;
}
QPushButton#primary:hover {
    background-color: #6b8cff;
}
QPushButton#primary:disabled {
    background-color: #2d3a63;
    color: #9aa3b2;
}
QPushButton#danger {
    background-color: #3a2a2e;
    border-color: #5a3a42;
}
QComboBox, QLineEdit, QSpinBox {
    background-color: #1a1d26;
    border: 1px solid #343b4b;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 32px;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #2a2f3c;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
    background: #6b8cff;
}
QProgressBar {
    background-color: #1a1d26;
    border: 1px solid #2a2f3c;
    border-radius: 8px;
    text-align: center;
    min-height: 18px;
    color: #e8eaed;
}
QProgressBar::chunk {
    background-color: #4f7cff;
    border-radius: 7px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #4a5162;
    background: #1a1d26;
}
QCheckBox::indicator:checked {
    background: #4f7cff;
    border-color: #4f7cff;
}
QStatusBar {
    background: #12141a;
    color: #9aa3b2;
}
QDialog {
    background-color: #12141a;
}
QGroupBox {
    border: 1px solid #2a2f3c;
    border-radius: 8px;
    margin-top: 18px;
    font-weight: 600;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #c5cdd8;
}
QLabel#badge {
    background-color: #242938;
    color: #8fa3c7;
    border: 1px solid #343f56;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: 600;
}
QLabel#countBadge {
    background-color: #1f2433;
    color: #8fa3c7;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}
QLabel#statusReady {
    color: #8fa3c7;
    font-weight: 600;
}
QLabel#statusConverting {
    color: #38bdf8;
    font-weight: 600;
}
QLabel#statusCompleted {
    color: #4ade80;
    font-weight: 600;
}
QLabel#statusFailed {
    color: #f87171;
    font-weight: 600;
}
QLabel#statusSkipped {
    color: #fbbf24;
    font-weight: 600;
}
QFrame#thumbnailBox {
    background-color: #0f1117;
    border: 1px solid #2a2f3c;
    border-radius: 6px;
}
QFrame#card {
    background-color: #161922;
    border: 1px solid #262b37;
    border-radius: 12px;
}
QPushButton#iconButton {
    background-color: transparent;
    border: none;
    padding: 4px;
    min-height: 24px;
    min-width: 24px;
    border-radius: 4px;
    color: #9aa3b2;
}
QPushButton#iconButton:hover {
    background-color: #262a35;
    color: #f4f6fb;
}
QScrollArea {
    border: none;
}
"""

