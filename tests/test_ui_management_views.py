"""Pruebas mínimas para vistas funcionales de gestión (BLOQUE 5)."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestUIManagementViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        from src.application.services.catalog_service import CatalogService
        from src.application.services.institution_service import InstitutionService
        from src.application.services.teacher_service import TeacherService
        from src.infrastructure.persistence.db import initialize_database

        self.connection = initialize_database(":memory:")
        self.institution_service = InstitutionService(self.connection)
        self.teacher_service = TeacherService(self.connection)
        self.catalog_service = CatalogService(self.connection)

    def tearDown(self) -> None:
        self.connection.close()

    def test_institution_view_loads_form(self) -> None:
        from src.presentation.views.institution_view import InstitutionView

        view = InstitutionView(self.institution_service)
        self.assertIsNotNone(view.name_input)
        self.assertIsNotNone(view.shift_input)

    def test_teachers_view_loads_empty_table(self) -> None:
        from src.presentation.views.teachers_view import TeachersView

        view = TeachersView(self.teacher_service)
        self.assertEqual(view.table.rowCount(), 0)
        self.assertIsNotNone(view.search_input)

    def test_catalogs_view_loads_tabs_and_tables(self) -> None:
        from src.presentation.views.catalogs_view import CatalogsView

        view = CatalogsView(self.catalog_service)
        self.assertEqual(view.tabs.count(), 4)
        self.assertEqual(view.courses_table.rowCount(), 0)
        self.assertEqual(view.parallels_table.rowCount(), 0)
        self.assertEqual(view.subjects_table.rowCount(), 0)
        self.assertEqual(view.subjects_table.columnCount(), 2)
        self.assertEqual(view.periods_table.rowCount(), 0)
