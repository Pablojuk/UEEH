"""Exportador de reportes académicos a PDF con diseño institucional."""

from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class PdfReportExporter:
    def exportar(self, output_path: str, report_title: str, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        if not rows:
            raise ValueError("No hay datos para exportar")

        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        if self._can_render_html_template():
            rendered = self._render_report_html(context, rows)
            if rendered:
                self._render_html_to_pdf(rendered, path)
                return str(path)

        return self._exportar_con_reportlab(path, report_title, context, rows)

    def _exportar_con_reportlab(
        self,
        path: Path,
        report_title: str,
        context: dict[str, Any],
        rows: list[dict[str, Any]],
    ) -> str:
        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.pdfgen import canvas
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("reportlab no está instalado") from exc

        c = canvas.Canvas(str(path), pagesize=landscape(letter))
        width, height = landscape(letter)

        self._draw_header(c, width, height, context, report_title)
        self._draw_general_info(c, width, height, context)

        if context.get("report_type") == "trimestral":
            self._draw_trimestral_table(c, width, height, rows)
            self._draw_logros_block(c, width, rows)
        else:
            self._draw_anual_table(c, width, height, rows)

        self._draw_signatures(c, width, context.get("firmantes", {}))
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
            ["Tutor", context.get("firmantes", {}).get("tutor_curso") or "N/D", "Nivel", context.get("curso_nivel", "N/D")],
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
            "Aportes/Insumos\nCalificación",
            "Aportes/Insumos\n70%",
            "Evaluaciones sumativas\nCalificación",
            "Evaluaciones sumativas\n30%",
            "Promedio Final",
            "Cualitativa",
            "Equivalencia",
            "Observación",
        ]
        data = [header1]
        for idx, row in enumerate(rows, start=1):
            data.append(
                [
                    idx,
                    row.get("estudiante", ""),
                    self._fmt(row.get("aportes_calificacion")),
                    self._fmt(row.get("aportes_70")),
                    self._fmt(row.get("sumativas_calificacion")),
                    self._fmt(row.get("sumativas_30")),
                    self._fmt(row.get("promedio_final")),
                    row.get("cualitativa", ""),
                    row.get("equivalencia", ""),
                    row.get("observacion", ""),
                ]
            )

        col_widths = [0.8 * cm, 6.0 * cm, 2.0 * cm, 1.8 * cm, 2.2 * cm, 1.8 * cm, 1.5 * cm, 1.6 * cm, 1.6 * cm, 1.8 * cm]
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
        table.drawOn(c, 1.0 * cm, 7.2 * cm)

    def _draw_anual_table(self, c, width: float, height: float, rows: list[dict[str, Any]]) -> None:
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm

        header_top = ["N°", "Nómina", "Primer Trimestre", "", "Segundo Trimestre", "", "Tercer Trimestre", "", "Promedio", "Cualitativa", "Supletorio", "Promedio Final", "Cualitativo", "Observación"]
        header_sub = ["", "", "Calificación", "Cualitativa", "Calificación", "Cualitativa", "Calificación", "Cualitativa", "", "", "", "", "", ""]
        data = [header_top, header_sub]
        for idx, row in enumerate(rows, start=1):
            data.append([
                idx,
                row.get("estudiante", ""),
                self._fmt(row.get("trimestre_1")),
                row.get("equivalencia_t1", ""),
                self._fmt(row.get("trimestre_2")),
                row.get("equivalencia_t2", ""),
                self._fmt(row.get("trimestre_3")),
                row.get("equivalencia_t3", ""),
                self._fmt(row.get("promedio")),
                row.get("cualitativa_anual", ""),
                self._fmt(row.get("supletorio")),
                self._fmt(row.get("promedio_final")),
                row.get("cualitativo_final", ""),
                row.get("observacion", ""),
            ])

        table = Table(data, colWidths=[0.8*cm, 5.1*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.1*cm, 1.3*cm, 1.4*cm, 1.4*cm], repeatRows=2)
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

        logro_counts = self._build_logros(rows)
        total = max(len(rows), 1)

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

        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.charts.piecharts import Pie
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

    def _draw_signatures(self, c, width: float, firmantes: dict[str, str]) -> None:
        from reportlab.lib.units import cm

        roles = [
            ("Docente", firmantes.get("docente", "")),
            ("Coordinador de Área", firmantes.get("coordinador_area", "")),
            ("Rector", firmantes.get("rector", "")),
            ("Tutor de Curso", firmantes.get("tutor_curso", "")),
        ]
        start_x = 2 * cm
        gap = (width - 4 * cm) / 4
        y = 1.2 * cm
        for idx, (role, firma) in enumerate(roles):
            x = start_x + idx * gap
            c.line(x, y + 0.8 * cm, x + 3.8 * cm, y + 0.8 * cm)
            c.setFont("Helvetica", 7)
            c.drawCentredString(x + 1.9 * cm, y + 0.45 * cm, firma or "")
            c.drawCentredString(x + 1.9 * cm, y + 0.2 * cm, role)

    @staticmethod
    def _fmt(value: Any) -> str:
        if value is None:
            return ""
        try:
            return f"{float(value):.2f}"
        except Exception:  # noqa: BLE001
            return str(value)

    @staticmethod
    def _build_logros(rows: list[dict[str, Any]]) -> list[tuple[str, str, int, float]]:
        total = max(len(rows), 1)
        defs = [
            ("Destreza alcanzada", "DA"),
            ("Alcanza los Aprendizajes", "AA"),
            ("Próximo a alcanzar", "PA"),
            ("No alcanza los aprendizajes", "NA"),
        ]
        counts = {sigla: 0 for _, sigla in defs}
        for row in rows:
            sigla = str(row.get("equivalencia") or "").strip()
            if sigla in counts:
                counts[sigla] += 1
        return [
            (label, sigla, counts[sigla], round((counts[sigla] / total) * 100, 2))
            for label, sigla in defs
        ]

    @staticmethod
    def _can_render_html_template() -> bool:
        try:
            from PySide6.QtGui import QTextDocument  # noqa: F401
            from PySide6.QtPrintSupport import QPrinter  # noqa: F401
            return True
        except Exception:  # noqa: BLE001
            return False

    def _render_report_html(self, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        template_name = "reporte_trimestral.html" if context.get("report_type") == "trimestral" else "reporte_anual.html"
        template_path = Path(__file__).resolve().parent.parent / "templates" / template_name
        if not template_path.exists():
            return ""

        template = template_path.read_text(encoding="utf-8")
        if context.get("report_type") == "trimestral":
            body_rows = self._build_trimestral_rows_html(rows)
        else:
            body_rows = self._build_anual_rows_html(rows)
        logros_rows = self._build_logros_rows_html(rows)
        promedio_general = self._fmt(sum((r.get("promedio_final") or 0) for r in rows) / max(len(rows), 1))
        values = {
            "institucion_nombre": context.get("institucion_nombre", "Institución"),
            "docente_nombre": context.get("docente_nombre", ""),
            "docente": context.get("docente_nombre", ""),
            "asignatura_nombre": context.get("asignatura_nombre", ""),
            "asignatura": context.get("asignatura_nombre", ""),
            "curso_nombre": context.get("curso_nombre", ""),
            "curso": context.get("curso_nombre", ""),
            "paralelo_nombre": context.get("paralelo_nombre", ""),
            "paralelo": context.get("paralelo_nombre", ""),
            "nivel": context.get("curso_nivel", ""),
            "trimestre": f"Trimestre {context.get('trimestre_num')}" if context.get("report_type") == "trimestral" else "Anual",
            "periodo": f"Trimestre {context.get('trimestre_num')}" if context.get("report_type") == "trimestral" else "Anual",
            "tutor": context.get("firmantes", {}).get("tutor_curso", ""),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "rows_html": body_rows,
            "logros_rows_html": logros_rows,
            "promedio_general": promedio_general,
            "firma_docente": context.get("firmantes", {}).get("docente", ""),
            "firma_coordinador": context.get("firmantes", {}).get("coordinador_area", ""),
            "firma_rector": context.get("firmantes", {}).get("rector", ""),
            "firma_tutor": context.get("firmantes", {}).get("tutor_curso", ""),
        }
        values.update(context.get("template_data", {}))
        rendered = template
        raw_keys = {"rows_html", "logros_rows_html"}
        pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}|\[\[\s*([a-zA-Z0-9_]+)\s*\]\]")

        def replace_token(match: re.Match[str]) -> str:
            key = match.group(1) or match.group(2) or ""
            value = values.get(key, "")
            return str(value) if key in raw_keys else html.escape(str(value))

        rendered = pattern.sub(replace_token, rendered)
        return rendered

    def _render_html_to_pdf(self, html_content: str, output_path: Path) -> None:
        from PySide6.QtCore import QMarginsF, QSizeF
        from PySide6.QtGui import QPageLayout, QPageSize, QPainter
        from PySide6.QtGui import QTextDocument
        from PySide6.QtPrintSupport import QPrinter
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        _ = app  # mantener referencia
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(output_path))
        printer.setPageOrientation(QPageLayout.Landscape)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageMargins(QMarginsF(10, 10, 10, 10))
        document = QTextDocument()
        document.setDocumentMargin(0)
        document.setHtml(html_content)
        page_rect = printer.pageRect(QPrinter.DevicePixel)
        document.setPageSize(QSizeF(float(page_rect.width()), float(page_rect.height())))
        painter = QPainter(printer)
        document.drawContents(painter)
        painter.end()

    def _build_trimestral_rows_html(self, rows: list[dict[str, Any]]) -> str:
        html_rows: list[str] = []
        for idx, row in enumerate(rows, start=1):
            html_rows.append(
                "<tr>"
                f"<td>{idx}</td>"
                f"<td>{html.escape(str(row.get('estudiante', '')))}</td>"
                f"<td>{self._fmt(row.get('aportes_calificacion'))}</td>"
                f"<td>{self._fmt(row.get('aportes_70'))}</td>"
                f"<td>{self._fmt(row.get('sumativas_calificacion'))}</td>"
                f"<td>{self._fmt(row.get('sumativas_30'))}</td>"
                f"<td>{self._fmt(row.get('promedio_final'))}</td>"
                f"<td>{html.escape(str(row.get('cualitativa', '')))}</td>"
                f"<td>{html.escape(str(row.get('equivalencia', '')))}</td>"
                f"<td>{html.escape(str(row.get('observacion', '')))}</td>"
                "</tr>"
            )
        for _ in range(len(rows), 34):
            html_rows.append("<tr><td>&nbsp;</td>" + "<td>&nbsp;</td>" * 9 + "</tr>")
        return "".join(html_rows)

    def _build_anual_rows_html(self, rows: list[dict[str, Any]]) -> str:
        html_rows: list[str] = []
        for idx, row in enumerate(rows, start=1):
            html_rows.append(
                "<tr>"
                f"<td>{idx}</td>"
                f"<td>{html.escape(str(row.get('estudiante', '')))}</td>"
                f"<td>{self._fmt(row.get('trimestre_1'))}</td><td>{html.escape(str(row.get('equivalencia_t1', '')))}</td>"
                f"<td>{self._fmt(row.get('trimestre_2'))}</td><td>{html.escape(str(row.get('equivalencia_t2', '')))}</td>"
                f"<td>{self._fmt(row.get('trimestre_3'))}</td><td>{html.escape(str(row.get('equivalencia_t3', '')))}</td>"
                f"<td>{self._fmt(row.get('promedio'))}</td>"
                f"<td>{html.escape(str(row.get('cualitativa_anual', '')))}</td>"
                f"<td>{self._fmt(row.get('supletorio'))}</td>"
                f"<td>{self._fmt(row.get('promedio_final'))}</td>"
                f"<td>{html.escape(str(row.get('observacion', '')))}</td>"
                "</tr>"
            )
        for _ in range(len(rows), 34):
            html_rows.append("<tr><td>&nbsp;</td>" + "<td>&nbsp;</td>" * 12 + "</tr>")
        return "".join(html_rows)

    def _build_logros_rows_html(self, rows: list[dict[str, Any]]) -> str:
        scale_map = {"DA": "9 - 10", "AA": "7 - 8,99", "PA": "5 - 6,99", "NA": "<= 5"}
        parts: list[str] = []
        for detalle, sigla, count, pct in self._build_logros(rows):
            parts.append(
                "<tr>"
                f"<td>{html.escape(detalle)}</td>"
                f"<td>{html.escape(scale_map[sigla])}</td>"
                f"<td>{html.escape(sigla)} ({count})</td>"
                f"<td>{pct}%</td>"
                "</tr>"
            )
        return "".join(parts)
