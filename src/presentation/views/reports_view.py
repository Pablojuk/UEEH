"""Vista contenedora del módulo de reportes académicos."""

from __future__ import annotations

import unicodedata

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from src.application.services.academic_summary_service import AcademicSummaryService
from src.application.services.classroom_accompaniment_service import ClassroomAccompanimentService
from src.application.services.report_export_service import ReportExportService
from src.presentation.views.academic_summary_view import AcademicSummaryView
from src.presentation.views.classroom_accompaniment_view import ClassroomAccompanimentView


class ReportsView(QWidget):
    def __init__(
        self,
        academic_summary_service: AcademicSummaryService,
        report_export_service: ReportExportService,
        classroom_accompaniment_service: ClassroomAccompanimentService,
    ) -> None:
        super().__init__()
        self.academic_summary_service = academic_summary_service
        self.classroom_accompaniment_service = classroom_accompaniment_service
        self._contexts_by_id: dict[str, dict] = {}

        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.academic_summary_view = AcademicSummaryView(
            academic_summary_service=academic_summary_service,
            report_export_service=report_export_service,
        )
        self.accompaniment_report_view = ClassroomAccompanimentView(
            accompaniment_service=classroom_accompaniment_service,
        )
        self.accompaniment_report_view.set_reports_mode(True)
        self.accompaniment_report_view.hide()

        self.stack.addWidget(self.academic_summary_view)
        self.stack.addWidget(self.accompaniment_report_view)
        layout.addWidget(self.stack)

        self.academic_summary_view.assignment_combo.currentIndexChanged.connect(self._sync_mode_from_summary_assignment)
        self.accompaniment_report_view.assignment_combo.currentIndexChanged.connect(self._sync_mode_from_accompaniment_assignment)
        self._refresh_contexts()
        self._sync_mode_from_summary_assignment()

    def refresh_data(self) -> None:
        self.academic_summary_view.refresh_data()
        self.accompaniment_report_view.load_contexts(
            selected_assignment_id=str(self.academic_summary_view.assignment_combo.currentData() or "")
        )
        self._refresh_contexts()
        self._sync_mode_from_summary_assignment()

    def _refresh_contexts(self) -> None:
        contexts = self.academic_summary_service.listar_contextos_disponibles()
        self._contexts_by_id = {str(row.get("id_asignacion")): row for row in contexts if row.get("id_asignacion")}

    def _sync_mode_from_summary_assignment(self) -> None:
        assignment_id = self.academic_summary_view.assignment_combo.currentData()
        assignment_id_str = str(assignment_id or "")
        if self._is_accompaniment_assignment(assignment_id_str):
            self.stack.setCurrentWidget(self.accompaniment_report_view)
            idx = self.accompaniment_report_view.assignment_combo.findData(assignment_id)
            if idx >= 0:
                self.accompaniment_report_view.assignment_combo.setCurrentIndex(idx)
            self.accompaniment_report_view.load_rows()
        else:
            self.stack.setCurrentWidget(self.academic_summary_view)

    def _sync_mode_from_accompaniment_assignment(self) -> None:
        assignment_id = self.accompaniment_report_view.assignment_combo.currentData()
        assignment_id_str = str(assignment_id or "")
        if not self._is_accompaniment_assignment(assignment_id_str):
            idx = self.academic_summary_view.assignment_combo.findData(assignment_id)
            if idx >= 0:
                self.academic_summary_view.assignment_combo.setCurrentIndex(idx)
            self.stack.setCurrentWidget(self.academic_summary_view)

    def _is_accompaniment_assignment(self, assignment_id: str) -> bool:
        if not assignment_id:
            return False
        context = self._contexts_by_id.get(assignment_id, {})
        subject_name = self._normalize_text(str(context.get("asignatura_nombre") or ""))
        return subject_name == self._normalize_text("acompañamiento integral en el aula")

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFD", str(value or "").strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())
