"""Pruebas mínimas para vista de acompañamiento integral."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


class _FakeAccompanimentService:
    def __init__(self, students: list[dict] | None = None) -> None:
        self.load_calls = 0
        self.students = students or [{"student_id": "E1", "code": "001", "name": "López María"}]

    def listar_contextos_disponibles(self) -> list[dict]:
        return [{"id_asignacion": "AS1", "display": "Demo"}]

    def cargar_evaluacion(self, asignacion_id: str, trimestre_num: int) -> dict:
        self.load_calls += 1
        return {
            "students": list(self.students),
            "skill_categories": [
                {
                    "category": "HABILIDADES COGNITIVAS",
                    "skills": [
                        {"key": "autoconocimiento", "label": "Autoconocimiento", "visible": True},
                        {"key": "pensamiento_critico", "label": "Pensamiento crítico", "visible": False},
                    ],
                }
            ],
            "active_skills": ["autoconocimiento"],
            "responses": {"E1": {"autoconocimiento": "Siempre"}},
            "results": {},
            "validation_message": "",
        }

    def guardar_evaluacion(self, asignacion_id: str, trimestre_num: int, active_skills: list[str], responses: dict) -> tuple[bool, str]:
        return True, "ok"

    def calcular_resultado_estudiante(
        self,
        skill_values: dict[str, str],
        active_skills: list[str],
        variant: str = "accompaniment",
    ) -> dict:
        return {
            "total_siempre": 1,
            "total_frecuentemente": 0,
            "total_ocasionalmente": 0,
            "total_nunca": 0,
            "puntaje_total_ponderado": 4,
            "valoracion_final": "",
            "validation_message": "",
        }

    def listar_firmantes_disponibles(self) -> list[str]:
        return ["Prof. Demo", "Rector Demo"]


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestClassroomAccompanimentView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()

    def test_crear_vista_y_cargar(self) -> None:
        from src.presentation.views.classroom_accompaniment_view import ClassroomAccompanimentView

        view = ClassroomAccompanimentView(_FakeAccompanimentService())
        view.load_rows()
        self.assertEqual(view.table.rowCount(), 1)
        self.assertGreaterEqual(view.table.columnCount(), 8)

    def test_cambio_trimestre_carga_automaticamente(self) -> None:
        from src.presentation.views.classroom_accompaniment_view import ClassroomAccompanimentView

        service = _FakeAccompanimentService()
        view = ClassroomAccompanimentView(service)
        before = service.load_calls
        view.trimester_combo.setCurrentIndex(1)
        self.assertGreater(service.load_calls, before)

    def test_tabla_y_reporte_conservan_orden_alfabetico_del_servicio(self) -> None:
        from src.presentation.views.classroom_accompaniment_view import ClassroomAccompanimentView

        service = _FakeAccompanimentService(
            students=[
                {"student_id": "E3", "code": "EST-3", "name": "alvarez Beatriz"},
                {"student_id": "E2", "code": "EST-2", "name": "Álvarez Luis"},
                {"student_id": "E1", "code": "EST-1", "name": "Zambrano Ana"},
            ]
        )
        view = ClassroomAccompanimentView(service)
        view.load_rows()

        self.assertEqual(
            [view.table.item(row, 1).text() for row in range(view.table.rowCount())],
            ["alvarez Beatriz", "Álvarez Luis", "Zambrano Ana"],
        )
        preview_rows = view._construir_estudiantes_trimestrales(
            [
                {"nombre": "alvarez Beatriz", "valoracion_final": ""},
                {"nombre": "Álvarez Luis", "valoracion_final": ""},
                {"nombre": "Zambrano Ana", "valoracion_final": ""},
            ]
        )
        self.assertEqual(
            [row["nombre"] for row in preview_rows],
            ["alvarez Beatriz", "Álvarez Luis", "Zambrano Ana"],
        )

    def test_configurar_habilidades_muestra_dialogo_con_cursor_normal(self) -> None:
        from PySide6.QtWidgets import QDialog

        from src.presentation.views.classroom_accompaniment_view import (
            ClassroomAccompanimentView,
            SkillConfigDialog,
        )

        for variant in ("accompaniment", "behavior"):
            with self.subTest(variant=variant):
                view = ClassroomAccompanimentView(_FakeAccompanimentService())
                view.set_evaluation_variant(variant)

                def dialog_exec(_dialog) -> int:
                    self.assertIsNone(QApplication.overrideCursor())
                    return QDialog.Rejected

                with patch.object(SkillConfigDialog, "exec", autospec=True, side_effect=dialog_exec):
                    view.open_skill_config()
                self.assertIsNone(QApplication.overrideCursor())
                self.assertTrue(view.configure_skills_button.isEnabled())

    def test_excepcion_al_cargar_configuracion_restaura_cursor_y_boton(self) -> None:
        from src.presentation.views.classroom_accompaniment_view import ClassroomAccompanimentView

        class FailingService(_FakeAccompanimentService):
            def cargar_evaluacion(self, asignacion_id: str, trimestre_num: int) -> dict:
                raise RuntimeError("fallo sintético de carga")

        view = ClassroomAccompanimentView(FailingService())
        original_text = view.configure_skills_button.text()
        with self.assertRaisesRegex(RuntimeError, "fallo sintético"):
            view.open_skill_config()
        self.assertIsNone(QApplication.overrideCursor())
        self.assertTrue(view.configure_skills_button.isEnabled())
        self.assertEqual(view.configure_skills_button.text(), original_text)

    def test_busy_button_preserva_un_override_externo_anidado(self) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QPushButton

        from src.presentation.widgets.busy_state import busy_button

        button = QPushButton("Acción")
        QApplication.setOverrideCursor(Qt.CrossCursor)
        try:
            with busy_button(button, "Procesando..."):
                self.assertEqual(QApplication.overrideCursor().shape(), Qt.WaitCursor)
            self.assertEqual(QApplication.overrideCursor().shape(), Qt.CrossCursor)
        finally:
            QApplication.restoreOverrideCursor()
        self.assertIsNone(QApplication.overrideCursor())


if __name__ == "__main__":
    unittest.main()
