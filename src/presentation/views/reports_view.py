"""Vista contenedora del módulo de reportes académicos."""

from __future__ import annotations

import unicodedata

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from src.application.services.academic_summary_service import AcademicSummaryService
from src.application.services.classroom_accompaniment_service import ClassroomAccompanimentService
from src.application.services.grade_registration_service import GradeRegistrationService
from src.application.services.report_export_service import ReportExportService
from src.presentation.views.academic_summary_view import AcademicSummaryView
from src.presentation.views.animacion_lectura_view import AnimacionLecturaView
from src.presentation.views.classroom_accompaniment_view import ClassroomAccompanimentView


class ReportsView(QWidget):
    MODE_SUMMARY = "summary"
    MODE_ACCOMPANIMENT = "accompaniment"
    MODE_ANIMATION = "animation"

    def __init__(
        self,
        academic_summary_service: AcademicSummaryService,
        report_export_service: ReportExportService,
        classroom_accompaniment_service: ClassroomAccompanimentService,
        grade_registration_service: GradeRegistrationService,
    ) -> None:
        super().__init__()
        self.academic_summary_service = academic_summary_service
        self.classroom_accompaniment_service = classroom_accompaniment_service
        self.grade_registration_service = grade_registration_service
        self._contexts_by_id: dict[str, dict] = {}
        self._syncing_mode = False

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
        self.animation_report_view = AnimacionLecturaView(
            list_signers=classroom_accompaniment_service.listar_firmantes_disponibles,
            get_assignment_context=classroom_accompaniment_service.obtener_contexto,
            get_institution_data=classroom_accompaniment_service.obtener_datos_institucion,
        )
        self.animation_report_view.set_reports_mode(True)
        self.animation_report_view.hide()

        self.stack.addWidget(self.academic_summary_view)
        self.stack.addWidget(self.accompaniment_report_view)
        self.stack.addWidget(self.animation_report_view)
        layout.addWidget(self.stack)

        self.academic_summary_view.assignment_combo.currentIndexChanged.connect(self._sync_mode_from_summary_assignment)
        self.academic_summary_view.report_type_combo.currentIndexChanged.connect(self._sync_mode_from_summary_assignment)
        self.accompaniment_report_view.assignment_combo.currentIndexChanged.connect(self._sync_mode_from_accompaniment_assignment)
        self.animation_report_view.report_assignment_combo.currentIndexChanged.connect(self._sync_mode_from_animation_assignment)
        self.animation_report_view.report_trimester_combo.currentIndexChanged.connect(self._sync_mode_from_animation_trimester)
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
        if self._syncing_mode:
            return
        self._syncing_mode = True
        assignment_id = self.academic_summary_view.assignment_combo.currentData()
        assignment_id_str = str(assignment_id or "")
        try:
            mode = self._get_report_mode(assignment_id_str)
            report_type, trimester_num = self.academic_summary_view.report_type_combo.currentData()
            trimester = int(trimester_num) if report_type == "trimestral" and trimester_num else 1
            if mode == self.MODE_ACCOMPANIMENT:
                self.stack.setCurrentWidget(self.accompaniment_report_view)
                idx = self.accompaniment_report_view.assignment_combo.findData(assignment_id)
                if idx >= 0:
                    self.accompaniment_report_view.assignment_combo.setCurrentIndex(idx)
                self.accompaniment_report_view.load_rows()
            elif mode == self.MODE_ANIMATION:
                self.stack.setCurrentWidget(self.animation_report_view)
                self.animation_report_view.configure_report_filters(
                    list(self._contexts_by_id.values()),
                    selected_assignment_id=assignment_id_str,
                    selected_trimester=trimester,
                )
                self.animation_report_view.set_context(
                    assignment_id=str(assignment_id) if assignment_id else None,
                    assignment_label=self.academic_summary_view.assignment_combo.currentText(),
                    trimester_num=trimester,
                    trimester_label=f"Trimestre {trimester}",
                )
                self.animation_report_view.set_students(self._load_animation_students(str(assignment_id), trimester))
            else:
                self.stack.setCurrentWidget(self.academic_summary_view)
        finally:
            self._syncing_mode = False

    def _sync_mode_from_accompaniment_assignment(self) -> None:
        if self._syncing_mode:
            return
        assignment_id = self.accompaniment_report_view.assignment_combo.currentData()
        idx = self.academic_summary_view.assignment_combo.findData(assignment_id)
        if idx >= 0 and idx != self.academic_summary_view.assignment_combo.currentIndex():
            self.academic_summary_view.assignment_combo.setCurrentIndex(idx)
            return
        self._sync_mode_from_summary_assignment()

    def _sync_mode_from_animation_assignment(self) -> None:
        if self._syncing_mode:
            return
        assignment_id = self.animation_report_view.report_assignment_combo.currentData()
        idx = self.academic_summary_view.assignment_combo.findData(assignment_id)
        if idx >= 0 and idx != self.academic_summary_view.assignment_combo.currentIndex():
            self.academic_summary_view.assignment_combo.setCurrentIndex(idx)
            return
        self._sync_mode_from_summary_assignment()

    def _sync_mode_from_animation_trimester(self) -> None:
        if self._syncing_mode:
            return
        trimester = self.animation_report_view.report_trimester_combo.currentData()
        if trimester is None:
            return
        idx = self.academic_summary_view.report_type_combo.findData(("trimestral", int(trimester)))
        if idx >= 0 and idx != self.academic_summary_view.report_type_combo.currentIndex():
            self.academic_summary_view.report_type_combo.setCurrentIndex(idx)
            return
        self._sync_mode_from_summary_assignment()

    def _is_accompaniment_assignment(self, assignment_id: str) -> bool:
        if not assignment_id:
            return False
        context = self._contexts_by_id.get(assignment_id, {})
        subject_name = self._normalize_text(str(context.get("asignatura_nombre") or ""))
        return subject_name == self._normalize_text("acompañamiento integral en el aula")

    def _is_animation_assignment(self, assignment_id: str) -> bool:
        if not assignment_id:
            return False
        context = self._contexts_by_id.get(assignment_id, {})
        subject_name = self._normalize_text(str(context.get("asignatura_nombre") or ""))
        return subject_name == self._normalize_text("animacion a la lectura")

    def _get_report_mode(self, assignment_id: str) -> str:
        if self._is_accompaniment_assignment(assignment_id):
            return self.MODE_ACCOMPANIMENT
        if self._is_animation_assignment(assignment_id):
            return self.MODE_ANIMATION
        return self.MODE_SUMMARY

    def _load_animation_students(self, assignment_id: str, trimester_num: int) -> list[dict[str, str]]:
        if not assignment_id:
            return []
        try:
            rows = self.grade_registration_service.obtener_animacion_lectura_evaluacion(assignment_id, int(trimester_num))
            if not rows:
                rows = self.grade_registration_service.cargar_registro(assignment_id, int(trimester_num))
        except ValueError:
            return []
        return [
            {
                "estudiante_id": str(row.get("estudiante_id") or ""),
                "estudiante": str(row.get("estudiante") or ""),
                "valor": row.get("valor", row.get("nota_trimestral")),
                "cualitativo": str(row.get("cualitativo") or ""),
                "cualitativo_1": str(row.get("cualitativo_1", row.get("cualitativo_adicional")) or ""),
            }
            for row in rows
        ]

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFD", str(value or "").strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())
