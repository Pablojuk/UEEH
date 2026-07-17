"""Pruebas del procesamiento de reportes fuera del hilo de interfaz."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtCore import QThread
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from src.application.services.report_export_service import PreparedReport
from src.presentation.workers.report_export_worker import ReportExportWorker


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class _RecordingService:
    def __init__(self) -> None:
        self.worker_thread = None

    def exportar_excel_preparado(self, report: PreparedReport) -> str:
        self.worker_thread = QThread.currentThread()
        return report.output_path

    def renderizar_html_preparado(self, _report: PreparedReport) -> str:
        self.worker_thread = QThread.currentThread()
        return "<html><body>Reporte sintético</body></html>"


def _prepared(kind: str) -> PreparedReport:
    return PreparedReport(
        export_kind=kind,
        output_path="reporte.xlsx" if kind == "excel" else "reporte.pdf",
        title="Reporte sintético",
        context={"report_type": "anual"},
        rows=[{"promedio": 8.0}],
    )


def test_excel_se_ejecuta_fuera_del_hilo_ui(qt_app) -> None:
    service = _RecordingService()
    worker = ReportExportWorker(service, _prepared("excel"))  # type: ignore[arg-type]
    completed = QSignalSpy(worker.completed)

    worker.start()

    assert worker.wait(5000)
    qt_app.processEvents()
    assert completed.count() == 1
    assert service.worker_thread is not qt_app.thread()
    assert completed.at(0)[0] is True


def test_jinja_para_pdf_se_ejecuta_fuera_del_hilo_ui(qt_app) -> None:
    service = _RecordingService()
    worker = ReportExportWorker(service, _prepared("pdf"))  # type: ignore[arg-type]
    rendered = QSignalSpy(worker.html_ready)

    worker.start()

    assert worker.wait(5000)
    qt_app.processEvents()
    assert rendered.count() == 1
    assert service.worker_thread is not qt_app.thread()
    assert "Reporte sintético" in rendered.at(0)[1]
