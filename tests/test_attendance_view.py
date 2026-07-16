"""Pruebas visuales básicas de la vista de asistencias."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


class _FakeAttendanceService:
    def list_assignments(self) -> list[dict]:
        return []

    def listar_firmantes_disponibles(self) -> list[dict]:
        return []


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestAttendanceView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_tres_pestanas_habilitadas_y_con_estilo_local(self) -> None:
        import src.presentation.views.attendance_view as attendance_module

        with patch.object(attendance_module, "QWebEngineView", None):
            view = attendance_module.AttendanceView(_FakeAttendanceService())

        self.assertEqual(view.tabs.objectName(), "AttendanceTabs")
        self.assertEqual(
            [view.tabs.tabText(index) for index in range(view.tabs.count())],
            ["Sábana mensual", "Informe trimestral", "Informe anual"],
        )
        self.assertTrue(all(view.tabs.isTabEnabled(index) for index in range(view.tabs.count())))
        self.assertIn("QTabWidget#AttendanceTabs", view.tabs.styleSheet())
        self.assertIn("QTabBar::tab:!selected:hover", view.tabs.styleSheet())
        view.deleteLater()


if __name__ == "__main__":
    unittest.main()
