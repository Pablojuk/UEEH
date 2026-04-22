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
        self.assertIsNotNone(view.delete_button)
        self.assertEqual(view.bulk_select_button.text(), "Selec. Estu.")
        self.assertFalse(hasattr(view, "search_input"))
        self.assertEqual(view.table.rowCount(), 0)
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

        view.student_filter_input.setText("EST-002")
        self.assertEqual(view.student_combo.count(), 1)
        self.assertEqual(view.student_combo.currentData(), "E2")
        conn.close()
