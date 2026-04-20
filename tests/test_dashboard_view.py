"""Pruebas mínimas de layout para vista de inicio."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel
except ImportError:  # pragma: no cover
    QApplication = None
    QLabel = None


class _FakeInstitutionService:
    def obtener_actual(self) -> dict:
        return {}


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestDashboardView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_titulos_logos_en_mayusculas_y_centrados(self) -> None:
        from src.presentation.views.dashboard_view import DashboardView

        view = DashboardView(_FakeInstitutionService())
        texts = {label.text(): label for label in view.findChildren(QLabel)}

        self.assertIn("MINISTERIO DE EDUCACIÓN, DEPORTE Y CULTURA", texts)
        self.assertIn("LOGO INSTITUCIONAL", texts)
        self.assertTrue(texts["MINISTERIO DE EDUCACIÓN, DEPORTE Y CULTURA"].alignment())
        self.assertTrue(texts["LOGO INSTITUCIONAL"].alignment())


if __name__ == "__main__":
    unittest.main()
