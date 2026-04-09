from PySide6.QtGui import QFont


APP_STYLE_SHEET = """
QWidget {
    background-color: #f3efe8;
    color: #182027;
    font-size: 14px;
}

QFrame#heroCard {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #f7efe1,
        stop: 0.55 #f9f6ef,
        stop: 1 #e4f1ee
    );
    border: 1px solid #d9d0c4;
    border-radius: 28px;
}

QFrame#surfaceCard {
    background-color: #fcfbf8;
    border: 1px solid #ddd6cb;
    border-radius: 24px;
}

QFrame#uploadCard {
    background-color: #f8f4ed;
    border: 1px solid #e0d5c7;
    border-radius: 20px;
}

QLabel#heroTitle {
    background: transparent;
    color: #132028;
    font-size: 30px;
    font-weight: 700;
}

QLabel#heroSubtitle {
    background: transparent;
    color: #52606a;
    font-size: 14px;
}

QLabel#sectionEyebrow {
    background: transparent;
    color: #0f766e;
    font-size: 12px;
    font-weight: 700;
}

QLabel#sectionTitle {
    background: transparent;
    color: #132028;
    font-size: 19px;
    font-weight: 700;
}

QLabel#uploadTitle {
    background: transparent;
    color: #132028;
    font-size: 16px;
    font-weight: 700;
}

QLabel#sectionSubtitle,
QLabel#mutedText,
QLabel#uploadMeta {
    background: transparent;
    color: #67727a;
    font-size: 13px;
}

QLabel#fieldLabel {
    background: transparent;
    color: #4f5a60;
    font-size: 12px;
    font-weight: 700;
}

QLabel#valueLabel,
QLabel#outputLabel {
    background-color: #f7f3ec;
    border: 1px solid #ddd6cb;
    border-radius: 16px;
    color: #1a252b;
    padding: 12px 14px;
}

QLabel#statusBadge,
QLabel#accentBadge {
    border-radius: 14px;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 10px;
}

QLabel#statusBadge {
    background-color: rgba(255, 255, 255, 0.88);
    border: 1px solid #cfe1dc;
    color: #0f766e;
}

QLabel#accentBadge {
    background-color: #0f766e;
    color: #ffffff;
}

QLineEdit,
QSpinBox,
QComboBox,
QListWidget {
    background-color: #ffffff;
    border: 1px solid #d9d1c5;
    border-radius: 16px;
    color: #182027;
    padding: 12px 14px;
    selection-background-color: #0f766e;
    selection-color: #ffffff;
}

QLineEdit:focus,
QSpinBox:focus,
QComboBox:focus,
QListWidget:focus {
    border: 1px solid #0f766e;
}

QSpinBox::up-button,
QSpinBox::down-button {
    border: none;
    width: 22px;
    background: transparent;
}

QSpinBox::up-arrow,
QSpinBox::down-arrow {
    image: none;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox::down-arrow {
    image: none;
}

QListWidget#fileDropList {
    background-color: #fffaf2;
    border: 2px dashed #ccbfae;
    border-radius: 18px;
    padding: 14px;
}

QListWidget#fileDropList[dragActive="true"] {
    background-color: #e8f4f1;
    border-color: #0f766e;
}

QListWidget::item {
    background-color: #f8f4ed;
    border: 1px solid #ece3d7;
    border-radius: 14px;
    margin: 4px 0;
    padding: 12px;
}

QListWidget::item:selected {
    background-color: #ddeeea;
    border: 1px solid #93c2b8;
    color: #15312f;
}

QPushButton {
    background-color: #e7ddd1;
    border: none;
    border-radius: 16px;
    color: #182027;
    font-weight: 700;
    padding: 12px 16px;
}

QPushButton:hover {
    background-color: #ddd1c2;
}

QPushButton:pressed {
    background-color: #d2c2af;
}

QPushButton#primaryButton {
    background-color: #0f766e;
    color: #ffffff;
    padding: 14px 20px;
}

QPushButton#primaryButton:hover {
    background-color: #0c615b;
}

QPushButton#primaryButton:pressed {
    background-color: #0a514c;
}

QPushButton#ghostButton {
    background-color: #ffffff;
    border: 1px solid #ddd6cb;
}

QPushButton#ghostButton:hover {
    background-color: #f6f2eb;
}

QPushButton#dangerButton {
    background-color: #ca6154;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #b65448;
}

QPushButton:disabled {
    background-color: #dad5cb;
    color: #8b908d;
}

QScrollBar:vertical {
    background: transparent;
    margin: 8px 2px;
    width: 10px;
}

QScrollBar::handle:vertical {
    background-color: #cbbfae;
    border-radius: 5px;
    min-height: 28px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    border: none;
    height: 0;
}

QMessageBox QWidget {
    background-color: #f7f3ec;
}
"""


def apply_app_theme(app):
    app.setStyle("Fusion")
    app.setFont(QFont("Avenir Next", 11))
    app.setStyleSheet(APP_STYLE_SHEET)
