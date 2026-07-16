"""Estilos globales minimalistas para la aplicación."""

BASE_FONT_POINT_SIZE = 9.75

ATTENDANCE_TABS_STYLE = """
QTabWidget#AttendanceTabs::pane {
    border: 1px solid #93b4d1;
    border-radius: 0 6px 6px 6px;
    background-color: #ffffff;
    top: -1px;
}
QTabWidget#AttendanceTabs QTabBar::tab {
    background-color: #eaf2f8;
    color: #163a5f;
    border: 1px solid #b7cde0;
    border-bottom-color: #93b4d1;
    padding: 8px 16px;
    min-width: 120px;
    font-weight: 600;
}
QTabWidget#AttendanceTabs QTabBar::tab:selected {
    background-color: #1f4e79;
    color: #ffffff;
    border-color: #1f4e79;
}
QTabWidget#AttendanceTabs QTabBar::tab:!selected:hover {
    background-color: #d5e7f5;
    color: #0f2f4f;
    border-color: #2d6ba3;
}
"""

APP_STYLE = """
QWidget {
    background-color: #f5f7fa;
    color: #1f2937;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 9.75pt;
}
QMainWindow, QDialog {
    background-color: #f5f7fa;
}
QFrame#Card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}
QPushButton {
    background-color: #1f4e79;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
}
QPushButton:hover {
    background-color: #2d6ba3;
}
QPushButton:pressed {
    background-color: #17405f;
}
QLineEdit, QComboBox {
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 6px 8px;
}
QAbstractItemView {
    selection-background-color: #dbeafe;
    selection-color: #0f172a;
}
QAbstractItemView::item:selected,
QAbstractItemView::item:selected:!active {
    background-color: #dbeafe;
    color: #0f172a;
    border: 1px solid #93c5fd;
}
QLabel#Title {
    font-size: 20px;
    font-weight: 600;
    color: #0f172a;
}
QLabel#Subtitle {
    font-size: 13px;
    color: #6b7280;
}
"""
