"""Vista contenedora del módulo de reportes académicos."""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.application.services.academic_summary_service import AcademicSummaryService
from src.application.services.report_export_service import ReportExportService
from src.presentation.views.academic_summary_view import AcademicSummaryView


class ReportsView(QWidget):
    def __init__(
        self,
        academic_summary_service: AcademicSummaryService,
        report_export_service: ReportExportService,
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.academic_summary_view = AcademicSummaryView(
            academic_summary_service=academic_summary_service,
            report_export_service=report_export_service,
        )
        layout.addWidget(self.academic_summary_view)

    def refresh_data(self) -> None:
        self.academic_summary_view.refresh_data()
