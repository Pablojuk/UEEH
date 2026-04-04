"""Pruebas del exportador Excel."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from src.infrastructure.exporters.excel_report_exporter import ExcelReportExporter


@unittest.skipIf(importlib.util.find_spec("openpyxl") is None, "openpyxl no instalado")
class TestExcelReportExporter(unittest.TestCase):
    def test_generar_archivo_excel_no_vacio_y_encabezados(self) -> None:
        from openpyxl import load_workbook

        exporter = ExcelReportExporter()
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
            output = str(Path(tmp) / "reporte.xlsx")
            result = exporter.exportar(output, "Reporte", context, rows)
            self.assertTrue(Path(result).exists())
            self.assertGreater(Path(result).stat().st_size, 0)

            wb = load_workbook(result)
            ws = wb.active
            self.assertEqual(ws["A5"].value, "Estudiante")
            self.assertEqual(ws["B5"].value, "Trimestre 1")
            wb.close()


if __name__ == "__main__":
    unittest.main()
