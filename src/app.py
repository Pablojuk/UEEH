"""Punto de entrada visual de la aplicación."""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

from src.application.services.academic_summary_service import AcademicSummaryService
from src.application.services.backup_service import BackupService
from src.application.services.catalog_service import CatalogService
from src.application.services.classroom_accompaniment_service import ClassroomAccompanimentService
from src.application.services.enrollment_service import EnrollmentService
from src.application.services.grade_registration_service import GradeRegistrationService
from src.application.services.institution_service import InstitutionService
from src.application.services.report_export_service import ReportExportService
from src.application.services.setup_service import SetupService
from src.application.services.student_import_service import StudentImportService
from src.application.services.student_service import StudentService
from src.application.services.teacher_service import TeacherService
from src.application.services.teaching_assignment_service import TeachingAssignmentService
from src.infrastructure.persistence.db import DEFAULT_DB_PATH, initialize_database
from src.presentation.main_window import MainWindow
from src.presentation.styles import APP_STYLE
from src.presentation.views.login_view import LoginView
from src.presentation.views.setup_view import SetupView


def run_application() -> int:
    """Inicializa app, estado inicial y ventana principal."""
    os.environ.setdefault("QT_QPA_PLATFORM", "windows" if os.name == "nt" else "xcb")

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    connection = initialize_database()
    setup_service = SetupService(connection)
    institution_service = InstitutionService(connection)
    teacher_service = TeacherService(connection)
    catalog_service = CatalogService(connection)
    student_service = StudentService(connection)
    student_import_service = StudentImportService(student_service)
    enrollment_service = EnrollmentService(connection)
    teaching_assignment_service = TeachingAssignmentService(connection)
    grade_registration_service = GradeRegistrationService(connection)
    academic_summary_service = AcademicSummaryService(connection)
    report_export_service = ReportExportService(
        connection=connection,
        academic_summary_service=academic_summary_service,
        institution_service=institution_service,
    )
    backup_service = BackupService(str(DEFAULT_DB_PATH))
    classroom_accompaniment_service = ClassroomAccompanimentService(connection)

    if setup_service.es_primer_uso():
        setup_dialog = SetupView(setup_service=setup_service, institution_service=institution_service)
        if setup_dialog.exec() != SetupView.Accepted:
            connection.close()
            return 0

    login_dialog = LoginView(setup_service=setup_service)
    if login_dialog.exec() != LoginView.Accepted:
        connection.close()
        return 0

    window = MainWindow(
        institution_service=institution_service,
        teacher_service=teacher_service,
        catalog_service=catalog_service,
        student_service=student_service,
        student_import_service=student_import_service,
        enrollment_service=enrollment_service,
        teaching_assignment_service=teaching_assignment_service,
        grade_registration_service=grade_registration_service,
        academic_summary_service=academic_summary_service,
        report_export_service=report_export_service,
        backup_service=backup_service,
        classroom_accompaniment_service=classroom_accompaniment_service,
    )
    window.show()

    exit_code = app.exec()
    connection.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(run_application())
