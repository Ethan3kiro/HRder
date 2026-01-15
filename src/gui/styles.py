"""
GUI 样式定义
提供深色和浅色主题
"""

# 深色主题
DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    color: #ffffff;
    font-family: "SF Pro Display", "Segoe UI", "Microsoft YaHei", Arial;
    font-size: 14px;
}

QFrame#sidebar {
    background-color: #252526;
    border-right: 1px solid #3e3e42;
}

QLabel#sidebarTitle {
    background-color: #2d2d30;
    color: white;
    font-size: 18px;
    font-weight: bold;
    padding: 10px;
}

QPushButton#menuButton {
    background-color: transparent;
    color: #cccccc;
    border: none;
    text-align: left;
    padding-left: 20px;
    font-size: 14px;
}

QPushButton#menuButton:hover {
    background-color: #2a2d2e;
}

QPushButton#menuButton[active="true"] {
    background-color: #094771;
    border-left: 4px solid #0e639c;
}

QLabel#sidebarInfo {
    background-color: #2d2d30;
    color: #858585;
    font-size: 12px;
    padding: 10px;
}

QLabel#pageTitle {
    font-size: 28px;
    font-weight: bold;
    color: #ffffff;
    padding: 20px;
}

QLabel#infoText {
    font-size: 16px;
    color: #cccccc;
    padding: 20px;
}

QStackedWidget {
    background-color: #1e1e1e;
}

QPushButton {
    background-color: #0e639c;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #094771;
}

QTableWidget {
    background-color: #252526;
    border: 1px solid #3e3e42;
    gridline-color: #3e3e42;
    color: #cccccc;
}

QHeaderView::section {
    background-color: #2d2d30;
    color: #cccccc;
    padding: 8px;
    border: none;
    border-right: 1px solid #3e3e42;
    border-bottom: 1px solid #3e3e42;
}

QLineEdit, QTextEdit, QComboBox {
    background-color: #3c3c3c;
    border: 1px solid #3e3e42;
    color: #cccccc;
    padding: 6px;
    border-radius: 3px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #0e639c;
}

QComboBox::drop-down {
    border: none;
    background-color: #2d2d30;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border: 2px solid #cccccc;
    border-right: none;
    border-top: none;
    width: 6px;
    height: 6px;
    transform: rotate(-45deg);
}

QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #3e3e42;
    selection-background-color: #0e639c;
    selection-color: white;
}

QSpinBox, QDoubleSpinBox {
    background-color: #3c3c3c;
    border: 1px solid #3e3e42;
    color: #cccccc;
    padding: 6px;
    border-radius: 3px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #0e639c;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: #2d2d30;
    border-left: 1px solid #3e3e42;
    border-bottom: 1px solid #3e3e42;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #3e3e42;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #2d2d30;
    border-left: 1px solid #3e3e42;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #3e3e42;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border: 2px solid #cccccc;
    border-left: none;
    border-bottom: none;
    width: 6px;
    height: 6px;
    transform: rotate(-45deg);
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border: 2px solid #cccccc;
    border-right: none;
    border-top: none;
    width: 6px;
    height: 6px;
    transform: rotate(-45deg);
}

QLabel#statusLabel {
    color: #858585;
    font-size: 12px;
}

QListWidget {
    background-color: #252526;
    border: 1px solid #3e3e42;
    color: #cccccc;
}

QListWidget::item {
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #0e639c;
    color: white;
}

QListWidget::item:hover {
    background-color: #2a2d2e;
}

QGroupBox {
    border: 1px solid #3e3e42;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #cccccc;
}

QCheckBox {
    color: #cccccc;
    spacing: 8px;
    padding: 4px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #555555;
    border-radius: 4px;
    background-color: #2d2d30;
}

QCheckBox::indicator:checked {
    background-color: #0e639c;
    border: 2px solid #1177bb;
    image: url(none);
}

QCheckBox::indicator:hover {
    border: 2px solid #0e639c;
    background-color: #3c3c3c;
}

