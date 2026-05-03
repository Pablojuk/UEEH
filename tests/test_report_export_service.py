"""Pruebas del servicio de exportación de reportes."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.application.services.academic_summary_service import AcademicSummaryService
from src.application.services.institution_service import InstitutionService
from src.application.services.report_export_service import ReportExportService
from src.infrastructure.persistence.db import initialize_database


class _FakePdfExporter:
    last_context: dict | None = None

    def exportar(self, output_path: str, report_title: str, context: dict, rows: list[dict]) -> str:
        _FakePdfExporter.last_context = context
        Path(output_path).write_text("pdf", encoding="utf-8")
        return output_path


class _FakeExcelExporter:
    def exportar(self, output_path: str, report_title: str, context: dict, rows: list[dict]) -> str:
        Path(output_path).write_text("xlsx", encoding="utf-8")
        return output_path


class _FailingExporter:
    def exportar(self, output_path: str, report_title: str, context: dict, rows: list[dict]) -> str:
        raise OSError("no writable")


class _FakeHtmlRenderer:
    def __init__(self) -> None:
        self.calls = 0

    def render(self, context: dict, rows: list[dict]) -> str:
        self.calls += 1
        return f"<html>{context.get('report_type')}:{len(rows)}</html>"


class TestReportExportService(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = initialize_database(":memory:")
        self.academic_summary_service = AcademicSummaryService(self.conn)
        self.institution_service = InstitutionService(self.conn)
        self._seed_data()

    def tearDown(self) -> None:
        self.conn.close()

    def _seed_data(self) -> None:
        with self.conn:
            self.conn.execute("INSERT INTO institucion (id_institucion, nombre, jornada) VALUES (?, ?, ?)", ("I1", "UEEH", "Matutina"))
            self.conn.execute(
                "INSERT INTO docentes (id_docente, nombres, apellidos, identificacion, activo) VALUES (?, ?, ?, ?, ?)",
                ("D1", "Ana", "Perez", "123", 1),
            )
            self.conn.execute("INSERT INTO asignaturas (id_asignatura, nombre, codigo) VALUES (?, ?, ?)", ("A1", "Mat", "MAT"))
            self.conn.execute("INSERT INTO cursos (id_curso, nombre, nivel) VALUES (?, ?, ?)", ("C1", "3ro de EGB-A", "Basica"))
            self.conn.execute("INSERT INTO paralelos (id_paralelo, nombre) VALUES (?, ?)", ("P1", "A"))
            self.conn.execute(
                "INSERT INTO periodos_lectivos (id_periodo, anio_inicio, anio_fin, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?, ?)",
                ("2025-2026", 2025, 2026, None, None),
            )
            self.conn.execute(
                "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres, identificacion) VALUES (?, ?, ?, ?, ?)",
                ("E1", "EST-1", "Lopez", "Maria", "999"),
            )
            self.conn.execute(
                "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id, numero_lista) VALUES (?, ?, ?, ?, ?, ?)",
                ("M1", "E1", "C1", "P1", "2025-2026", 1),
            )
            self.conn.execute(
                "INSERT INTO asignaciones_docente (id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) VALUES (?, ?, ?, ?, ?, ?)",
                ("AS1", "D1", "A1", "C1", "P1", "2025-2026"),
            )
            self.conn.execute(
                """
                INSERT INTO grade_records (
                    id_registro, estudiante_id, asignacion_id, trimestre_num,
                    actividad_1, mejora_1, actividad_2, mejora_2, actividad_3, mejora_3,
                    proyecto, evaluacion, refuerzo, mejora_sumativa,
                    promedio_formativo, promedio_sumativo, nota_trimestral
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("G1", "E1", "AS1", 1, 8, None, 8, None, 8, None, 8, 8, 8, None, 8, 8, 8),
            )

    def test_exportar_resumen_valido_pdf(self) -> None:
        service = ReportExportService(
            connection=self.conn,
            academic_summary_service=self.academic_summary_service,
            institution_service=self.institution_service,
            pdf_exporter=_FakePdfExporter(),
            excel_exporter=_FakeExcelExporter(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp) / "reporte.pdf")
            ok, message = service.exportar_resumen_pdf("AS1", output)
            self.assertTrue(ok)
            self.assertIn("Archivo generado", message)
            self.assertTrue(Path(output).exists())

    def test_exportar_resumen_valido_excel(self) -> None:
        service = ReportExportService(
            connection=self.conn,
            academic_summary_service=self.academic_summary_service,
            institution_service=self.institution_service,
            pdf_exporter=_FakePdfExporter(),
            excel_exporter=_FakeExcelExporter(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp) / "reporte.xlsx")
            ok, message = service.exportar_resumen_excel("AS1", output)
            self.assertTrue(ok)
            self.assertIn("Archivo generado", message)
            self.assertTrue(Path(output).exists())

    def test_rechazar_exportacion_sin_datos(self) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM grade_records")
        service = ReportExportService(
            connection=self.conn,
            academic_summary_service=self.academic_summary_service,
            institution_service=self.institution_service,
            pdf_exporter=_FakePdfExporter(),
            excel_exporter=_FakeExcelExporter(),
        )
        ok, message = service.exportar_resumen_pdf("AS1", "out.pdf")
        self.assertFalse(ok)
        self.assertIn("No hay datos", message)

    def test_manejar_error_de_escritura(self) -> None:
        service = ReportExportService(
            connection=self.conn,
            academic_summary_service=self.academic_summary_service,
            institution_service=self.institution_service,
            pdf_exporter=_FailingExporter(),
            excel_exporter=_FakeExcelExporter(),
        )
        ok, message = service.exportar_resumen_pdf("AS1", "/root/no_access/reporte.pdf")
        self.assertFalse(ok)
        self.assertIn("Error al exportar", message)

    def test_exporta_firmantes_en_contexto(self) -> None:
        service = ReportExportService(
            connection=self.conn,
            academic_summary_service=self.academic_summary_service,
            institution_service=self.institution_service,
            pdf_exporter=_FakePdfExporter(),
            excel_exporter=_FakeExcelExporter(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp) / "firmas.pdf")
            ok, _ = service.exportar_resumen_pdf(
                "AS1",
                output,
                firmantes={"docente": "Econ. Pablo Juca", "rector": "Msc. Ana Perez"},
            )
            self.assertTrue(ok)
            context = _FakePdfExporter.last_context or {}
            self.assertIn("firmantes", context)
            self.assertEqual(context["firmantes"].get("docente"), "Econ. Pablo Juca")

    def test_generar_resumen_html_reutiliza_renderer(self) -> None:
        fake_renderer = _FakeHtmlRenderer()
        service = ReportExportService(
            connection=self.conn,
            academic_summary_service=self.academic_summary_service,
            institution_service=self.institution_service,
            pdf_exporter=_FakePdfExporter(),
            excel_exporter=_FakeExcelExporter(),
            html_renderer=fake_renderer,
        )
        html = service.generar_resumen_html("AS1", report_type="anual")
        self.assertIn("anual", html)
        self.assertEqual(fake_renderer.calls, 1)

    def test_corrige_subtitulo_con_santa_isabel(self) -> None:
        cleaned = ReportExportService._sanitize_institucion({"ciudad": "Santa Isabale", "parroquia": "Cañaribamba"})
        self.assertEqual(cleaned["ciudad"], "Santa Isabel")

    def test_detecta_simplificado_en_curso_con_paralelo(self) -> None:
        service = ReportExportService(
            connection=self.conn,
            academic_summary_service=self.academic_summary_service,
            institution_service=self.institution_service,
        )
        context, _ = service._prepare_report_context("AS1", "anual", None, None)
        self.assertTrue(context["is_simplified_anual"])



if __name__ == "__main__":
    unittest.main()
