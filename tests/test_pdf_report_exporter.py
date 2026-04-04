"""Pruebas del exportador PDF."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from src.infrastructure.exporters.pdf_report_exporter import PdfReportExporter


@unittest.skipIf(importlib.util.find_spec("reportlab") is None, "reportlab no instalado")
class TestPdfReportExporter(unittest.TestCase):
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
        context = {"contexto_display": "AS1", "institucion_nombre": "UEEH"}

        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp) / "reporte.pdf")
            result = exporter.exportar(output, "Reporte", context, rows)
            self.assertTrue(Path(result).exists())
            self.assertGreater(Path(result).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
