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

    def exportar_resumen_pdf(self, asignacion_id: str, output_path: str) -> tuple[bool, str]:
        return self._exportar(asignacion_id, output_path, export_kind="pdf")

    def exportar_resumen_excel(self, asignacion_id: str, output_path: str) -> tuple[bool, str]:
        return self._exportar(asignacion_id, output_path, export_kind="excel")

    def _exportar(self, asignacion_id: str, output_path: str, export_kind: str) -> tuple[bool, str]:
        if not str(asignacion_id or "").strip():
            return False, "Debe seleccionar una asignación"

        try:
            context = self._build_context(asignacion_id)
            rows = self.academic_summary_service.obtener_resumen_por_asignacion(asignacion_id)
            if not rows or not self._hay_datos_exportables(rows):
                return False, "No hay datos para exportar"

            normalized_path = self._normalize_output_path(output_path, export_kind)
            if export_kind == "pdf":
                result_path = self.pdf_exporter.exportar(normalized_path, "Reporte Académico Resumido", context, rows)
            else:
                result_path = self.excel_exporter.exportar(normalized_path, "Reporte Académico Resumido", context, rows)
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
    def _hay_datos_exportables(rows: list[dict[str, Any]]) -> bool:
        for row in rows:
            if any(row.get(k) is not None for k in ("trimestre_1", "trimestre_2", "trimestre_3", "supletorio")):
                return True
        return False
