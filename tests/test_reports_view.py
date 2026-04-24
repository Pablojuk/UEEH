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
        return [
            {"id_asignacion": "AS1", "display": "Matemática | 8vo-A", "asignatura_nombre": "Matemática"},
            {"id_asignacion": "AS2", "display": "Animación | 8vo-A", "asignatura_nombre": "Animación a la Lectura"},
        ]

    def obtener_resumen_por_asignacion(self, asignacion_id: str) -> list[dict]:
        return []

    def obtener_reporte_anual(self, asignacion_id: str) -> list[dict]:
        return []

    def obtener_reporte_trimestral(self, asignacion_id: str, trimestre_num: int) -> list[dict]:
        return []

    def listar_firmantes_disponibles(self) -> list[dict]:
        return []

    def recalcular_resumenes(self, rows: list[dict]) -> list[dict]:
        return rows

    def guardar_supletorios(self, asignacion_id: str, rows: list[dict]) -> tuple[bool, str]:
        return True, "ok"


class _FakeReportExportService:
    def exportar_resumen_pdf(self, asignacion_id: str, output_path: str, report_type: str = "anual", trimestre_num: int | None = None) -> tuple[bool, str]:
        return False, "No hay datos para exportar"

    def exportar_resumen_excel(self, asignacion_id: str, output_path: str, report_type: str = "anual", trimestre_num: int | None = None) -> tuple[bool, str]:
        return False, "No hay datos para exportar"


class _FakeClassroomAccompanimentService:
    def listar_contextos_disponibles(self) -> list[dict]:
        return [
            {"id_asignacion": "AS1", "display": "Matemática | 8vo-A", "asignatura_nombre": "Matemática"},
            {"id_asignacion": "AS2", "display": "Animación | 8vo-A", "asignatura_nombre": "Animación a la Lectura"},
        ]

    def cargar_evaluacion(self, asignacion_id: str, trimestre_num: int) -> dict:
        return {
            "students": [],
            "skill_categories": [],
            "active_skills": [],
            "responses": {},
            "results": {},
            "validation_message": "",
        }

    def guardar_evaluacion(self, asignacion_id: str, trimestre_num: int, active_skills: list[str], responses: dict) -> tuple[bool, str]:
        return True, "ok"

    def calcular_resultado_estudiante(self, skill_values: dict[str, str], active_skills: list[str]) -> dict:
        return {
            "total_siempre": 0,
            "total_frecuentemente": 0,
            "total_ocasionalmente": 0,
            "total_nunca": 0,
            "puntaje_total_ponderado": 0,
            "valoracion_final": "",
            "validation_message": "",
        }

    def listar_firmantes_disponibles(self) -> list[str]:
        return []

    def obtener_contexto(self, asignacion_id: str) -> dict:
        return {
            "docente_apellidos": "",
            "docente_nombres": "",
            "curso_nombre": "",
            "paralelo_nombre": "",
            "curso_nivel": "",
            "periodo_id": "",
        }

    def obtener_datos_institucion(self) -> dict:
        return {"rector": "", "logo_path": "", "logo_ministerio_path": ""}


class _FakeGradeRegistrationService:
    def obtener_animacion_lectura_evaluacion(self, asignacion_id: str, trimestre_num: int, nivel: str | None = None) -> list[dict]:
        return [
            {
                "estudiante_id": "E1",
                "estudiante": "Lopez Maria",
                "valor": 8.5,
                "cualitativo": "B+",
                "cualitativo_1": "B",
            }
        ]

    def cargar_registro(self, asignacion_id: str, trimestre_num: int) -> list[dict]:
        return [
            {
                "estudiante_id": "E1",
                "estudiante": "Lopez Maria",
                "nota_trimestral": 8.5,
                "cualitativo": "B+",
                "cualitativo_adicional": "B",
            }
        ]


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestReportsView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_crear_vista_sin_error_y_botones_exportacion(self) -> None:
        from src.presentation.views.reports_view import ReportsView

        view = ReportsView(
            _FakeAcademicSummaryService(),
            _FakeReportExportService(),
            _FakeClassroomAccompanimentService(),
            _FakeGradeRegistrationService(),
        )
        summary_view = view.findChild(type(view.layout().itemAt(0).widget()))
        self.assertIsNotNone(summary_view)
        self.assertIsNotNone(view.academic_summary_view.export_pdf_button)
        self.assertIsNotNone(view.academic_summary_view.export_excel_button)

    def test_manejar_escenario_sin_datos_sin_romper(self) -> None:
        from src.presentation.views.reports_view import ReportsView

        view = ReportsView(
            _FakeAcademicSummaryService(),
            _FakeReportExportService(),
            _FakeClassroomAccompanimentService(),
            _FakeGradeRegistrationService(),
        )
        summary_view = view.academic_summary_view

        original = QFileDialog.getSaveFileName
        QFileDialog.getSaveFileName = staticmethod(lambda *args, **kwargs: ("", ""))
        try:
            summary_view.export_pdf()
            summary_view.export_excel()
        finally:
            QFileDialog.getSaveFileName = original

        self.assertEqual(summary_view.table.rowCount(), 0)

    def test_animacion_mantiene_combo_asignacion_y_sincroniza(self) -> None:
        from src.presentation.views.reports_view import ReportsView

        view = ReportsView(
            _FakeAcademicSummaryService(),
            _FakeReportExportService(),
            _FakeClassroomAccompanimentService(),
            _FakeGradeRegistrationService(),
        )
        summary_combo = view.academic_summary_view.assignment_combo
        animation_combo = view.animation_report_view.report_assignment_combo

        idx_animacion = summary_combo.findData("AS2")
        self.assertGreaterEqual(idx_animacion, 0)
        summary_combo.setCurrentIndex(idx_animacion)

        self.assertEqual(view.stack.currentWidget(), view.animation_report_view)
        self.assertGreater(animation_combo.count(), 1)
        self.assertEqual(animation_combo.currentData(), "AS2")
        self.assertTrue(view.animation_report_view.level_combo.isVisible())

        idx_mate = animation_combo.findData("AS1")
        self.assertGreaterEqual(idx_mate, 0)
        animation_combo.setCurrentIndex(idx_mate)
        self.assertEqual(summary_combo.currentData(), "AS1")


if __name__ == "__main__":
    unittest.main()
