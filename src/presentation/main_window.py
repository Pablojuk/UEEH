"""Ventana principal con navegación lateral."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from src.application.services.academic_summary_service import AcademicSummaryService
from src.application.services.backup_service import BackupService
from src.application.services.catalog_service import CatalogService
from src.application.services.enrollment_service import EnrollmentService
from src.application.services.grade_registration_service import GradeRegistrationService
from src.application.services.institution_service import InstitutionService
from src.application.services.report_export_service import ReportExportService
from src.application.services.student_import_service import StudentImportService
from src.application.services.student_service import StudentService
from src.application.services.teacher_service import TeacherService
from src.application.services.teaching_assignment_service import TeachingAssignmentService
from src.presentation.views.catalogs_view import CatalogsView
from src.presentation.views.dashboard_view import DashboardView
from src.presentation.views.enrollments_view import EnrollmentsView
from src.presentation.views.grades_view import GradesView
from src.presentation.views.institution_view import InstitutionView
from src.presentation.views.reports_view import ReportsView
from src.presentation.views.settings_view import SettingsView
from src.presentation.views.students_view import StudentsView
from src.presentation.views.teachers_view import TeachersView
from src.presentation.views.teaching_assignments_view import TeachingAssignmentsView
from src.presentation.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(
        self,
        institution_service: InstitutionService,
        teacher_service: TeacherService,
        catalog_service: CatalogService,
        student_service: StudentService,
        student_import_service: StudentImportService,
        enrollment_service: EnrollmentService,
        teaching_assignment_service: TeachingAssignmentService,
        grade_registration_service: GradeRegistrationService,
        academic_summary_service: AcademicSummaryService,
        report_export_service: ReportExportService,
        backup_service: BackupService,
    ) -> None:
        super().__init__()

        self.institution_service = institution_service
        self.teacher_service = teacher_service
        self.catalog_service = catalog_service
        self.student_service = student_service
        self.student_import_service = student_import_service
        self.enrollment_service = enrollment_service
        self.teaching_assignment_service = teaching_assignment_service
        self.grade_registration_service = grade_registration_service
        self.academic_summary_service = academic_summary_service
        self.report_export_service = report_export_service
        self.backup_service = backup_service

        self.setWindowTitle("Sistema Académico UEEH")
        self.resize(1180, 720)

        root = QWidget()
        self.setCentralWidget(root)

        container = QHBoxLayout(root)
        container.setContentsMargins(12, 12, 12, 12)
        container.setSpacing(12)

        self.sidebar = Sidebar()
        self.sidebar.section_selected.connect(self._change_view)

        right_panel = QFrame()
        right_panel.setObjectName("Card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)

        header_title = QLabel("Sistema de Gestión Académica")
        header_title.setObjectName("Title")
        header_subtitle = QLabel("Panel principal")
        header_subtitle.setObjectName("Subtitle")

        self.stack = QStackedWidget()
        self.views = {
            "dashboard": DashboardView(),
            "institution": InstitutionView(institution_service=self.institution_service),
            "teachers": TeachersView(teacher_service=self.teacher_service),
            "catalogs": CatalogsView(catalog_service=self.catalog_service),
            "students": StudentsView(
                student_service=self.student_service,
                student_import_service=self.student_import_service,
            ),
            "enrollments": EnrollmentsView(
                enrollment_service=self.enrollment_service,
                student_service=self.student_service,
                catalog_service=self.catalog_service,
            ),
            "teaching_assignments": TeachingAssignmentsView(
                teaching_assignment_service=self.teaching_assignment_service,
                teacher_service=self.teacher_service,
                catalog_service=self.catalog_service,
            ),
            "grades": GradesView(grade_registration_service=self.grade_registration_service),
            "reports": ReportsView(
                academic_summary_service=self.academic_summary_service,
                report_export_service=self.report_export_service,
            ),
            "settings": SettingsView(backup_service=self.backup_service),
        }

        for view in self.views.values():
            self.stack.addWidget(view)

        right_layout.addWidget(header_title)
        right_layout.addWidget(header_subtitle)
        right_layout.addWidget(self.stack, 1)

        container.addWidget(self.sidebar)
        container.addWidget(right_panel, 1)

        self._change_view("dashboard")

    def _change_view(self, section: str) -> None:
        widget = self.views.get(section)
        if widget is not None:
            self.stack.setCurrentWidget(widget)
