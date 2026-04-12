"""Servicio de exportación de reportes académicos."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from src.application.services.academic_summary_service import AcademicSummaryService
from src.application.services.institution_service import InstitutionService
from src.infrastructure.exporters.excel_report_exporter import ExcelReportExporter
from src.infrastructure.exporters.pdf_report_exporter import PdfReportExporter


class ReportExportService:
    """Prepara contexto y delega exportación a PDF/Excel."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        academic_summary_service: AcademicSummaryService,
        institution_service: InstitutionService,
        pdf_exporter: PdfReportExporter | None = None,
        excel_exporter: ExcelReportExporter | None = None,
    ) -> None:
        self.connection = connection
        self.academic_summary_service = academic_summary_service
        self.institution_service = institution_service
        self.pdf_exporter = pdf_exporter or PdfReportExporter()
        self.excel_exporter = excel_exporter or ExcelReportExporter()

    def exportar_resumen_pdf(
        self,
        asignacion_id: str,
        output_path: str,
        report_type: str = "anual",
        trimestre_num: int | None = None,
        firmantes: dict[str, str] | None = None,
    ) -> tuple[bool, str]:
        return self._exportar(
            asignacion_id,
            output_path,
            export_kind="pdf",
            report_type=report_type,
            trimestre_num=trimestre_num,
            firmantes=firmantes,
        )

    def exportar_resumen_excel(
        self,
        asignacion_id: str,
        output_path: str,
        report_type: str = "anual",
        trimestre_num: int | None = None,
        firmantes: dict[str, str] | None = None,
    ) -> tuple[bool, str]:
        return self._exportar(
            asignacion_id,
            output_path,
            export_kind="excel",
            report_type=report_type,
            trimestre_num=trimestre_num,
            firmantes=firmantes,
        )

    def _exportar(
        self,
        asignacion_id: str,
        output_path: str,
        export_kind: str,
        report_type: str,
        trimestre_num: int | None,
        firmantes: dict[str, str] | None,
    ) -> tuple[bool, str]:
        if not str(asignacion_id or "").strip():
            return False, "Debe seleccionar una asignación"

        try:
            context = self._build_context(asignacion_id)
            context["report_type"] = report_type
            context["trimestre_num"] = trimestre_num
            context["firmantes"] = firmantes or {}
            rows = (
                self.academic_summary_service.obtener_reporte_trimestral(asignacion_id, trimestre_num or 1)
                if report_type == "trimestral"
                else self.academic_summary_service.obtener_reporte_anual(asignacion_id)
            )
            if not rows or not self._hay_datos_exportables(rows, report_type):
                return False, "No hay datos para exportar"

            normalized_path = self._normalize_output_path(output_path, export_kind)
            if export_kind == "pdf":
                title = "Cuadro de Calificación Trimestral" if report_type == "trimestral" else "Cuadro de Calificación Anual"
                result_path = self.pdf_exporter.exportar(normalized_path, title, context, rows)
            else:
                title = "Cuadro de Calificación Trimestral" if report_type == "trimestral" else "Cuadro de Calificación Anual"
                result_path = self.excel_exporter.exportar(normalized_path, title, context, rows)
            return True, f"Archivo generado: {result_path}"
        except Exception as exc:
            return False, f"Error al exportar: {exc}"

    def _build_context(self, asignacion_id: str) -> dict[str, Any]:
        context = next(
            (c for c in self.academic_summary_service.listar_contextos_disponibles() if c.get("id_asignacion") == asignacion_id),
            None,
        )
        if not context:
            raise ValueError("Asignación no encontrada")

        institucion = self.institution_service.obtener_actual() or {}
        return {
            "contexto_display": context.get("display", asignacion_id),
            "institucion_nombre": institucion.get("nombre"),
            "docente_id": context.get("docente_id"),
            "asignatura_id": context.get("asignatura_id"),
            "curso_id": context.get("curso_id"),
            "paralelo_id": context.get("paralelo_id"),
            "periodo_id": context.get("periodo_id"),
            "docente_nombre": f"{context.get('docente_apellidos', '')} {context.get('docente_nombres', '')}".strip(),
            "asignatura_nombre": context.get("asignatura_nombre") or context.get("asignatura_id"),
            "curso_nombre": context.get("curso_nombre") or context.get("curso_id"),
            "curso_nivel": context.get("curso_nivel"),
            "paralelo_nombre": context.get("paralelo_nombre") or context.get("paralelo_id"),
            "logo_path": institucion.get("logo_path"),
            "logo_ministerio_path": institucion.get("logo_ministerio_path"),
            "institucion": institucion,
        }

    @staticmethod
    def _normalize_output_path(output_path: str, export_kind: str) -> str:
        text = str(output_path or "").strip()
        if not text:
            raise ValueError("Ruta de salida inválida")

        path = Path(text).expanduser().resolve()
        suffix = ".pdf" if export_kind == "pdf" else ".xlsx"
        if path.suffix.lower() != suffix:
            path = path.with_suffix(suffix)
        return str(path)

    @staticmethod
    def _hay_datos_exportables(rows: list[dict[str, Any]], report_type: str) -> bool:
        if report_type == "trimestral":
            return any(row.get("promedio_final") is not None for row in rows)
        for row in rows:
            if any(
                row.get(k) is not None
                for k in ("trimestre_1", "trimestre_2", "trimestre_3", "promedio", "supletorio")
            ):
                return True
        return False
