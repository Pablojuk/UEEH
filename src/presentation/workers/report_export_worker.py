"""Trabajador para renderizado Jinja2 y escritura Excel fuera del hilo UI."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from src.application.services.report_export_service import PreparedReport, ReportExportService


class ReportExportWorker(QThread):
    """Procesa la parte no visual de una exportación académica."""

    completed = Signal(bool, str)
    html_ready = Signal(object, str)

    def __init__(
        self,
        service: ReportExportService,
        report: PreparedReport,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.service = service
        self.report = report

    def run(self) -> None:
        try:
            if self.report.export_kind == "excel":
                output_path = self.service.exportar_excel_preparado(self.report)
                self.completed.emit(True, f"Archivo generado: {output_path}")
                return

            html_content = self.service.renderizar_html_preparado(self.report)
            self.html_ready.emit(self.report, html_content)
        except Exception as exc:  # noqa: BLE001
            self.completed.emit(False, f"Error al exportar: {exc}")
