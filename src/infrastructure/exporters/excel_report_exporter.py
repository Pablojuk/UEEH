"""Exportador de reportes académicos a Excel (.xlsx)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ExcelReportExporter:
    HEADERS = [
        "Estudiante",
        "Trimestre 1",
        "Trimestre 2",
        "Trimestre 3",
        "Promedio Final",
        "Cualitativo",
        "Observacion",
        "Supletorio",
        "Nota Definitiva",
    ]

    def exportar(self, output_path: str, report_title: str, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("openpyxl no está instalado") from exc

        if not rows:
            raise ValueError("No hay datos para exportar")

        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        wb = Workbook()
        ws = wb.active
        ws.title = "Resumen"

        ws["A1"] = report_title
        ws["A1"].font = Font(bold=True, size=13)
        ws["A2"] = f"Institución: {context.get('institucion_nombre') or 'Institución no configurada'}"
        ws["A3"] = f"Contexto: {context.get('contexto_display', 'N/D')}"

        header_row = 5
        for idx, title in enumerate(self.HEADERS, start=1):
            cell = ws.cell(row=header_row, column=idx, value=title)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")

        row_index = header_row + 1
        for row in rows:
            values = [
                row.get("estudiante", ""),
                row.get("trimestre_1"),
                row.get("trimestre_2"),
                row.get("trimestre_3"),
                row.get("promedio_final"),
                row.get("cualitativo", ""),
                row.get("observacion", ""),
                row.get("supletorio"),
                row.get("nota_definitiva"),
            ]
            for col, value in enumerate(values, start=1):
                ws.cell(row=row_index, column=col, value=value)
            row_index += 1

        widths = {1: 28, 2: 12, 3: 12, 4: 12, 5: 14, 6: 12, 7: 14, 8: 12, 9: 14}
        for col_idx, width in widths.items():
            col_letter = chr(ord("A") + col_idx - 1)
            ws.column_dimensions[col_letter].width = width

        wb.save(str(path))
        return str(path)
