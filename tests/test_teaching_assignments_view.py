"""Pruebas mínimas de vista de asignaciones académicas."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

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
        self.assertIsNotNone(view.delete_button)
        self.assertFalse(hasattr(view, "search_input"))
        self.assertEqual(view.table.rowCount(), 0)
        headers = [view.table.horizontalHeaderItem(i).text() for i in range(view.table.columnCount())]
        self.assertEqual(headers, ["ID", "Docente", "Asignatura", "Curso", "Nombre", "Paralelo", "Período"])
        self.assertTrue(view.table.isColumnHidden(0))
        conn.close()

    def test_tabla_muestra_catalogos_y_conserva_id_oculto_para_crud(self) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QHeaderView, QMessageBox

        from src.application.services.catalog_service import CatalogService
        from src.application.services.teacher_service import TeacherService
        from src.application.services.teaching_assignment_service import TeachingAssignmentService
        from src.infrastructure.persistence.db import initialize_database
        from src.presentation.views.teaching_assignments_view import TeachingAssignmentsView

        conn = initialize_database(":memory:")
        teacher_service = TeacherService(conn)
        catalog_service = CatalogService(conn)
        assignment_service = TeachingAssignmentService(conn)
        teacher_service.crear_docente(
            {
                "id_docente": "D1",
                "nombres": "Ana",
                "apellidos": "Prueba",
                "identificacion": "DOC-001",
            }
        )
        catalog_service.crear_asignatura(
            {"id_asignatura": "ASSID-001", "nombre": "Matemática sintética", "codigo": "MAT-S"}
        )
        catalog_service.crear_periodo_lectivo(
            {
                "id_periodo": "2025-2026",
                "anio_inicio": 2025,
                "anio_fin": 2026,
                "fecha_inicio": None,
                "fecha_fin": None,
            }
        )
        ok, _ = assignment_service.crear_asignacion(
            {
                "docente_id": "D1",
                "asignatura_id": "ASSID-001",
                "curso_id": "CUR-007",
                "paralelo_id": "PAR-001",
                "periodo_id": "2025-2026",
            }
        )
        self.assertTrue(ok)

        view = TeachingAssignmentsView(assignment_service, teacher_service, catalog_service)
        self.assertEqual(view.table.rowCount(), 1)
        self.assertTrue(view.table.isColumnHidden(0))
        self.assertEqual(view.table.item(0, 1).text(), "Prueba Ana")
        self.assertEqual(view.table.item(0, 1).data(Qt.UserRole), "D1")
        self.assertEqual(view.table.item(0, 2).text(), "Matemática sintética")
        self.assertEqual(view.table.item(0, 3).text(), "CUR-007")
        self.assertEqual(view.table.item(0, 4).text(), "1ro BGU")
        self.assertEqual(view.table.item(0, 5).text(), "A")
        header = view.table.horizontalHeader()
        for column in range(1, view.table.columnCount()):
            self.assertEqual(header.sectionResizeMode(column), QHeaderView.Interactive)
        self.assertEqual(view.table.item(0, 2).toolTip(), "Matemática sintética")
        self.assertEqual(view.table.item(0, 4).toolTip(), "1ro BGU")

        assignment_id = assignment_service.listar_asignaciones()[0]["id_asignacion"]
        view.select_assignment(0, 0)
        self.assertEqual(view.selected_assignment_id, assignment_id)

        view.catalog_service.listar_asignaturas = lambda: []
        view.catalog_service.listar_paralelos = lambda: []
        view.load_assignments()
        self.assertEqual(view.table.item(0, 2).text(), "ASSID-001")
        self.assertEqual(view.table.item(0, 5).text(), "PAR-001")

        view.select_assignment(0, 0)
        with (
            patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes),
            patch.object(QMessageBox, "information"),
        ):
            view.delete_assignment()
        self.assertEqual(assignment_service.listar_asignaciones(), [])
        conn.close()

    def test_cancelar_advertencia_no_elimina_asignacion(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        from src.application.services.catalog_service import CatalogService
        from src.application.services.teacher_service import TeacherService
        from src.application.services.teaching_assignment_service import TeachingAssignmentService
        from src.infrastructure.persistence.db import initialize_database
        from src.presentation.views.teaching_assignments_view import TeachingAssignmentsView

        conn = initialize_database(":memory:")
        service = TeachingAssignmentService(conn)
        conn.execute(
            "INSERT INTO docentes (id_docente, nombres, apellidos, identificacion) "
            "VALUES ('D1', 'Ana', 'Prueba', 'DOC-1')"
        )
        conn.execute(
            "INSERT INTO asignaturas (id_asignatura, nombre, codigo) "
            "VALUES ('A1', 'Matematica', 'MAT')"
        )
        conn.execute(
            "INSERT INTO asignaciones_docente "
            "(id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) "
            "VALUES ('AD1', 'D1', 'A1', 'C1', 'P1', '2025')"
        )
        conn.commit()
        view = TeachingAssignmentsView(service, TeacherService(conn), CatalogService(conn))
        view.select_assignment(0, 0)
        with (
            patch.object(QMessageBox, "warning", return_value=QMessageBox.No) as warning,
            patch.object(service, "eliminar_asignacion") as delete,
        ):
            view.delete_assignment()
        warning.assert_called_once()
        self.assertEqual(warning.call_args.args[-1], QMessageBox.No)
        delete.assert_not_called()
        self.assertIsNotNone(service.repo.obtener_por_id("AD1"))
        conn.close()
