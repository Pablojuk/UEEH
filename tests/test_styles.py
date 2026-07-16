"""Pruebas del tamaño de fuente base y unidades admitidas por Qt."""

from __future__ import annotations

import os
import unittest

from src.presentation.styles import APP_STYLE, ATTENDANCE_TABS_STYLE, BASE_FONT_POINT_SIZE

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication, QWidget
except ImportError:  # pragma: no cover
    QApplication = None
    QFont = None
    QWidget = None


class TestStyleDefinition(unittest.TestCase):
    def test_tamano_base_es_positivo_y_en_puntos(self) -> None:
        self.assertGreater(BASE_FONT_POINT_SIZE, 0)
        self.assertIn("font-size: 9.75pt;", APP_STYLE)
        self.assertNotIn("QWidget {\n    background-color: #f5f7fa;\n    color: #1f2937;\n    font-family: 'Segoe UI', 'Arial', sans-serif;\n    font-size: 13px;", APP_STYLE)

    def test_seleccion_de_tablas_es_suave_y_legible(self) -> None:
        self.assertIn("selection-background-color: #dbeafe;", APP_STYLE)
        self.assertIn("selection-color: #0f172a;", APP_STYLE)
        self.assertIn("border: 1px solid #93c5fd;", APP_STYLE)

    def test_pestanas_de_asistencias_tienen_estilo_local_legible(self) -> None:
        self.assertIn("QTabWidget#AttendanceTabs QTabBar::tab:selected", ATTENDANCE_TABS_STYLE)
        self.assertIn("background-color: #1f4e79;", ATTENDANCE_TABS_STYLE)
        self.assertIn("color: #ffffff;", ATTENDANCE_TABS_STYLE)
        self.assertIn("QTabBar::tab:!selected:hover", ATTENDANCE_TABS_STYLE)
        self.assertNotIn("AttendanceTabs", APP_STYLE)


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestQtFontUnits(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_estilo_base_produce_point_size_positivo(self) -> None:
        previous_style = self.app.styleSheet()
        try:
            self.app.setStyleSheet(APP_STYLE)
            widget = QWidget()
            widget.ensurePolished()
            self.assertGreater(widget.font().pointSizeF(), 0)
        finally:
            self.app.setStyleSheet(previous_style)

    def test_fuente_en_pixeles_conserva_su_unidad(self) -> None:
        font = QFont()
        font.setPixelSize(13)
        self.assertEqual(font.pixelSize(), 13)
        self.assertEqual(font.pointSizeF(), -1)

    def test_fuente_en_puntos_conserva_tamano_positivo(self) -> None:
        font = QFont()
        font.setPointSizeF(BASE_FONT_POINT_SIZE)
        self.assertEqual(font.pointSizeF(), BASE_FONT_POINT_SIZE)
        self.assertEqual(font.pixelSize(), -1)
