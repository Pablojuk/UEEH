"""Exportador de reportes académicos a Excel (.xlsx) con diseño institucional."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ExcelReportExporter:
    def exportar(self, output_path: str, report_title: str, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("openpyxl no está instalado") from exc

        if not rows:
            raise ValueError("No hay datos para exportar")

        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        wb = Workbook()
        ws = wb.active
        ws.title = "Informe"

        thin = Side(style="thin", color="000000")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        ws.merge_cells("A1:N1")
        ws["A1"] = context.get("institucion_nombre") or "Institución"
        ws["A1"].font = Font(bold=True, size=13)
        ws["A1"].alignment = Alignment(horizontal="center")

        ws.merge_cells("A2:N2")
        ws["A2"] = report_title.upper()
        ws["A2"].font = Font(bold=True, size=12)
        ws["A2"].alignment = Alignment(horizontal="center")

        ws["A4"] = "Docente"; ws["B4"] = context.get("docente_nombre", "N/D")
        ws["D4"] = "Asignatura"; ws["E4"] = context.get("asignatura_nombre", "N/D")
        ws["G4"] = "Curso"; ws["H4"] = context.get("curso_nombre", "N/D")
        ws["J4"] = "Paralelo"; ws["K4"] = context.get("paralelo_nombre", "N/D")

        for cell in ("A4", "D4", "G4", "J4"):
            ws[cell].font = Font(bold=True)

        if context.get("report_type") == "trimestral":
            headers = [
                "N°", "Nómina",
                "Aportes/Insumos Calificación", "Aportes/Insumos 70%",
                "Evaluaciones sumativas Calificación", "Evaluaciones sumativas 30%",
                "Promedio Final", "Cualitativa", "Equivalencia", "Observación",
            ]
            start_row = 6
            for col, title in enumerate(headers, start=1):
                cell = ws.cell(row=start_row, column=col, value=title)
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
                cell.border = border

            for idx, row in enumerate(rows, start=1):
                r = start_row + idx
                values = [
                    idx,
                    row.get("estudiante", ""),
                    row.get("aportes_calificacion"),
                    row.get("aportes_70"),
                    row.get("sumativas_calificacion"),
                    row.get("sumativas_30"),
                    row.get("promedio_final"),
                    row.get("cualitativa", ""),
                    row.get("equivalencia", ""),
                    row.get("observacion", ""),
                ]
                for cidx, value in enumerate(values, start=1):
                    cell = ws.cell(row=r, column=cidx, value=value)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    cell.border = border
                    if isinstance(value, (int, float)) and cidx != 1:
                        cell.number_format = "0.00"
            widths = [5, 30, 14, 12, 15, 12, 10, 10, 10, 12]
        else:
            headers = [
                "N°", "Nómina",
                "Primer Trimestre Calificación", "Primer Trimestre Cualitativa",
                "Segundo Trimestre Calificación", "Segundo Trimestre Cualitativa",
                "Tercer Trimestre Calificación", "Tercer Trimestre Cualitativa",
                "Promedio", "Cualitativa", "Supletorio", "Promedio Final", "Cualitativo Final", "Observación",
            ]
            start_row = 6
            for col, title in enumerate(headers, start=1):
                cell = ws.cell(row=start_row, column=col, value=title)
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
                cell.border = border
            for idx, row in enumerate(rows, start=1):
                r = start_row + idx
                values = [
                    idx,
                    row.get("estudiante", ""),
                    row.get("trimestre_1"),
                    row.get("equivalencia_t1", ""),
                    row.get("trimestre_2"),
                    row.get("equivalencia_t2", ""),
                    row.get("trimestre_3"),
                    row.get("equivalencia_t3", ""),
                    row.get("promedio"),
                    row.get("cualitativa_anual", ""),
                    row.get("supletorio"),
                    row.get("promedio_final"),
                    row.get("cualitativo_final", ""),
                    row.get("observacion", ""),
                ]
                for cidx, value in enumerate(values, start=1):
                    cell = ws.cell(row=r, column=cidx, value=value)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    cell.border = border
                    if isinstance(value, (int, float)) and cidx != 1:
                        cell.number_format = "0.00"
            widths = [5, 30, 12, 12, 12, 12, 12, 12, 9, 10, 10, 10, 12, 12]

        for idx, w in enumerate(widths, start=1):
            ws.column_dimensions[chr(ord("A") + idx - 1)].width = w

        self._draw_signatures(ws, start_row + len(rows) + 3, len(widths), context.get("firmantes", {}))
        wb.save(str(path))
        return str(path)

    @staticmethod
    def _draw_signatures(ws, start_row: int, max_cols: int, firmantes: dict[str, str]) -> None:
        from openpyxl.styles import Alignment

        roles = [
            ("Docente", firmantes.get("docente", "")),
            ("Coordinador de Área", firmantes.get("coordinador_area", "")),
            ("Rector", firmantes.get("rector", "")),
            ("Tutor de Curso", firmantes.get("tutor_curso", "")),
        ]
        block = max(1, max_cols // 4)
        for idx, (rol, firma) in enumerate(roles):
            col_start = (idx * block) + 1
            col_end = min(max_cols, col_start + block - 1)
            ws.merge_cells(start_row=start_row, start_column=col_start, end_row=start_row, end_column=col_end)
            ws.merge_cells(start_row=start_row + 1, start_column=col_start, end_row=start_row + 1, end_column=col_end)
            ws.merge_cells(start_row=start_row + 2, start_column=col_start, end_row=start_row + 2, end_column=col_end)
            ws.cell(row=start_row, column=col_start, value="_____________________________")
            ws.cell(row=start_row + 1, column=col_start, value=firma or "")
            ws.cell(row=start_row + 2, column=col_start, value=rol)
            ws.cell(row=start_row, column=col_start).alignment = Alignment(horizontal="center")
            ws.cell(row=start_row + 1, column=col_start).alignment = Alignment(horizontal="center")
            ws.cell(row=start_row + 2, column=col_start).alignment = Alignment(horizontal="center")
