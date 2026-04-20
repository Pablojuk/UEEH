"""Pruebas mínimas para vista de acompañamiento integral."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


class _FakeAccompanimentService:
    def listar_contextos_disponibles(self) -> list[dict]:
        return [{"id_asignacion": "AS1", "display": "Demo"}]

    def cargar_evaluacion(self, asignacion_id: str, trimestre_num: int) -> dict:
        return {
            "students": [{"student_id": "E1", "code": "001", "name": "López María"}],
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
        }

    def guardar_evaluacion(self, asignacion_id: str, trimestre_num: int, active_skills: list[str], responses: dict) -> tuple[bool, str]:
        return True, "ok"

    def calcular_resultado_estudiante(self, skill_values: dict[str, str], active_skills: list[str]) -> dict:
        return {
            "total_siempre": 1,
            "total_frecuentemente": 0,
            "total_ocasionalmente": 0,
            "total_nunca": 0,
            "valoracion_final": "",
        }


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestClassroomAccompanimentView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_crear_vista_y_cargar(self) -> None:
        from src.presentation.views.classroom_accompaniment_view import ClassroomAccompanimentView

        view = ClassroomAccompanimentView(_FakeAccompanimentService())
        view.load_rows()
        self.assertEqual(view.table.rowCount(), 1)
        self.assertGreaterEqual(view.table.columnCount(), 8)


if __name__ == "__main__":
    unittest.main()
