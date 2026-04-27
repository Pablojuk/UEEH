"""Pruebas de la vista especial de Orientación Vocacional."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QComboBox
except ImportError:  # pragma: no cover
    QApplication = None
    QComboBox = None
    Qt = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestOrientacionVocacionalView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_detecta_curso_con_variantes(self) -> None:
        from src.presentation.views.orientacion_vocacional_view import OrientacionVocacionalView

        self.assertEqual(OrientacionVocacionalView.detect_course_key("8vo de EGB"), "8")
        self.assertEqual(OrientacionVocacionalView.detect_course_key("Noveno"), "9")
        self.assertEqual(OrientacionVocacionalView.detect_course_key("Décimo"), "10")

    def test_calcula_calificacion_automaticamente(self) -> None:
        from src.presentation.views.orientacion_vocacional_view import OrientacionVocacionalView

        view = OrientacionVocacionalView()
        view.set_context("AS1", 1, "8vo de EGB")
        view.set_students([{"estudiante_id": "E1", "estudiante": "Lopez Maria"}])
        self.assertIn("fortalezas", view.table.horizontalHeaderItem(2).text().lower())
        self.assertFalse(view.table.verticalHeader().isVisible())
        self.assertGreaterEqual(view.table.columnWidth(1), 220)
        self.assertEqual(view.table.horizontalScrollBarPolicy(), Qt.ScrollBarAsNeeded)
        self.assertTrue(bool(view.table.horizontalHeaderItem(2).toolTip()))

        values = [3, 3, 3, 2, 3]
        for idx, value in enumerate(values):
            combo = view.table.cellWidget(0, 2 + idx)
            assert isinstance(combo, QComboBox)
            combo.setCurrentIndex(combo.findData(value))

        self.assertEqual(view.table.item(0, 7).text(), "A+")
        payload = view.build_save_payload()
        self.assertEqual(payload["filas"][0]["puntaje_total"], 14)
        self.assertEqual(payload["filas"][0]["calificacion"], "A+")


if __name__ == "__main__":
    unittest.main()
