"""Pruebas smoke de UI para BLOQUE 4."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestUISmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_import_app_module(self) -> None:
        from src import app  # noqa: F401

    def test_creacion_ventana_principal(self) -> None:
        from PySide6.QtCore import qInstallMessageHandler

        from src.application.services.academic_summary_service import AcademicSummaryService
        from src.application.services.attendance_service import AttendanceService
        from src.application.services.backup_service import BackupService
        from src.application.services.catalog_service import CatalogService
        from src.application.services.classroom_accompaniment_service import ClassroomAccompanimentService
        from src.application.services.report_export_service import ReportExportService
        from src.application.services.enrollment_service import EnrollmentService
        from src.application.services.grade_registration_service import GradeRegistrationService
        from src.application.services.institution_service import InstitutionService
        from src.application.services.student_import_service import StudentImportService
        from src.application.services.student_service import StudentService
        from src.application.services.teacher_service import TeacherService
        from src.application.services.teaching_assignment_service import TeachingAssignmentService
        from src.infrastructure.persistence.db import initialize_database
        from src.presentation.main_window import MainWindow
        from src.presentation.styles import APP_STYLE

        conn = initialize_database(":memory:")
        student_service = StudentService(conn)
        messages: list[str] = []

        def message_handler(_message_type, _context, message) -> None:
            messages.append(str(message))

        previous_handler = qInstallMessageHandler(message_handler)
        previous_style = self.app.styleSheet()
        try:
            self.app.setStyleSheet(APP_STYLE)
            window = MainWindow(
                institution_service=InstitutionService(conn),
                teacher_service=TeacherService(conn),
                catalog_service=CatalogService(conn),
                student_service=student_service,
                student_import_service=StudentImportService(student_service),
                enrollment_service=EnrollmentService(conn),
                teaching_assignment_service=TeachingAssignmentService(conn),
                grade_registration_service=GradeRegistrationService(conn),
                academic_summary_service=AcademicSummaryService(conn),
                report_export_service=ReportExportService(
                    connection=conn,
                    academic_summary_service=AcademicSummaryService(conn),
                    institution_service=InstitutionService(conn),
                ),
                backup_service=BackupService(":memory:"),
                classroom_accompaniment_service=ClassroomAccompanimentService(conn),
                attendance_service=AttendanceService(conn),
            )
            self.app.processEvents()
        finally:
            self.app.setStyleSheet(previous_style)
            qInstallMessageHandler(previous_handler)

        self.assertEqual(window.windowTitle(), "Sistema Académico UEEH")
        self.assertNotIn("classroom_accompaniment", window.sidebar._buttons)
        self.assertFalse(any("QFont::setPointSize: Point size <= 0" in message for message in messages))
        conn.close()
