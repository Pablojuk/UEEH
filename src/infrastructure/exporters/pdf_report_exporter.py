"""Exportador de reportes académicos a PDF con diseño institucional."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


class PdfReportExporter:
    def exportar(self, output_path: str, report_title: str, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib.units import cm
            from reportlab.pdfgen import canvas
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics.charts.piecharts import Pie
            from reportlab.platypus import Table, TableStyle
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("reportlab no está instalado") from exc

        if not rows:
            raise ValueError("No hay datos para exportar")

        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(path), pagesize=landscape(letter))
        width, height = landscape(letter)

        self._draw_header(c, width, height, context, report_title)
        self._draw_general_info(c, width, height, context)

        if context.get("report_type") == "trimestral":
            self._draw_trimestral_table(c, width, height, rows)
            self._draw_logros_block(c, width, rows)
        else:
            self._draw_anual_table(c, width, height, rows)

        self._draw_signatures(c, width)
        c.save()
        return str(path)

    def _draw_header(self, c, width: float, height: float, context: dict[str, Any], report_title: str) -> None:
        from reportlab.lib.units import cm

        for xpos, logo_key in ((1.5 * cm, "logo_ministerio_path"), (width - 5.5 * cm, "logo_path")):
            logo_path = context.get(logo_key)
            if logo_path and Path(logo_path).exists():
                c.drawImage(str(logo_path), xpos, height - 3.2 * cm, width=4 * cm, height=2 * cm, preserveAspectRatio=True)

        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, height - 1.2 * cm, context.get("institucion_nombre") or "Institución")
        c.setFont("Helvetica", 9)
        ubicacion = " - ".join(
            filter(None, [context.get("institucion", {}).get("ciudad"), context.get("institucion", {}).get("parroquia")])
        )
        c.drawCentredString(width / 2, height - 1.8 * cm, ubicacion or "Ubicación no registrada")
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(width / 2, height - 2.5 * cm, report_title.upper())

    def _draw_general_info(self, c, width: float, height: float, context: dict[str, Any]) -> None:
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm

        trimestre_text = (
            f"Trimestre {context.get('trimestre_num')}" if context.get("report_type") == "trimestral" else "Anual"
        )
        data = [
            ["Docente", context.get("docente_nombre", "N/D"), "Asignatura", context.get("asignatura_nombre", "N/D")],
            ["Curso", context.get("curso_nombre", "N/D"), "Paralelo", context.get("paralelo_nombre", "N/D")],
            ["Tutor", context.get("docente_nombre", "N/D"), "Nivel", context.get("curso_nombre", "N/D")],
            ["Trimestre", trimestre_text, "Fecha", datetime.now().strftime("%Y-%m-%d")],
        ]
        table = Table(data, colWidths=[2.3 * cm, 7.2 * cm, 2.3 * cm, 7.2 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#FDE68A")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#FDE68A")),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        table.wrapOn(c, width - 3 * cm, height)
        table.drawOn(c, 1.5 * cm, height - 6.5 * cm)

    def _draw_trimestral_table(self, c, width: float, height: float, rows: list[dict[str, Any]]) -> None:
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm

        header1 = [
            "N°",
            "Nómina",
            "Aportes/Insumos",
            "70%",
            "Proyecto Integrador",
            "15%",
            "Examen",
            "15%",
            "Promedio",
            "Cualitativa",
            "Supletorio",
            "Promedio Final",
            "Observación",
            "Logro de evaluación\nde aprendizaje",
        ]
        data = [header1]
        for idx, row in enumerate(rows, start=1):
            aportes = row.get("aportes")
            proyecto = row.get("proyecto_integrador")
            examen = row.get("examen")
            data.append(
                [
                    idx,
                    row.get("estudiante", ""),
                    self._fmt(aportes),
                    self._fmt((aportes or 0) * 0.70 if aportes is not None else None),
                    self._fmt(proyecto),
                    self._fmt((proyecto or 0) * 0.15 if proyecto is not None else None),
                    self._fmt(examen),
                    self._fmt((examen or 0) * 0.15 if examen is not None else None),
                    self._fmt(row.get("promedio")),
                    row.get("cualitativo", ""),
                    self._fmt(row.get("supletorio")),
                    self._fmt(row.get("promedio_final")),
                    "",
                    row.get("logro", ""),
                ]
            )

        col_widths = [0.8 * cm, 5.6 * cm, 1.4 * cm, 1.0 * cm, 1.6 * cm, 1.0 * cm, 1.3 * cm, 1.0 * cm, 1.3 * cm, 1.4 * cm, 1.2 * cm, 1.4 * cm, 1.4 * cm, 2.2 * cm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.45, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (1, 1), (1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        table.wrapOn(c, width - 3 * cm, height)
        table.drawOn(c, 1.0 * cm, 6.1 * cm)

    def _draw_anual_table(self, c, width: float, height: float, rows: list[dict[str, Any]]) -> None:
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm

        header_top = ["N°", "Nómina", "Primer Trimestre", "", "Segundo Trimestre", "", "Tercer Trimestre", "", "Promedio", "Cualitativa", "Supletorio", "Promedio Final", "Observación"]
        header_sub = ["", "", "Calificación", "Cualitativa", "Calificación", "Cualitativa", "Calificación", "Cualitativa", "", "", "", "", ""]
        data = [header_top, header_sub]
        for idx, row in enumerate(rows, start=1):
            data.append([
                idx,
                row.get("estudiante", ""),
                self._fmt(row.get("trimestre_1")),
                "",
                self._fmt(row.get("trimestre_2")),
                "",
                self._fmt(row.get("trimestre_3")),
                "",
                self._fmt(row.get("promedio_final")),
                row.get("cualitativo", ""),
                self._fmt(row.get("supletorio")),
                self._fmt(row.get("nota_definitiva")),
                row.get("observacion", ""),
            ])

        table = Table(data, colWidths=[0.8*cm, 5.5*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.2*cm, 1.4*cm, 1.6*cm], repeatRows=2)
        style = [
            ("GRID", (0, 0), (-1, -1), 0.45, colors.black),
            ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#E5E7EB")),
            ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
            ("SPAN", (2, 0), (3, 0)),
            ("SPAN", (4, 0), (5, 0)),
            ("SPAN", (6, 0), (7, 0)),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (1, 2), (1, -1), "LEFT"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]
        table.setStyle(TableStyle(style))
        table.wrapOn(c, width - 3 * cm, height)
        table.drawOn(c, 1.0 * cm, 6.3 * cm)

    def _draw_logros_block(self, c, width: float, rows: list[dict[str, Any]]) -> None:
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm

        total = max(len(rows), 1)
        ranges = [
            ("Destreza alcanzada", "DA", lambda v: v is not None and 9 <= v <= 10),
            ("Alcanza los Aprendizajes", "AA", lambda v: v is not None and 7 <= v < 9),
            ("Próximo a alcanzar", "PA", lambda v: v is not None and 5 <= v < 7),
            ("No alcanza los aprendizajes", "NA", lambda v: v is not None and v < 5),
        ]
        logro_counts = []
        for detail, sigla, fn in ranges:
            count = sum(1 for r in rows if fn(r.get("promedio_final")))
            logro_counts.append((detail, sigla, count, round((count / total) * 100, 2)))

        data = [["Cuadro de logros en la evaluación de los aprendizajes", "", "", ""], ["Detalle", "Escala", "Siglas", "%"]]
        scale_map = {"DA": "9 - 10", "AA": "7 - 8,99", "PA": "5 - 6,99", "NA": "<= 5"}
        for detail, sigla, count, pct in logro_counts:
            data.append([detail, scale_map[sigla], f"{sigla} ({count})", f"{pct}%"])
        promedio_general = sum((r.get("promedio_final") or 0) for r in rows) / total
        data.append(["Promedio", "", self._fmt(promedio_general), ""])

        table = Table(data, colWidths=[5.8 * cm, 2.0 * cm, 2.0 * cm, 1.6 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.45, colors.black),
                    ("SPAN", (0, 0), (-1, 0)),
                    ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#E5E7EB")),
                    ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (0, 2), (0, -1), "LEFT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                ]
            )
        )
        table.wrapOn(c, width, 5 * cm)
        table.drawOn(c, 1.2 * cm, 2.2 * cm)

        drawing = Drawing(6 * cm, 4 * cm)
        pie = Pie()
        pie.x = 1.0 * cm
        pie.y = 0
        pie.width = 3.8 * cm
        pie.height = 3.8 * cm
        pie.labels = [item[1] for item in logro_counts]
        pie.data = [max(1, item[2]) for item in logro_counts]
        pie.slices.strokeWidth = 0.5
        drawing.add(pie)
        drawing.drawOn(c, width - 8.2 * cm, 2.1 * cm)

    def _draw_signatures(self, c, width: float) -> None:
        from reportlab.lib.units import cm

        roles = ["Docente", "Coordinador de Área", "Rector", "Tutor de Curso"]
        start_x = 2 * cm
        gap = (width - 4 * cm) / 4
        y = 1.2 * cm
        for idx, role in enumerate(roles):
            x = start_x + idx * gap
            c.line(x, y + 0.8 * cm, x + 3.8 * cm, y + 0.8 * cm)
            c.setFont("Helvetica", 7)
            c.drawCentredString(x + 1.9 * cm, y + 0.4 * cm, role)

    @staticmethod
    def _fmt(value: Any) -> str:
        if value is None:
            return ""
        try:
            return f"{float(value):.2f}"
        except Exception:  # noqa: BLE001
            return str(value)
