"""Pruebas mínimas de vista de matrículas."""

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
        self.assertTrue(view.student_combo.isHidden())
        self.assertFalse(view.student_filter_input.isHidden())
        self.assertIsNotNone(view.table)
        self.assertIsNotNone(view.delete_button)
        self.assertEqual(view.bulk_select_button.text(), "Selec. Estu.")
        self.assertFalse(hasattr(view, "search_input"))
        self.assertEqual(view.table.rowCount(), 0)
        self.assertTrue(view.table.isColumnHidden(0))
        conn.close()

    def test_tabla_filtra_por_curso_y_busca_por_codigo(self) -> None:
        from src.application.services.catalog_service import CatalogService
        from src.application.services.enrollment_service import EnrollmentService
        from src.application.services.student_service import StudentService
        from src.infrastructure.persistence.db import initialize_database
        from src.presentation.views.enrollments_view import EnrollmentsView

        conn = initialize_database(":memory:")
        with conn:
            conn.execute(
                "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres, identificacion) VALUES (?, ?, ?, ?, ?)",
                ("E1", "EST-001", "Lopez", "Ana", "0101"),
            )
            conn.execute(
                "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres, identificacion) VALUES (?, ?, ?, ?, ?)",
                ("E2", "EST-002", "Perez", "Luis", "0202"),
            )
            conn.execute(
                "INSERT INTO periodos_lectivos (id_periodo, anio_inicio, anio_fin, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?, ?)",
                ("2025-2026", 2025, 2026, None, None),
            )
            conn.execute(
                "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id, numero_lista) VALUES (?, ?, ?, ?, ?, ?)",
                ("M1", "E1", "CUR-007", "PAR-001", "2025-2026", 1),
            )
            conn.execute(
                "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id, numero_lista) VALUES (?, ?, ?, ?, ?, ?)",
                ("M2", "E2", "CUR-008", "PAR-001", "2025-2026", 2),
            )

        view = EnrollmentsView(EnrollmentService(conn), StudentService(conn), CatalogService(conn))
        index_c7 = view.course_combo.findData("CUR-007")
        view.course_combo.setCurrentIndex(index_c7)
        view.load_enrollments()
        self.assertEqual(view.table.rowCount(), 1)
        self.assertEqual(view.table.item(0, 2).text(), "CUR-007")
        self.assertEqual(view.table.item(0, 3).text(), "1ro BGU")

        index_c9 = view.course_combo.findData("CUR-009")
        view.course_combo.setCurrentIndex(index_c9)
        view.load_enrollments()
        self.assertEqual(view.table.rowCount(), 0)

        view.student_completer.setCompletionPrefix("eSt-002")
        self.assertEqual(view.student_completer.completionCount(), 1)
        conn.close()

    def test_autocompletado_valida_limpia_y_conserva_id_oculto_para_crud(self) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QHeaderView, QMessageBox

        from src.application.services.catalog_service import CatalogService
        from src.application.services.enrollment_service import EnrollmentService
        from src.application.services.student_service import StudentService
        from src.infrastructure.persistence.db import initialize_database
        from src.presentation.views.enrollments_view import EnrollmentsView

        conn = initialize_database(":memory:")
        with conn:
            conn.execute(
                "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres, identificacion) "
                "VALUES (?, ?, ?, ?, ?)",
                ("E1", "EST-001", "Perez", "Ana", "0101"),
            )
            conn.execute(
                "INSERT INTO periodos_lectivos (id_periodo, anio_inicio, anio_fin, fecha_inicio, fecha_fin) "
                "VALUES (?, ?, ?, ?, ?)",
                ("2025-2026", 2025, 2026, None, None),
            )

        enrollment_service = EnrollmentService(conn)
        catalog_service = CatalogService(conn)
        view = EnrollmentsView(enrollment_service, StudentService(conn), catalog_service)

        self.assertEqual(view.completer_model.rowCount(), 1)
        model_index = view.completer_model.index(0, 0)
        self.assertEqual(model_index.data(Qt.DisplayRole), "Perez Ana - 0101 - EST-001")
        self.assertEqual(model_index.data(Qt.UserRole), "E1")
        self.assertEqual(view.student_completer.filterMode(), Qt.MatchContains)
        self.assertEqual(view.student_completer.caseSensitivity(), Qt.CaseInsensitive)

        view.student_completer.setCompletionPrefix("pErEz")
        self.assertEqual(view.student_completer.completionCount(), 1)
        view.student_completer.setCompletionPrefix("010")
        self.assertEqual(view.student_completer.completionCount(), 1)

        view.on_student_selected(model_index)
        self.assertEqual(view.selected_student_id, "E1")
        view.student_filter_input.setText("Perez Ana editado")
        self.assertIsNone(view.selected_student_id)

        with patch.object(QMessageBox, "warning") as warning:
            view.save_enrollment()
        warning.assert_called_once_with(view, "Validación", "Seleccione un estudiante válido.")
        self.assertEqual(enrollment_service.listar_matriculas(), [])

        view.on_student_selected(model_index)
        view.course_combo.setCurrentIndex(view.course_combo.findData("CUR-007"))
        view.parallel_combo.setCurrentIndex(view.parallel_combo.findData("PAR-001"))
        view.period_combo.setCurrentIndex(view.period_combo.findData("2025-2026"))
        with patch.object(QMessageBox, "information"):
            view.save_enrollment()

        self.assertIsNone(view.selected_student_id)
        self.assertEqual(view.selected_student_display, "")
        self.assertEqual(view.student_filter_input.text(), "")
        self.assertEqual(view.table.rowCount(), 1)
        self.assertTrue(view.table.isColumnHidden(0))
        self.assertEqual(view.table.item(0, 4).text(), "A")
        header = view.table.horizontalHeader()
        for column in range(1, view.table.columnCount()):
            self.assertEqual(header.sectionResizeMode(column), QHeaderView.Interactive)
        self.assertEqual(view.table.item(0, 1).toolTip(), "Perez Ana")
        self.assertEqual(view.table.item(0, 3).toolTip(), "1ro BGU")

        enrollment_id = enrollment_service.listar_matriculas()[0]["id_matricula"]
        view.select_enrollment(0, 0)
        self.assertEqual(view.selected_enrollment_id, enrollment_id)

        view.catalog_service.listar_paralelos = lambda: []
        view.load_enrollments()
        self.assertEqual(view.table.item(0, 4).text(), "PAR-001")

        view.select_enrollment(0, 0)
        with (
            patch.object(QMessageBox, "question", return_value=QMessageBox.Yes),
            patch.object(QMessageBox, "information"),
        ):
            view.delete_enrollment()
        self.assertEqual(enrollment_service.listar_matriculas(), [])
        conn.close()

    def test_modal_conserva_checks_al_cambiar_filtro(self) -> None:
        from src.application.services.enrollment_service import EnrollmentService
        from src.infrastructure.persistence.db import initialize_database
        from src.presentation.views.enrollments_view import BulkEnrollmentDialog

        conn = initialize_database(":memory:")
        service = EnrollmentService(conn)
        students = [
            {"id_estudiante": "E1", "codigo": "EST-129", "apellidos": "Lopez", "nombres": "Ana", "identificacion": "0101"},
            {"id_estudiante": "E2", "codigo": "EST-130", "apellidos": "Perez", "nombres": "Luis", "identificacion": "0202"},
        ]
        dialog = BulkEnrollmentDialog(
            enrollment_service=service,
            students=students,
            courses=[{"id_curso": "CUR-007", "nombre": "1ro BGU"}],
            parallels=[{"id_paralelo": "PAR-001", "nombre": "A"}],
            periods=[{"id_periodo": "2025-2026"}],
            selected_course="CUR-007",
            selected_parallel="PAR-001",
            selected_period="2025-2026",
        )
        dialog.search_input.setText("EST-129")
        dialog._render_students()
        dialog.table.item(0, 0).setCheckState(2)
        dialog.search_input.setText("EST-130")
        dialog._render_students()
        dialog.table.item(0, 0).setCheckState(2)
        dialog.search_input.clear()
        dialog._render_students()
        self.assertEqual(set(dialog._selected_students()), {"E1", "E2"})
        conn.close()
