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
        self.signers = [{"id_docente": "D1", "firma": "Econ. Pablo Juca"}]
        self.trimestral_calls = 0
        self.anual_calls = 0

    def listar_contextos_disponibles(self) -> list[dict]:
        return [
            {
                "id_asignacion": "AS1",
                "display": "Contexto demo",
                "curso_nombre": "2do de EGB",
                "asignatura_nombre": "Matemática",
            },
            {
                "id_asignacion": "AS2",
                "display": "Contexto especial",
                "curso_nombre": "2do de EGB",
                "asignatura_nombre": "Comportamiento",
            },
            {
                "id_asignacion": "AS3",
                "display": "Contexto general",
                "curso_nombre": "8vo de EGB",
                "asignatura_nombre": "Matemática",
            },
        ]

    def obtener_resumen_por_asignacion(self, asignacion_id: str) -> list[dict]:
        return list(self.rows)

    def obtener_reporte_anual(self, asignacion_id: str) -> list[dict]:
        self.anual_calls += 1
        return list(self.rows)

    def obtener_reporte_trimestral(self, asignacion_id: str, trimestre_num: int) -> list[dict]:
        self.trimestral_calls += 1
        return list(self.rows)

    def recalcular_resumenes(self, rows: list[dict]) -> list[dict]:
        return rows

    def guardar_supletorios(self, asignacion_id: str, rows: list[dict]) -> tuple[bool, str]:
        return True, f"Supletorios procesados: {len(rows)}"

    def listar_firmantes_disponibles(self) -> list[dict]:
        return list(self.signers)


class _FakeReportExportService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generar_resumen_html(self, asignacion_id: str, report_type: str = "anual", trimestre_num=None, firmantes=None) -> str:
        self.calls.append(
            {
                "asignacion_id": asignacion_id,
                "report_type": report_type,
                "trimestre_num": trimestre_num,
                "firmantes": firmantes or {},
            }
        )
        return "<html><body><h1>Vista previa institucional</h1></body></html>"


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

    def test_boton_vista_previa_existe(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        view = AcademicSummaryView(_FakeAcademicSummaryService())
        self.assertEqual(view.preview_button.text(), "Vista previa")
        self.assertEqual(view.btn_toggle_filas.text(), "🙈 Ocultar Filas Vacías")

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

    def test_tabla_conserva_orden_alfabetico_entregado_por_servicio(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        rows = [
            {"estudiante_id": "E3", "estudiante": "alvarez Beatriz", "numero_lista": 3},
            {"estudiante_id": "E2", "estudiante": "Álvarez Luis", "numero_lista": 2},
            {"estudiante_id": "E1", "estudiante": "Zambrano Ana", "numero_lista": 1},
        ]
        view = AcademicSummaryView(_FakeAcademicSummaryService(rows=rows))

        view.load_summary()

        self.assertEqual(
            [view.table.item(row, 1).text() for row in range(view.table.rowCount())],
            ["alvarez Beatriz", "Álvarez Luis", "Zambrano Ana"],
        )

    def test_vista_previa_usa_servicio_generar_html(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        fake_report_service = _FakeReportExportService()
        view = AcademicSummaryView(
            _FakeAcademicSummaryService(rows=[]),
            report_export_service=fake_report_service,
        )
        initial_calls = len(fake_report_service.calls)
        view.show_preview()
        self.assertEqual(len(fake_report_service.calls), initial_calls + 1)
        self.assertEqual(fake_report_service.calls[-1]["asignacion_id"], "AS1")
        self.assertEqual(view.tabs.currentIndex(), 1)

    def test_cambio_tipo_informe_dispara_carga_automatica(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        service = _FakeAcademicSummaryService(rows=[])
        view = AcademicSummaryView(service, report_export_service=_FakeReportExportService())
        before = service.trimestral_calls
        view.report_type_combo.setCurrentIndex(1)
        self.assertGreater(service.trimestral_calls, before)

    def test_cambio_firmantes_refresca_vista_previa_en_tiempo_real(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        report_service = _FakeReportExportService()
        view = AcademicSummaryView(_FakeAcademicSummaryService(rows=[]), report_export_service=report_service)
        before = len(report_service.calls)
        view.signer_docente_combo.setCurrentIndex(1)
        self.assertGreater(len(report_service.calls), before)

    def test_sanitiza_nombre_de_archivo_desde_asignacion(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        value = AcademicSummaryView._sanitize_filename("MATEMATICAS | SEGUNDO-A | Juca Farfan Pablo Hernan | PER-26-27")
        self.assertEqual(value, "MATEMATICAS_SEGUNDO-A_Juca_Farfan_Pablo_Hernan_PER-26-27")

    def test_refresh_data_actualiza_lista_firmantes(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        service = _FakeAcademicSummaryService(rows=[])
        view = AcademicSummaryView(service)
        initial_count = view.signer_docente_combo.count()
        service.signers.append({"id_docente": "D2", "firma": "Msc. Ana Perez"})
        view.refresh_data()
        self.assertGreater(view.signer_docente_combo.count(), initial_count)

    def test_modo_simplificado_oculta_controles_supletorio_en_2do_egb(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        view = AcademicSummaryView(_FakeAcademicSummaryService(rows=[]), report_export_service=_FakeReportExportService())
        idx = view.assignment_combo.findData("AS1")
        self.assertGreaterEqual(idx, 0)
        view.assignment_combo.setCurrentIndex(idx)

        self.assertFalse(view.load_button.isVisible())
        self.assertFalse(view.recalc_button.isVisible())
        self.assertFalse(view.save_button.isVisible())
        self.assertFalse(view.tabs.isTabVisible(0))
        self.assertTrue(view.preview_button.isVisible())
        self.assertTrue(view.export_pdf_button.isVisible())
        self.assertTrue(view.export_excel_button.isVisible())

    def test_materia_especial_no_aplica_modo_simplificado(self) -> None:
        from src.presentation.views.academic_summary_view import AcademicSummaryView

        view = AcademicSummaryView(_FakeAcademicSummaryService(rows=[]), report_export_service=_FakeReportExportService())
        idx = view.assignment_combo.findData("AS2")
        self.assertGreaterEqual(idx, 0)
        view.assignment_combo.setCurrentIndex(idx)

        self.assertTrue(view.load_button.isVisible())
        self.assertTrue(view.recalc_button.isVisible())
        self.assertTrue(view.save_button.isVisible())
        self.assertTrue(view.tabs.isTabVisible(0))


if __name__ == "__main__":
    unittest.main()
