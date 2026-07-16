"""Pruebas del exportador PDF."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.infrastructure.exporters.pdf_report_exporter import PdfReportExporter


class TestPdfReportExporter(unittest.TestCase):
    def test_reporte_trimestral_normal_exporta_en_horizontal(self) -> None:
        exporter = PdfReportExporter()
        context = {"report_type": "trimestral", "is_simplified_trimestral": False}
        rows = [{"estudiante": "Estudiante Sintético", "promedio_final": 8}]
        with patch.object(exporter, "_render_report_html", return_value="<html></html>"), patch.object(
            exporter, "export_to_pdf", return_value=True
        ) as export_to_pdf:
            exporter.exportar("reporte.pdf", "Reporte", context, rows)

        self.assertEqual(export_to_pdf.call_args.kwargs["orientation"], "landscape")

    def test_reporte_trimestral_simplificado_conserva_orientacion_vertical(self) -> None:
        exporter = PdfReportExporter()
        context = {"report_type": "trimestral", "is_simplified_trimestral": True}
        rows = [{"estudiante": "Estudiante Sintético", "promedio_final": 8}]
        with patch.object(exporter, "_render_report_html", return_value="<html></html>"), patch.object(
            exporter, "export_to_pdf", return_value=True
        ) as export_to_pdf:
            exporter.exportar("reporte.pdf", "Reporte", context, rows)

        self.assertEqual(export_to_pdf.call_args.kwargs["orientation"], "portrait")

    def test_reporte_anual_normal_exporta_en_horizontal(self) -> None:
        exporter = PdfReportExporter()
        context = {"report_type": "anual", "is_simplified_anual": False}
        rows = [{"estudiante": "Estudiante Sintético", "promedio_final": 8}]
        with patch.object(exporter, "_render_report_html", return_value="<html></html>"), patch.object(
            exporter, "export_to_pdf", return_value=True
        ) as export_to_pdf:
            exporter.exportar("reporte.pdf", "Reporte", context, rows)

        self.assertEqual(export_to_pdf.call_args.kwargs["orientation"], "landscape")

    def test_reporte_anual_simplificado_conserva_orientacion_vertical(self) -> None:
        exporter = PdfReportExporter()
        context = {"report_type": "anual", "is_simplified_anual": True}
        rows = [{"estudiante": "Estudiante Sintético", "promedio_final": 8}]
        with patch.object(exporter, "_render_report_html", return_value="<html></html>"), patch.object(
            exporter, "export_to_pdf", return_value=True
        ) as export_to_pdf:
            exporter.exportar("reporte.pdf", "Reporte", context, rows)

        self.assertEqual(export_to_pdf.call_args.kwargs["orientation"], "portrait")

    def test_ocultar_filas_js_incluye_regla_para_guion(self) -> None:
        exporter = PdfReportExporter()
        captured_js: dict[str, str] = {}
        callback_called = {"value": False}

        class _FakePage:
            def runJavaScript(self, code, done):
                captured_js["code"] = code
                done(True)

        exporter._ocultar_filas_antes_de_pdf(_FakePage(), lambda: callback_called.__setitem__("value", True))
        self.assertIn("text === '—'", captured_js.get("code", ""))
        self.assertTrue(callback_called["value"])

    def test_render_html_con_placeholders_nuevos(self) -> None:
        exporter = PdfReportExporter()
        rows = [
            {
                "estudiante": "Lopez Maria",
                "aportes_calificacion": 9.2,
                "aportes_70": 6.4,
                "sumativas_calificacion": 8.7,
                "sumativas_30": 2.6,
                "promedio_final": 9.0,
                "cualitativa": "Excelente",
                "equivalencia": "DA",
                "observacion": "Aprobado",
            }
        ]

        custom_template = """
        <h1>[[institucion_nombre]]</h1>
        <p>[[institucion_subtitulo]]</p>
        <img src="[[logo_inst_src]]"/>
        <img src="[[logo_mineduc_src]]"/>
        <h2>Promedio General</h2>
        <div>[[promedio_general]]</div>
        <table><tbody>[[rows_html]]</tbody></table>
        <table><tbody>[[logros_rows_html]]</tbody></table>
        <section>[[chart_svg]]</section>
        """
        original_read_text = Path.read_text

        def fake_read_text(path_obj: Path, *args, **kwargs) -> str:
            if path_obj.name == "reporte_trimestral.html":
                return custom_template
            return original_read_text(path_obj, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            logo_inst = Path(tmp) / "logo_inst.png"
            logo_mineduc = Path(tmp) / "logo_mineduc.png"
            logo_inst.write_bytes(b"PNG")
            logo_mineduc.write_bytes(b"PNG")

            context = {
                "report_type": "trimestral",
                "trimestre_num": 1,
                "institucion_nombre": "UEEH",
                "institucion": {"parroquia": "Centro", "ciudad": "Quito"},
                "logo_path": str(logo_inst),
                "logo_ministerio_path": str(logo_mineduc),
            }

            with patch.object(Path, "read_text", new=fake_read_text):
                rendered = exporter._render_report_html(context, rows)

        self.assertIn("UEEH", rendered)
        self.assertIn("data:image/png;base64,", rendered)
        self.assertIn("Promedio General", rendered)
        self.assertIn("<svg", rendered)
        self.assertIn("class='nomina'", rendered)
        self.assertNotIn("[[", rendered)

    @unittest.skipIf(importlib.util.find_spec("reportlab") is None, "reportlab no instalado")
    def test_generar_archivo_pdf_no_vacio(self) -> None:
        exporter = PdfReportExporter()
        rows = [
            {
                "estudiante": "Lopez Maria",
                "trimestre_1": 8,
                "trimestre_2": 7,
                "trimestre_3": 6,
                "promedio_final": 7,
                "cualitativo": "B-",
                "observacion": "APB",
                "supletorio": None,
                "nota_definitiva": 7,
            }
        ]
        context = {"contexto_display": "AS1", "institucion_nombre": "UEEH", "report_type": "anual"}

        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp) / "reporte.pdf")
            result = exporter.exportar(output, "Reporte", context, rows)
            self.assertTrue(Path(result).exists())
            self.assertGreater(Path(result).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
