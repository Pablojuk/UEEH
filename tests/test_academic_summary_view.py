"""Pruebas mínimas de vista de resumen académico."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None


class _FakeAcademicSummaryService:
    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = rows or []

    def listar_contextos_disponibles(self) -> list[dict]:
        return [{"id_asignacion": "AS1", "display": "Contexto demo"}]

    def obtener_resumen_por_asignacion(self, asignacion_id: str) -> list[dict]:
        return list(self.rows)

    def obtener_reporte_anual(self, asignacion_id: str) -> list[dict]:
        return list(self.rows)

    def obtener_reporte_trimestral(self, asignacion_id: str, trimestre_num: int) -> list[dict]:
        return list(self.rows)

    def recalcular_resumenes(self, rows: list[dict]) -> list[dict]:
        return rows

    def guardar_supletorios(self, asignacion_id: str, rows: list[dict]) -> tuple[bool, str]:
        return True, f"Supletorios procesados: {len(rows)}"

    def listar_firmantes_disponibles(self) -> list[dict]:
        return [{"id_docente": "D1", "firma": "Econ. Pablo Juca"}]


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestAcademicSummaryView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_crear_vista_sin_error(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        view = AcademicSummaryView(_FakeAcademicSummaryService())
        self.assertIsNotNone(view.assignment_combo)
        self.assertIsNotNone(view.table)

    def test_cargar_tabla_vacia_sin_romper(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        view = AcademicSummaryView(_FakeAcademicSummaryService(rows=[]))
        view.load_summary()
        self.assertEqual(view.table.rowCount(), 0)
        self.assertEqual(view.table.horizontalHeaderItem(0).text(), "N°")
        self.assertEqual(view.table.horizontalHeaderItem(1).text(), "Nómina")

    def test_poblar_tabla_con_datos(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        view = AcademicSummaryView(
            _FakeAcademicSummaryService(
                rows=[
                    {
                        "estudiante_id": "E1",
                        "estudiante": "Lopez Maria",
                        "trimestre_1": 8,
                        "equivalencia_t1": "AA",
                        "trimestre_2": 7,
                        "equivalencia_t2": "AA",
                        "trimestre_3": 6,
                        "equivalencia_t3": "PA",
                        "promedio": 7,
                        "cualitativa_anual": "AA",
                        "promedio_final": 7,
                        "cualitativo": "B-",
                        "observacion": "APB",
                        "supletorio": None,
                        "nota_definitiva": 7,
                    }
                ]
            )
        )
        view.load_summary()
        self.assertEqual(view.table.rowCount(), 1)
        self.assertEqual(view.table.item(0, 0).text(), "")
        self.assertEqual(view.table.item(0, 1).text(), "Lopez Maria")


if __name__ == "__main__":
    unittest.main()
