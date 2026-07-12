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

    def test_tabla_ordena_codigos_naturalmente_tambien_en_busqueda(self) -> None:
        from PySide6.QtWidgets import QHeaderView

        from src.presentation.views.students_view import StudentsView

        students = [
            ("E100", "EST-100", "Grupo", "Cien", "100"),
            ("E10", "EST-010", "Grupo", "Diez", "010"),
            ("E1", "EST-001", "Grupo", "Uno", "001"),
            ("E9", "EST-009", "Grupo", "Nueve", "009"),
            ("E2", "EST-002", "Grupo", "Dos", "002"),
        ]
        with self.connection:
            self.connection.executemany(
                "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres, identificacion) "
                "VALUES (?, ?, ?, ?, ?)",
                students,
            )

        view = StudentsView(self.student_service, self.import_service)
        expected = ["EST-001", "EST-002", "EST-009", "EST-010", "EST-100"]
        self.assertEqual([view.table.item(row, 0).text() for row in range(view.table.rowCount())], expected)
        header = view.table.horizontalHeader()
        for column in range(view.table.columnCount()):
            self.assertEqual(header.sectionResizeMode(column), QHeaderView.Interactive)
        self.assertEqual(view.table.item(0, 1).toolTip(), "Grupo")
        self.assertEqual(view.table.item(0, 2).toolTip(), "Uno")

        view.search_input.setText("Grupo")
        self.assertEqual([view.table.item(row, 0).text() for row in range(view.table.rowCount())], expected)
