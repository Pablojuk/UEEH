"""Pruebas mínimas de la vista de estudiantes."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestStudentsView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        from src.application.services.student_import_service import StudentImportService
        from src.application.services.student_service import StudentService
        from src.infrastructure.persistence.db import initialize_database

        self.connection = initialize_database(":memory:")
        self.student_service = StudentService(self.connection)
        self.import_service = StudentImportService(self.student_service)

    def tearDown(self) -> None:
        self.connection.close()

    def test_crear_vista_sin_error(self) -> None:
        from src.presentation.views.students_view import StudentsView

        view = StudentsView(self.student_service, self.import_service)
        self.assertIsNotNone(view)
        self.assertEqual(view.table.rowCount(), 0)
        self.assertIsNotNone(view.search_input)
        self.assertIsNotNone(view.import_button)
