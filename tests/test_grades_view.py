"""Pruebas mínimas de vista de notas."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


class _FakeGradeRegistrationService:
    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = rows or []

    def listar_contextos_disponibles(self) -> list[dict]:
        return [{"id_asignacion": "AS1", "display": "Contexto demo"}]

    def cargar_registro(self, asignacion_id: str, trimestre_num: int) -> list[dict]:
        return list(self.rows)

    def obtener_numero_actividades(self, asignacion_id: str, trimestre_num: int) -> int:
        return 3

    def configurar_numero_actividades(self, asignacion_id: str, trimestre_num: int, numero: int) -> tuple[bool, str]:
        return True, "ok"

    def recalcular_fila(self, fila: dict) -> dict:
        salida = dict(fila)
        salida.setdefault("promedio_formativo", 0.0)
        salida.setdefault("promedio_sumativo", 0.0)
        salida.setdefault("nota_trimestral", 0.0)
        return salida

    def guardar_registros(self, asignacion_id: str, trimestre_num: int, filas: list[dict]) -> tuple[bool, str]:
        return True, f"Registros guardados: {len(filas)}"


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestGradesView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_crear_vista_sin_error(self) -> None:
        from src.presentation.views.grades_view import GradesView

        view = GradesView(_FakeGradeRegistrationService())
        self.assertIsNotNone(view.assignment_combo)
        self.assertIsNotNone(view.trimester_combo)
        self.assertIsNotNone(view.table)

    def test_cargar_tabla_vacia_sin_romper(self) -> None:
        from src.presentation.views.grades_view import GradesView

        view = GradesView(_FakeGradeRegistrationService(rows=[]))
        view.load_rows()
        self.assertEqual(view.table.rowCount(), 0)

    def test_poblar_tabla_con_estudiantes(self) -> None:
        from src.presentation.views.grades_view import GradesView

        view = GradesView(
            _FakeGradeRegistrationService(
                rows=[
                    {
                        "estudiante_id": "E1",
                        "estudiante": "Lopez Maria",
                        "actividad_1": 8,
                        "mejora_1": None,
                        "actividad_2": 9,
                        "mejora_2": None,
                        "actividad_3": 10,
                        "mejora_3": None,
                        "proyecto": 8,
                        "evaluacion": 9,
                        "refuerzo": 7,
                        "mejora_sumativa": None,
                        "promedio_formativo": 9,
                        "promedio_sumativo": 8,
                        "nota_trimestral": 8.7,
                    }
                ]
            )
        )
        view.load_rows()
        self.assertEqual(view.table.rowCount(), 1)
        self.assertEqual(view.table.item(0, 0).text(), "Lopez Maria")

    def test_formato_encabezado_largo_en_dos_lineas(self) -> None:
        from src.presentation.views.grades_view import GradesView

        self.assertEqual(
            GradesView._format_header_label("Promedio Evaluación Sumativa 30%"),
            "Promedio Evaluación\nSumativa 30%",
        )
        self.assertEqual(GradesView._format_header_label("Actividad 1"), "Actividad 1")

    def test_copy_paste_en_tabla(self) -> None:
        from src.presentation.views.grades_view import GradesView

        view = GradesView(
            _FakeGradeRegistrationService(
                rows=[
                    {"estudiante_id": "E1", "estudiante": "Lopez Maria", "actividad_1": 8},
                    {"estudiante_id": "E2", "estudiante": "Perez Juan", "actividad_1": 7},
                ]
            )
        )
        view.load_rows()
        view.table.setCurrentCell(0, 1)
        view.table.selectRow(0)
        view._copy_selected_cells()
        copied = QApplication.clipboard().text()
        self.assertTrue("Lopez Maria" in copied)

        QApplication.clipboard().setText("9\t10")
        view.table.setCurrentCell(0, 1)
        view._paste_from_clipboard()
        self.assertEqual(view.table.item(0, 1).text(), "9")


if __name__ == "__main__":
    unittest.main()
