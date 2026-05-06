"""Exportador de reportes académicos a PDF con fidelidad de vista previa HTML."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from src.infrastructure.exporters.html_report_renderer import HtmlReportRenderer


class PdfReportExporter:
    def __init__(self, html_renderer: HtmlReportRenderer | None = None) -> None:
        self.html_renderer = html_renderer or HtmlReportRenderer()

    def exportar(
        self,
        output_path: str,
        report_title: str,
        context: dict[str, Any],
        rows: list[dict[str, Any]],
        ocultar_filas_vacias: bool = False,
    ) -> str:
        _ = report_title
        if not rows:
            raise ValueError("No hay datos para exportar")

        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        rendered = self._render_report_html(context, rows)
        if not rendered:
            raise RuntimeError("No se pudo renderizar la plantilla HTML del reporte")

        is_simplified_trimestral = bool(
            context.get("report_type") == "trimestral" and context.get("is_simplified_trimestral")
        )
        orientation = "portrait" if is_simplified_trimestral else (
            "landscape" if context.get("report_type") == "trimestral" else "portrait"
        )
        if not self.export_to_pdf(
            rendered,
            str(path),
            orientation=orientation,
            ocultar_filas_vacias=ocultar_filas_vacias,
        ):
            raise RuntimeError("No se pudo exportar el reporte PDF")
        return str(path)

    def _render_report_html(self, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        return self.html_renderer.render(context, rows)

    def export_to_pdf(
        self,
        html_content: str,
        output_path: str,
        orientation: str = "landscape",
        ocultar_filas_vacias: bool = False,
    ) -> bool:
        """Exporta HTML a PDF usando QWebEngineView offscreen."""
        try:
            from PySide6.QtCore import QEventLoop, QMarginsF, QTimer, QUrl
            from PySide6.QtGui import QPageLayout, QPageSize
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtWidgets import QApplication
        except Exception as exc:  # noqa: BLE001
            print(f"[Reportes] Motor Qt WebEngine no disponible: {exc}")
            return False

        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            page_orientation = QPageLayout.Landscape if orientation == "landscape" else QPageLayout.Portrait

            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageOrientation(page_orientation)
            printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Millimeter)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(output_path)

            page_layout = QPageLayout(
                QPageSize(QPageSize.A4),
                page_orientation,
                QMarginsF(10, 10, 10, 10),
                QPageLayout.Millimeter,
            )

            loop = QEventLoop()
            state = {"success": False, "finished": False, "timed_out": False}

            web_view = QWebEngineView()
            web_view.resize(1200, 900)
            web_view.setZoomFactor(1.0)

            def on_timeout() -> None:
                state["timed_out"] = True
                if not state["finished"]:
                    print("[Reportes] Timeout al esperar render/impresión de PDF")
                    loop.quit()

            timeout_timer = QTimer()
            timeout_timer.setSingleShot(True)
            timeout_timer.timeout.connect(on_timeout)
            timeout_timer.start(15000)

            def on_pdf_printed(path: str, pdf_ok: bool) -> None:
                state["finished"] = True
                timeout_timer.stop()
                exists = os.path.exists(path)
                size_ok = exists and os.path.getsize(path) > 0
                state["success"] = bool(pdf_ok and size_ok)
                if not state["success"]:
                    print(f"[Reportes] Error al imprimir PDF. ok={pdf_ok}, existe={exists}, size_ok={size_ok}")
                loop.quit()

            def on_load_finished(ok: bool) -> None:
                if not ok:
                    state["finished"] = True
                    timeout_timer.stop()
                    print("[Reportes] Falló carga HTML previa a impresión PDF")
                    loop.quit()
                    return

                web_view.setZoomFactor(1.0)
                try:
                    web_view.page().pdfPrintingFinished.connect(on_pdf_printed)
                except Exception as exc:  # noqa: BLE001
                    state["finished"] = True
                    timeout_timer.stop()
                    print(f"[Reportes] No se pudo conectar pdfPrintingFinished: {exc}")
                    loop.quit()
                    return
                if ocultar_filas_vacias:
                    self._ocultar_filas_antes_de_pdf(
                        web_view.page(),
                        lambda: QTimer.singleShot(300, lambda: web_view.page().printToPdf(output_path, page_layout)),
                    )
                else:
                    web_view.page().printToPdf(output_path, page_layout)

            web_view.loadFinished.connect(on_load_finished)
            web_view.setHtml(html_content, QUrl("about:blank"))
            loop.exec()

            try:
                web_view.loadFinished.disconnect(on_load_finished)
            except Exception:  # noqa: BLE001
                pass
            try:
                web_view.page().pdfPrintingFinished.disconnect(on_pdf_printed)
            except Exception:  # noqa: BLE001
                pass
            web_view.deleteLater()

            if state["timed_out"]:
                return False
            return bool(state["success"])
        except Exception as exc:  # noqa: BLE001
            print(f"[Reportes] Error inesperado al exportar PDF: {exc}")
            return False

    @staticmethod
    def _ocultar_filas_antes_de_pdf(page, callback) -> None:
        js = """
            (function() {
                function isEmptyCell(cell) {
                    if (!cell) { return true; }
                    var text = (cell.textContent || '').replace(/\\u00A0/g, '').trim();
                    var raw = (cell.innerHTML || '').trim().toLowerCase();
                    return text === '' || text === '—' || raw === '&nbsp;' || raw === '';
                }
                var rows = document.querySelectorAll('table.principal tbody tr');
                rows.forEach(function(row) {
                    var celdaNombre = row.cells[1];
                    if (isEmptyCell(celdaNombre)) {
                        row.style.display = 'none';
                    }
                });
                return true;
            })();
        """
        try:
            page.runJavaScript(js, lambda _result: callback())
        except Exception:  # noqa: BLE001
            callback()
