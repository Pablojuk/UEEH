"""Pruebas mínimas de vista de matrículas."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestEnrollmentsView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_crear_vista_sin_error(self) -> None:
        from src.application.services.catalog_service import CatalogService
        from src.application.services.enrollment_service import EnrollmentService
        from src.application.services.student_service import StudentService
        from src.infrastructure.persistence.db import initialize_database
        from src.presentation.views.enrollments_view import EnrollmentsView

        conn = initialize_database(":memory:")
        view = EnrollmentsView(EnrollmentService(conn), StudentService(conn), CatalogService(conn))
        self.assertIsNotNone(view.student_combo)
        self.assertIsNotNone(view.table)
        self.assertEqual(view.table.rowCount(), 0)
        conn.close()
