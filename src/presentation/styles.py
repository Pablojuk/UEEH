"""Estilos globales minimalistas para la aplicación."""

BASE_FONT_POINT_SIZE = 9.75

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
