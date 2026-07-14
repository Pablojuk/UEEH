"""Pruebas mínimas de vista de notas."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFontMetrics
    from PySide6.QtWidgets import QApplication, QHeaderView
except ImportError:  # pragma: no cover
    QApplication = None


class _FakeGradeRegistrationService:
    def __init__(self, rows: list[dict] | None = None, contexts: list[dict] | None = None) -> None:
        self.rows = rows or []
        self.contexts = contexts or [{"id_asignacion": "AS1", "display": "Contexto demo"}]
        self.activity_config = {"numero_actividades": 3, "metadata": [{"nombre": "Actividad Diagnóstica"}]}

    def listar_contextos_disponibles(self) -> list[dict]:
        return list(self.contexts)

    def cargar_registro(self, asignacion_id: str, trimestre_num: int) -> list[dict]:
        return list(self.rows)

    def obtener_numero_actividades(self, asignacion_id: str, trimestre_num: int) -> int:
        return 3

    def obtener_configuracion_actividades(self, asignacion_id: str, trimestre_num: int) -> dict:
        return dict(self.activity_config)

    def guardar_configuracion_actividades(self, asignacion_id: str, trimestre_num: int, metadata: list[dict]) -> tuple[bool, str]:
        self.activity_config["metadata"] = list(metadata)
        return True, "ok"

    def configurar_numero_actividades(self, asignacion_id: str, trimestre_num: int, numero: int) -> tuple[bool, str]:
        return True, "ok"

    def recalcular_fila(self, fila: dict, numero_actividades: int = 3, usar_logica_basica: bool = False) -> dict:
        salida = dict(fila)
        try:
            salida["nota_trimestral"] = float(salida.get("actividad_1")) if salida.get("actividad_1") not in (None, "") else 0.0
        except Exception:
            salida["nota_trimestral"] = 0.0
        salida.setdefault("promedio_formativo", 0.0)
        salida.setdefault("promedio_sumativo", 0.0)
        salida.setdefault("cualitativo_adicional", "AA")
        return salida

    def guardar_registros(self, asignacion_id: str, trimestre_num: int, filas: list[dict]) -> tuple[bool, str]:
        return True, f"Registros guardados: {len(filas)}"

    def validar_curso_orientacion_vocacional(self, asignacion_id: str) -> tuple[bool, str | None, str]:
        return True, "8", "8vo de EGB"

    def obtener_orientacion_vocacional_evaluacion(self, asignacion_id: str, trimestre_num: int) -> list[dict]:
        return []

    def guardar_orientacion_vocacional_evaluacion(self, payload: dict) -> tuple[bool, str]:
        return True, "ok"

    def usar_logica_cuantitativa_basica(self, asignacion_id: str) -> bool:
        return str(asignacion_id).startswith("AS-EGB")


class _FakeClassroomAccompanimentService:
    def __init__(self, contexts: list[dict] | None = None) -> None:
        self.contexts = contexts or [{"id_asignacion": "AS-COMP", "display": "Comportamiento demo"}]
        self.loaded_assignment_ids: list[str] = []

    def listar_contextos_disponibles(self) -> list[dict]:
        return list(self.contexts)

    def cargar_evaluacion(self, asignacion_id: str, trimestre_num: int) -> dict:
        self.loaded_assignment_ids.append(asignacion_id)
        return {"students": [], "skill_categories": [], "active_skills": [], "responses": {}, "results": {}}

    def guardar_evaluacion(self, asignacion_id: str, trimestre_num: int, active_skills: list[str], responses: dict) -> tuple[bool, str]:
        return True, "ok"

    def calcular_resultado_estudiante(self, skill_values: dict[str, str], active_skills: list[str]) -> dict:
        return {}

    def listar_firmantes_disponibles(self) -> list[str]:
        return []

    def obtener_contexto(self, asignacion_id: str) -> dict:
        return {}

    def obtener_datos_institucion(self) -> dict:
        return {}


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
        self.assertIsNotNone(view.activities_meta_card)

    def test_cargar_tabla_vacia_sin_romper(self) -> None:
        from src.presentation.views.grades_view import GradesView

        view = GradesView(_FakeGradeRegistrationService(rows=[]))
        view.load_rows()
        self.assertEqual(view.table.rowCount(), 1)

    def test_fila_superior_para_nombre_actividad(self) -> None:
        from src.presentation.views.grades_view import GradesView

        view = GradesView(_FakeGradeRegistrationService(rows=[]))
        view.load_rows()
        self.assertIn("Actividad", view.table.item(0, 1).text())

    def test_metodo_compatibilidad_save_activity_metadata_existe(self) -> None:
        from src.presentation.views.grades_view import GradesView

        view = GradesView(_FakeGradeRegistrationService(rows=[]))
        view.load_rows()
        view._save_activity_metadata()

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
        headers = [view.table.horizontalHeaderItem(i).text() for i in range(view.table.columnCount())]
        self.assertIn("Equivalencia", headers)

    def test_formato_encabezado_largo_en_dos_o_tres_lineas(self) -> None:
        from src.presentation.views.grades_view import GradesView

        self.assertEqual(
            GradesView._format_header_label("Promedio Evaluación Sumativa 30%"),
            "Promedio Evaluación\nSumativa 30%",
        )
        self.assertEqual(
            GradesView._format_header_label("Promedio con Mejora Evaluación Sumativa"),
            "Promedio con\nMejora Evaluación\nSumativa",
        )
        self.assertEqual(
            GradesView._format_header_label("Proyecto Interdisciplinar"),
            "Proyecto\nInterdisciplinar",
        )
        self.assertEqual(GradesView._format_header_label("Actividad 1"), "Actividad 1")

    def test_dimensiona_encabezados_para_todos_los_niveles_y_cantidades_de_actividades(self) -> None:
        from src.presentation.views.grades_view import GradesView

        for egb_basic_mode in (False, True):
            for activity_count in (3, 5, 8):
                with self.subTest(egb_basic_mode=egb_basic_mode, activity_count=activity_count):
                    view = GradesView(_FakeGradeRegistrationService(rows=[]))
                    view._egb_basic_mode = egb_basic_mode
                    view._numero_actividades = activity_count
                    view._setup_columns()
                    view._apply_column_resize_policy()

                    header = view.table.horizontalHeader()
                    metrics = QFontMetrics(header.font())
                    maximum_line_count = 1
                    for column, (_, full_title) in enumerate(view._table_columns):
                        item = view.table.horizontalHeaderItem(column)
                        lines = item.text().splitlines()
                        maximum_line_count = max(maximum_line_count, len(lines))
                        expected_minimum = max(metrics.horizontalAdvance(line) for line in lines) + 24
                        self.assertGreaterEqual(view.table.columnWidth(column), expected_minimum)
                        self.assertEqual(item.toolTip(), full_title)
                        self.assertLessEqual(len(lines), 3)

                    expected_height = metrics.height() + (maximum_line_count - 1) * metrics.lineSpacing() + 12
                    self.assertEqual(header.height(), expected_height)
                    self.assertEqual(header.sectionResizeMode(0), QHeaderView.Interactive)
                    self.assertNotEqual(view.table.horizontalScrollBarPolicy(), Qt.ScrollBarAlwaysOff)

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

    def test_paste_normaliza_coma_decimal(self) -> None:
        from src.presentation.views.grades_view import GradesView

        view = GradesView(_FakeGradeRegistrationService(rows=[{"estudiante_id": "E1", "estudiante": "Lopez Maria", "actividad_1": 8}]))
        view.load_rows()
        view.table.setCurrentCell(0, 1)
        QApplication.clipboard().setText("8,75")
        view._paste_from_clipboard()
        self.assertEqual(view.table.item(0, 1).text(), "8.75")

    def test_refresh_data_conserva_asignacion_seleccionada(self) -> None:
        from src.presentation.views.grades_view import GradesView

        service = _FakeGradeRegistrationService(
            contexts=[
                {"id_asignacion": "AS1", "display": "Contexto demo 1"},
                {"id_asignacion": "AS2", "display": "Contexto demo 2"},
            ]
        )
        view = GradesView(service)
        idx = view.assignment_combo.findData("AS2")
        view.assignment_combo.setCurrentIndex(idx)

        view.refresh_data()
        self.assertEqual(view.assignment_combo.currentData(), "AS2")

    def test_detecta_orientacion_como_materia_especial(self) -> None:
        from src.presentation.views.grades_view import GradesView

        service = _FakeGradeRegistrationService(
            rows=[{"estudiante_id": "E1", "estudiante": "Lopez Maria"}],
            contexts=[
                {
                    "id_asignacion": "AS-OVP",
                    "display": "Orientación Vocacional | 8vo-A",
                    "asignatura_nombre": "Orientación Vocacional y Profesional",
                    "curso_nombre": "8vo de EGB",
                }
            ],
        )
        view = GradesView(service, classroom_accompaniment_service=_FakeClassroomAccompanimentService())
        view.assignment_combo.setCurrentIndex(0)
        self.assertTrue(view._vocational_orientation_mode)
        self.assertFalse(view.table.isVisible())

    def test_detecta_comportamiento_como_materia_especial_de_acompanamiento(self) -> None:
        from src.presentation.views.grades_view import GradesView

        service = _FakeGradeRegistrationService(
            rows=[{"estudiante_id": "E1", "estudiante": "Lopez Maria"}],
            contexts=[
                {
                    "id_asignacion": "AS-COMP",
                    "display": "Comportamiento | 7mo-A",
                    "asignatura_nombre": "  COMPORTAMIENTO ",
                }
            ],
        )
        view = GradesView(service, classroom_accompaniment_service=_FakeClassroomAccompanimentService())
        view.assignment_combo.setCurrentIndex(0)
        self.assertTrue(view._accompaniment_mode)
        self.assertFalse(view.table.isVisible())

    def test_recarga_contextos_integrados_y_selecciona_el_id_exacto(self) -> None:
        from src.presentation.views.grades_view import GradesView

        grade_service = _FakeGradeRegistrationService(
            contexts=[{"id_asignacion": "AS1", "display": "Matemática", "asignatura_nombre": "Matemática"}]
        )
        accompaniment_service = _FakeClassroomAccompanimentService(
            contexts=[{"id_asignacion": "AS-ANTERIOR", "display": "Anterior"}]
        )
        view = GradesView(grade_service, classroom_accompaniment_service=accompaniment_service)

        grade_service.contexts = [
            {
                "id_asignacion": "AS-COMP-2",
                "display": "Comportamiento | 2do EGB-A",
                "asignatura_nombre": "Comportamiento",
            }
        ]
        accompaniment_service.contexts = [
            {"id_asignacion": "AS-COMP-2", "display": "Comportamiento | 2do EGB-A"}
        ]
        view.load_contexts(selected_assignment_id="AS-COMP-2")

        assert view.accompaniment_view is not None
        self.assertEqual(view.accompaniment_view.assignment_combo.currentData(), "AS-COMP-2")
        self.assertEqual(accompaniment_service.loaded_assignment_ids[-1], "AS-COMP-2")

    def test_asignacion_integrada_inexistente_limpia_y_no_reutiliza_anterior(self) -> None:
        from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

        from src.presentation.views.grades_view import GradesView

        grade_service = _FakeGradeRegistrationService(
            contexts=[{"id_asignacion": "AS1", "display": "Matemática", "asignatura_nombre": "Matemática"}]
        )
        accompaniment_service = _FakeClassroomAccompanimentService(
            contexts=[{"id_asignacion": "AS-ANTERIOR", "display": "Anterior"}]
        )
        view = GradesView(grade_service, classroom_accompaniment_service=accompaniment_service)
        assert view.accompaniment_view is not None
        view.accompaniment_view.table.setColumnCount(1)
        view.accompaniment_view.table.setRowCount(1)
        view.accompaniment_view.table.setItem(0, 0, QTableWidgetItem("No reutilizar"))

        grade_service.contexts = [
            {
                "id_asignacion": "AS-INEXISTENTE",
                "display": "Comportamiento inexistente",
                "asignatura_nombre": "Comportamiento",
            }
        ]
        with patch.object(QMessageBox, "warning") as warning:
            view.load_contexts(selected_assignment_id="AS-INEXISTENTE")

        self.assertIsNone(view.accompaniment_view.assignment_combo.currentData())
        self.assertEqual(view.accompaniment_view.table.rowCount(), 0)
        self.assertNotIn("AS-ANTERIOR", accompaniment_service.loaded_assignment_ids)
        warning.assert_called_once()
        self.assertIn("evitar cargar otra asignación", warning.call_args.args[2])

    def test_carga_automatica_en_materia_cuantitativa(self) -> None:
        from src.presentation.views.grades_view import GradesView
        service = _FakeGradeRegistrationService(
            rows=[{"estudiante_id": "E1", "estudiante": "Lopez Maria"}],
            contexts=[{"id_asignacion": "AS1", "display": "Matemática | 7mo-A", "asignatura_nombre": "Matemática"}],
        )
        view = GradesView(service)
        view.assignment_combo.setCurrentIndex(0)
        self.assertGreaterEqual(view.table.rowCount(), 1)
        self.assertFalse(view.load_button.isVisible())
        self.assertFalse(view.recalc_button.isVisible())


if __name__ == "__main__":
    unittest.main()
