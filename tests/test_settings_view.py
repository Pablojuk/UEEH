"""Pruebas mínimas de vista de utilidades."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None

from src.application.services.backup_service import BackupService


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestSettingsView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_crear_vista_sin_error(self) -> None:
        from src.presentation.views.settings_view import SettingsView

        view = SettingsView(backup_service=BackupService(":memory:"))
        self.assertIsNotNone(view)

    def test_mostrar_controles_principales(self) -> None:
        from src.presentation.views.settings_view import SettingsView

        view = SettingsView(backup_service=BackupService(":memory:"))
        self.assertIsNotNone(view.backup_button)
        self.assertIsNotNone(view.restore_button)
        self.assertTrue(view.db_path_label.text())


if __name__ == "__main__":
    unittest.main()
