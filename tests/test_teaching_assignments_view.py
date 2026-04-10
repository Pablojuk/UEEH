"""Pruebas mínimas de vista de asignaciones académicas."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestTeachingAssignmentsView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_crear_vista_sin_error(self) -> None:
        from src.application.services.catalog_service import CatalogService
        from src.application.services.teacher_service import TeacherService
        from src.application.services.teaching_assignment_service import TeachingAssignmentService
        from src.infrastructure.persistence.db import initialize_database
        from src.presentation.views.teaching_assignments_view import TeachingAssignmentsView

        conn = initialize_database(":memory:")
        view = TeachingAssignmentsView(TeachingAssignmentService(conn), TeacherService(conn), CatalogService(conn))
        self.assertIsNotNone(view.teacher_combo)
        self.assertIsNotNone(view.table)
        self.assertFalse(hasattr(view, "search_input"))
        self.assertEqual(view.table.rowCount(), 0)
        conn.close()