QCheckBox::indicator:checked:hover {
    background-color: #1177bb;
    border: 2px solid #1177bb;
}
"""

# 浅色主题
LIGHT_THEME = """
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    color: #333333;
    font-family: "SF Pro Display", "Segoe UI", "Microsoft YaHei", Arial;
    font-size: 14px;
}

QFrame#sidebar {
    background-color: #2c3e50;
    border-right: 1px solid #34495e;
}

QLabel#sidebarTitle {
    background-color: #34495e;
    color: white;
    font-size: 18px;
    font-weight: bold;
    padding: 10px;
}

QPushButton#menuButton {
    background-color: transparent;
    color: #ecf0f1;
    border: none;
    text-align: left;
    padding-left: 20px;
    font-size: 14px;
}

QPushButton#menuButton:hover {
    background-color: #34495e;
}

QPushButton#menuButton[active="true"] {
    background-color: #3498db;
    border-left: 4px solid #2980b9;
}

QLabel#sidebarInfo {
    background-color: #34495e;
    color: #95a5a6;
    font-size: 12px;
    padding: 10px;
}

QLabel#pageTitle {
    font-size: 28px;
    font-weight: bold;
    color: #2c3e50;
    padding: 20px;
}

QLabel#infoText {
    font-size: 16px;
    color: #7f8c8d;
    padding: 20px;
}

QStackedWidget {
    background-color: white;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #21618c;
}

QTableWidget {
    background-color: white;
    border: 1px solid #ddd;
    gridline-color: #ddd;
    color: #333;
}

QHeaderView::section {
    background-color: #ecf0f1;
    color: #2c3e50;
    padding: 8px;
    border: none;
    border-right: 1px solid #ddd;
    border-bottom: 1px solid #ddd;
    font-weight: bold;
}

QLineEdit, QTextEdit, QComboBox {
    background-color: white;
    border: 1px solid #ddd;
    color: #333;
    padding: 6px;
    border-radius: 3px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #3498db;
}

QComboBox::drop-down {
    border: none;
    background-color: #ecf0f1;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border: 2px solid #333;
    border-right: none;
    border-top: none;
    width: 6px;
    height: 6px;
    transform: rotate(-45deg);
}

QComboBox QAbstractItemView {
    background-color: white;
    color: #333;
    border: 1px solid #ddd;
    selection-background-color: #3498db;
    selection-color: white;
}

QSpinBox, QDoubleSpinBox {
    background-color: white;
    border: 1px solid #ddd;
    color: #333;
    padding: 6px;
    border-radius: 3px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #3498db;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: #ecf0f1;
    border-left: 1px solid #ddd;
    border-bottom: 1px solid #ddd;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #d5dbdb;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #ecf0f1;
    border-left: 1px solid #ddd;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #d5dbdb;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border: 2px solid #333;
    border-left: none;
    border-bottom: none;
    width: 6px;
    height: 6px;
    transform: rotate(-45deg);
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border: 2px solid #333;
    border-right: none;
    border-top: none;
    width: 6px;
    height: 6px;
    transform: rotate(-45deg);
}

QLabel#statusLabel {
    color: #7f8c8d;
    font-size: 12px;
}

QListWidget {
    background-color: white;
    border: 1px solid #ddd;
    color: #333;
}

QListWidget::item {
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QListWidget::item:hover {
    background-color: #ecf0f1;
}

QGroupBox {
    border: 1px solid #ddd;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #2c3e50;
}

QCheckBox {
    color: #333;
    spacing: 8px;
    padding: 4px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #95a5a6;
    border-radius: 4px;
    background-color: #f8f9fa;
}

QCheckBox::indicator:checked {
    background-color: #3498db;
    border: 2px solid #2980b9;
    image: url(none);
}

QCheckBox::indicator:hover {
    border: 2px solid #3498db;
    background-color: #ecf0f1;
}

QCheckBox::indicator:checked:hover {
    background-color: #2980b9;
    border: 2px solid #21618c;
}
"""


def get_theme(theme_name="light"):
    """
    获取主题样式
    
    Args:
        theme_name: 主题名称 ("light" 或 "dark")
    
    Returns:
        str: CSS 样式字符串
    """
    if theme_name.lower() == "dark":
        return DARK_THEME
    return LIGHT_THEME
