"""Pruebas para reporte especial de Orientación Vocacional."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestOrientacionVocacionalReportView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_mapeo_descripcion_por_cualitativo(self) -> None:
        from src.presentation.views.orientacion_vocacional_report_view import OrientacionVocacionalReportView

        self.assertEqual(OrientacionVocacionalReportView._descripcion_por_cualitativo("A+"), "Siempre")
        self.assertEqual(OrientacionVocacionalReportView._descripcion_por_cualitativo("A-"), "Frecuentemente")
        self.assertEqual(OrientacionVocacionalReportView._descripcion_por_cualitativo("B+"), "Ocasionalmente")
        self.assertEqual(OrientacionVocacionalReportView._descripcion_por_cualitativo(""), "Sin información")

    def test_estadistica_usa_solo_a_mas_a_menos_b_mas(self) -> None:
        from src.presentation.views.orientacion_vocacional_report_view import OrientacionVocacionalReportView

        view = OrientacionVocacionalReportView()
        view.set_context("AS1", 1)
        view.set_students(
            [
                {"estudiante": "A", "calificacion": "A+"},
                {"estudiante": "B", "calificacion": "A-"},
                {"estudiante": "C", "calificacion": "A+"},
                {"estudiante": "D", "calificacion": ""},
            ]
        )
        stats = view._build_stats_summary()
        self.assertEqual([r["escala"] for r in stats["rows"]], ["A+", "A-", "B+"])
        self.assertEqual([r["numero"] for r in stats["rows"]], [2, 1, 0])
        self.assertEqual(stats["total_n"], 4)


if __name__ == "__main__":
    unittest.main()
