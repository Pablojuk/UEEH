"""Pruebas de comportamiento para Animación a la Lectura."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None
    Qt = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestAnimacionLecturaView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_scroll_horizontal_visible_en_tabla_central(self) -> None:
        from src.presentation.views.animacion_lectura_view import AnimacionLecturaView

        view = AnimacionLecturaView()
        view.level_combo.setCurrentIndex(view.level_combo.findData("superior"))
        view.set_students([{"estudiante_id": "E1", "estudiante": "López María"}], selected_level="superior")

        self.assertEqual(view.center_table.horizontalScrollBarPolicy(), Qt.ScrollBarAlwaysOn)
        self.assertGreater(view.center_table.columnCount(), 0)


if __name__ == "__main__":
    unittest.main()
