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

        self._add_logos(ws, context)

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
            signatures_row = start_row + len(rows) + 3
        else:
            headers = [
                "N°", "Nómina",
                "Primer Trimestre Calificación", "Primer Trimestre Cualitativa",
                "Segundo Trimestre Calificación", "Segundo Trimestre Cualitativa",
                "Tercer Trimestre Calificación", "Tercer Trimestre Cualitativa",
                "Promedio", "Cualitativa", "Supletorio", "Promedio Final", "Cualitativo", "Observación",
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
            signatures_row = self._draw_annual_statistics(ws, start_row + len(rows) + 3, border, rows)

        for idx, w in enumerate(widths, start=1):
            ws.column_dimensions[chr(ord("A") + idx - 1)].width = w

        self._draw_signatures(ws, signatures_row, len(widths), context.get("firmantes", {}))
        wb.save(str(path))
        return str(path)

    @staticmethod
    def _add_logos(ws, context: dict[str, Any]) -> None:
        try:
            from openpyxl.drawing.image import Image
        except Exception:  # noqa: BLE001
            return

        logos = [
            (context.get("logo_path"), "A1"),
            (context.get("logo_ministerio_path"), "M1"),
        ]
        for logo_path, anchor in logos:
            if not logo_path:
                continue
            path = Path(str(logo_path)).expanduser().resolve()
            if not path.exists():
                continue
            try:
                image = Image(str(path))
                image.width = 70
                image.height = 50
                ws.add_image(image, anchor)
            except Exception:  # noqa: BLE001
                continue

    def _draw_annual_statistics(self, ws, start_row: int, border, rows: list[dict[str, Any]]) -> int:
        from openpyxl.chart import PieChart, Reference
        from openpyxl.styles import Alignment, Font

        aprobados, reprobados = self._count_observations(rows)
        total = aprobados + reprobados
        pct_aprobados = round((aprobados / total) * 100, 2) if total else 0
        pct_reprobados = round((reprobados / total) * 100, 2) if total else 0
        promedio = self._average_promedio_final(rows)

        ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=6)
        title_cell = ws.cell(row=start_row, column=1, value="Cuadro de logros en la evaluación de los aprendizajes")
        title_cell.font = Font(bold=True)
        title_cell.alignment = Alignment(horizontal="center")
        for col in range(1, 7):
            ws.cell(row=start_row, column=col).border = border

        labels = ["Total aprobados", "Total reprobados"]
        values = [aprobados, reprobados]
        percentages = [pct_aprobados, pct_reprobados]

        for idx, label in enumerate(labels, start=1):
            r = start_row + idx
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
            ws.cell(row=r, column=1, value=label).alignment = Alignment(horizontal="left")
            ws.cell(row=r, column=5, value=values[idx - 1]).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=6, value=percentages[idx - 1] / 100).number_format = "0%"
            ws.cell(row=r, column=6).alignment = Alignment(horizontal="center")
            for col in range(1, 7):
                ws.cell(row=r, column=col).border = border

        promedio_row = start_row + 4
        ws.merge_cells(start_row=promedio_row, start_column=1, end_row=promedio_row, end_column=5)
        ws.cell(row=promedio_row, column=1, value="Promedio").alignment = Alignment(horizontal="center")
        ws.cell(row=promedio_row, column=6, value=promedio if promedio is not None else "—")
        if promedio is not None:
            ws.cell(row=promedio_row, column=6).number_format = "0.00"
        ws.cell(row=promedio_row, column=6).alignment = Alignment(horizontal="center")
        for col in range(1, 7):
            ws.cell(row=promedio_row, column=col).border = border

        chart = PieChart()
        chart.title = "Aprobados/Reprobados"
        data = Reference(ws, min_col=5, min_row=start_row + 1, max_row=start_row + 2)
        cats = Reference(ws, min_col=1, min_row=start_row + 1, max_row=start_row + 2)
        chart.add_data(data, titles_from_data=False)
        chart.set_categories(cats)
        chart.height = 5
        chart.width = 8
        ws.add_chart(chart, f"H{start_row}")

        return promedio_row + 3

    @staticmethod
    def _count_observations(rows: list[dict[str, Any]]) -> tuple[int, int]:
        aprobados = 0
        reprobados = 0
        for row in rows:
            obs = str(row.get("observacion", "")).strip().lower()
            has_final = row.get("promedio_final") is not None
            if obs in {"aprobado", "apr", "apb"}:
                aprobados += 1
            elif obs or has_final:
                reprobados += 1
        return aprobados, reprobados

    @staticmethod
    def _average_promedio_final(rows: list[dict[str, Any]]) -> float | None:
        values: list[float] = []
        for row in rows:
            value = row.get("promedio_final")
            if value is None:
                continue
            try:
                values.append(float(value))
            except Exception:  # noqa: BLE001
                continue
        if not values:
            return None
        return round(sum(values) / len(values), 2)

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
