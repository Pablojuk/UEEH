"""Pruebas mínimas de vista de reportes/exportación."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QFileDialog
except ImportError:  # pragma: no cover
    QApplication = None
    QFileDialog = None


class _FakeAcademicSummaryService:
    def listar_contextos_disponibles(self) -> list[dict]:
        return [{"id_asignacion": "AS1", "display": "Contexto demo"}]

    def obtener_resumen_por_asignacion(self, asignacion_id: str) -> list[dict]:
        return []

    def recalcular_resumenes(self, rows: list[dict]) -> list[dict]:
        return rows

    def guardar_supletorios(self, asignacion_id: str, rows: list[dict]) -> tuple[bool, str]:
        return True, "ok"


class _FakeReportExportService:
    def exportar_resumen_pdf(self, asignacion_id: str, output_path: str) -> tuple[bool, str]:
        return False, "No hay datos para exportar"

    def exportar_resumen_excel(self, asignacion_id: str, output_path: str) -> tuple[bool, str]:
        return False, "No hay datos para exportar"


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestReportsView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_crear_vista_sin_error_y_botones_exportacion(self) -> None:
        from src.presentation.views.reports_view import ReportsView

        view = ReportsView(_FakeAcademicSummaryService(), _FakeReportExportService())
        summary_view = view.findChild(type(view.layout().itemAt(0).widget()))
        self.assertIsNotNone(summary_view)
        self.assertIsNotNone(summary_view.export_pdf_button)
        self.assertIsNotNone(summary_view.export_excel_button)

    def test_manejar_escenario_sin_datos_sin_romper(self) -> None:
        from src.presentation.views.reports_view import ReportsView

        view = ReportsView(_FakeAcademicSummaryService(), _FakeReportExportService())
        summary_view = view.layout().itemAt(0).widget()

        original = QFileDialog.getSaveFileName
        QFileDialog.getSaveFileName = staticmethod(lambda *args, **kwargs: ("", ""))
        try:
            summary_view.export_pdf()
            summary_view.export_excel()
        finally:
            QFileDialog.getSaveFileName = original

        self.assertEqual(summary_view.table.rowCount(), 0)


if __name__ == "__main__":
    unittest.main()
