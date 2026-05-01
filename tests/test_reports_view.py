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
            {"id_asignacion": "AS2", "display": "Animación | 8vo-A", "asignatura_nombre": "  ANIMACIÓN   A   LA   LECTURA  "},
            {"id_asignacion": "AS3", "display": "Acompañamiento | 8vo-A", "asignatura_nombre": "Acompanamiento integral en el aula"},
            {"id_asignacion": "AS4", "display": "OVP | 10mo-A", "asignatura_nombre": "ORIENTACIÓN VOCACIONAL PROFESIONAL"},
            {"id_asignacion": "AS5", "display": "Comportamiento | 7mo-A", "asignatura_nombre": "  COMPORTAMIENTO  "},
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
            {"id_asignacion": "AS3", "display": "Acompañamiento | 8vo-A", "asignatura_nombre": "Acompañamiento integral en el aula"},
            {"id_asignacion": "AS4", "display": "OVP | 10mo-A", "asignatura_nombre": "Orientacion Vocacional y Profesional"},
            {"id_asignacion": "AS5", "display": "Comportamiento | 7mo-A", "asignatura_nombre": "Comportamiento"},
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
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, str | None]] = []
        self.orientation_calls: list[tuple[str, int]] = []

    def obtener_animacion_lectura_evaluacion(self, asignacion_id: str, trimestre_num: int, nivel: str | None = None) -> list[dict]:
        self.calls.append((asignacion_id, trimestre_num, nivel))
        return [
            {
                "estudiante_id": "E1",
                "estudiante": "Lopez Maria",
                "valor": 8.5,
                "cualitativo": "B+",
                "cualitativo_1": "B",
                "nivel": nivel or "elemental",
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

    def obtener_orientacion_vocacional_evaluacion(self, asignacion_id: str, trimestre_num: int) -> list[dict]:
        self.orientation_calls.append((asignacion_id, trimestre_num))
        return [
            {
                "estudiante_id": "E1",
                "estudiante": "Lopez Maria",
                "calificacion": "A+",
            }
        ]


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestReportsView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_view(self):
        from src.presentation.views.reports_view import ReportsView

        grade_service = _FakeGradeRegistrationService()
        view = ReportsView(
            _FakeAcademicSummaryService(),
            _FakeReportExportService(),
            _FakeClassroomAccompanimentService(),
            grade_service,
        )
        return view, grade_service

    def test_crear_vista_sin_error_y_botones_exportacion(self) -> None:
        view, _ = self._build_view()
        summary_view = view.findChild(type(view.layout().itemAt(0).widget()))
        self.assertIsNotNone(summary_view)
        self.assertIsNotNone(view.academic_summary_view.export_pdf_button)
        self.assertIsNotNone(view.academic_summary_view.export_excel_button)

    def test_manejar_escenario_sin_datos_sin_romper(self) -> None:
        view, _ = self._build_view()
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
        view, _ = self._build_view()
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

    def test_cambio_desde_acompanamiento_a_animacion_no_caer_en_resumen_cuantitativo(self) -> None:
        view, _ = self._build_view()
        summary_combo = view.academic_summary_view.assignment_combo

        idx_acomp = summary_combo.findData("AS3")
        self.assertGreaterEqual(idx_acomp, 0)
        summary_combo.setCurrentIndex(idx_acomp)
        self.assertEqual(view.stack.currentWidget(), view.accompaniment_report_view)

        idx_anim = summary_combo.findData("AS2")
        self.assertGreaterEqual(idx_anim, 0)
        summary_combo.setCurrentIndex(idx_anim)
        self.assertEqual(view.stack.currentWidget(), view.animation_report_view)

    def test_comportamiento_usa_reporte_especial_de_acompanamiento(self) -> None:
        view, _ = self._build_view()
        summary_combo = view.academic_summary_view.assignment_combo
        idx_behavior = summary_combo.findData("AS5")
        self.assertGreaterEqual(idx_behavior, 0)
        summary_combo.setCurrentIndex(idx_behavior)
        self.assertEqual(view.stack.currentWidget(), view.accompaniment_report_view)

    def test_animacion_conserva_trimestre_y_nivel_en_carga_automatica(self) -> None:
        view, grade_service = self._build_view()
        summary_combo = view.academic_summary_view.assignment_combo

        idx_anim = summary_combo.findData("AS2")
        self.assertGreaterEqual(idx_anim, 0)
        summary_combo.setCurrentIndex(idx_anim)
        self.assertEqual(view.stack.currentWidget(), view.animation_report_view)

        idx_trim_2 = view.animation_report_view.report_trimester_combo.findData(2)
        self.assertGreaterEqual(idx_trim_2, 0)
        view.animation_report_view.report_trimester_combo.setCurrentIndex(idx_trim_2)
        self.assertEqual(view.animation_report_view.report_trimester_combo.currentData(), 2)

        idx_media = view.animation_report_view.level_combo.findData("media")
        self.assertGreaterEqual(idx_media, 0)
        view.animation_report_view.level_combo.setCurrentIndex(idx_media)
        self.assertEqual(view.animation_report_view.level_combo.currentData(), "media")

        self.assertIn(("AS2", 2, "media"), grade_service.calls)
        self.assertIn("ANIMACIÓN A LA LECTURA - TRIMESTRE 2", view.animation_report_view._last_preview_html)

    def test_orientacion_detecta_materia_especial_y_no_usa_resumen_cuantitativo(self) -> None:
        view, grade_service = self._build_view()
        summary_combo = view.academic_summary_view.assignment_combo
        idx_ovp = summary_combo.findData("AS4")
        self.assertGreaterEqual(idx_ovp, 0)
        summary_combo.setCurrentIndex(idx_ovp)

        self.assertEqual(view.stack.currentWidget(), view.orientation_report_view)
        self.assertIn(("AS4", 1), grade_service.orientation_calls)
        html = view.orientation_report_view._last_preview_html
        self.assertIn("ORIENTACIÓN VOCACIONAL Y PROFESIONAL - TRIMESTRE 1", html)
        self.assertIn("Nómina de Estudiantes", html)
        self.assertNotIn("T1 Calificación", html)


if __name__ == "__main__":
    unittest.main()
