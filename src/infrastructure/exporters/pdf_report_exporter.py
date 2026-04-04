"""Exportador de reportes académicos a PDF."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


class PdfReportExporter:
    """Genera un PDF legible con contexto y tabla de resultados."""

    HEADERS = [
        "Estudiante",
        "T1",
        "T2",
        "T3",
        "Promedio",
        "Cualitativo",
        "Observación",
        "Supletorio",
        "Definitiva",
    ]

    def exportar(self, output_path: str, report_title: str, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib.units import cm
            from reportlab.pdfgen import canvas
            from reportlab.platypus import Table, TableStyle
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("reportlab no está instalado") from exc

        if not rows:
            raise ValueError("No hay datos para exportar")

        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(path), pagesize=landscape(letter))
        width, height = landscape(letter)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, height - 2 * cm, report_title)

        c.setFont("Helvetica", 9)
        institution_name = context.get("institucion_nombre") or "Institución no configurada"
        c.drawString(2 * cm, height - 2.7 * cm, f"Institución: {institution_name}")
        c.drawString(2 * cm, height - 3.3 * cm, f"Contexto: {context.get('contexto_display', 'N/D')}")
        c.drawString(2 * cm, height - 3.9 * cm, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        data = [self.HEADERS]
        for row in rows:
            data.append(
                [
                    str(row.get("estudiante", "")),
                    self._fmt(row.get("trimestre_1")),
                    self._fmt(row.get("trimestre_2")),
                    self._fmt(row.get("trimestre_3")),
                    self._fmt(row.get("promedio_final")),
                    str(row.get("cualitativo", "")),
                    str(row.get("observacion", "")),
                    self._fmt(row.get("supletorio")),
                    self._fmt(row.get("nota_definitiva")),
                ]
            )

        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ]
            )
        )

        table_width, table_height = table.wrapOn(c, width - 4 * cm, height - 7 * cm)
        table.drawOn(c, 2 * cm, max(2 * cm, height - 5 * cm - table_height))

        c.setFont("Helvetica-Oblique", 8)
        c.drawString(2 * cm, 1.2 * cm, "Generado por Sistema Académico UEEH")

        c.save()
        return str(path)

    @staticmethod
    def _fmt(value: Any) -> str:
        if value is None:
            return ""
        return str(value)
