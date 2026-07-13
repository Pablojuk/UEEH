"""Renderizador HTML reutilizable para reportes académicos institucionales."""

from __future__ import annotations

import html
import math
import re
import base64
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any

from src.domain.calculations import ESCALA_CUALITATIVA_ACADEMICA


class HtmlReportRenderer:
    def render(self, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        simplified_trimestral = bool(context.get("report_type") == "trimestral" and context.get("is_simplified_trimestral"))
        simplified_anual = bool(context.get("report_type") == "anual" and context.get("is_simplified_anual"))
        if simplified_trimestral:
            template_name = "reporte_trimestral_simplificado.html"
        elif simplified_anual:
            template_name = "reporte_anual_simplificado_egb.html"
        else:
            template_name = "reporte_trimestral.html" if context.get("report_type") == "trimestral" else "reporte_anual.html"
        template_path = Path(__file__).resolve().parent.parent / "templates" / template_name
        if not template_path.exists():
            return ""

        template = template_path.read_text(encoding="utf-8")
        is_trimestral = context.get("report_type") == "trimestral"
        body_rows = self._build_simplified_trimestral_rows_html(rows) if simplified_trimestral else (
            self._build_trimestral_rows_html(rows) if is_trimestral else (
                self._build_simplified_anual_rows_html(rows) if simplified_anual else self._build_anual_rows_html(rows)
            )
        )
        logros_rows = self._build_simplified_stats_rows_html(rows, use_anual=bool(simplified_anual)) if (simplified_trimestral or simplified_anual) else (
            self._build_logros_rows_html(rows) if is_trimestral else ""
        )
        estadistica_rows = self._build_estadistica_rows_html(rows) if not is_trimestral else ""
        chart_svg = self._build_simplified_trimestral_chart_html(rows, use_anual=bool(simplified_anual)) if (simplified_trimestral or simplified_anual) else (
            self._build_trimestral_chart_svg(rows) if is_trimestral else self._build_anual_chart_svg(rows)
        )
        promedio_field = "promedio" if simplified_anual else "promedio_final"
        promedio_general = self._fmt(
            sum((float(r.get(promedio_field)) for r in rows if not self._is_empty_value(r.get(promedio_field))), 0.0)
            / max(sum(1 for r in rows if not self._is_empty_value(r.get(promedio_field))), 1)
        )
        values = {
            "institucion_nombre": context.get("institucion_nombre", "Institución"),
            "institucion_subtitulo": self._build_institucion_subtitulo(context),
            "logo_inst_src": self._build_logo_source(context.get("logo_path"), "institucional"),
            "logo_mineduc_src": self._build_logo_source(context.get("logo_ministerio_path"), "ministerio"),
            "docente_nombre": context.get("docente_nombre", ""),
            "docente": context.get("docente_nombre", ""),
            "asignatura_nombre": context.get("asignatura_nombre", ""),
            "asignatura": context.get("asignatura_nombre", ""),
            "curso_nombre": context.get("curso_nombre", ""),
            "curso": context.get("curso_nombre", ""),
            "paralelo_nombre": context.get("paralelo_nombre", ""),
            "paralelo": context.get("paralelo_nombre", ""),
            "nivel": context.get("curso_nivel", ""),
            "trimestre": f"Trimestre {context.get('trimestre_num')}" if is_trimestral else "Anual",
            "periodo": f"Trimestre {context.get('trimestre_num')}" if is_trimestral else "Anual",
            "tutor": context.get("firmantes", {}).get("tutor_curso", ""),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "rows_html": body_rows,
            "logros_rows_html": logros_rows,
            "estadistica_rows_html": estadistica_rows,
            "chart_svg": chart_svg,
            "promedio_general": self._fmt(
                self._average_trimestral(rows) if simplified_trimestral else float(promedio_general or 0)
            ),
            "firma_docente": context.get("firmantes", {}).get("docente", ""),
            "firma_coordinador": context.get("firmantes", {}).get("coordinador_area", ""),
            "firma_rector": context.get("firmantes", {}).get("rector", ""),
            "firma_tutor": context.get("firmantes", {}).get("tutor_curso", ""),
        }
        values.update(context.get("template_data", {}))
        rendered = template
        raw_keys = {"rows_html", "logros_rows_html", "estadistica_rows_html", "chart_svg"}
        pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}|\[\[\s*([a-zA-Z0-9_]+)\s*\]\]")

        def replace_token(match: re.Match[str]) -> str:
            key = match.group(1) or match.group(2) or ""
            value = values.get(key, "")
            return str(value) if key in raw_keys else html.escape(str(value))

        return pattern.sub(replace_token, rendered)

    @staticmethod
    def _average_trimestral(rows: list[dict[str, Any]]) -> float:
        values = []
        for row in rows:
            value = row.get("promedio_trimestral", row.get("promedio_final"))
            if HtmlReportRenderer._is_empty_value(value):
                continue
            try:
                values.append(float(value))
            except Exception:  # noqa: BLE001
                continue
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _build_simplified_trimestral_rows_html(self, rows: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for idx, row in enumerate(rows, start=1):
            promedio = (
                row.get("promedio_trimestral")
                if row.get("promedio_trimestral") is not None
                else row.get("nota_trimestral", row.get("promedio_final"))
            )
            cualitativo = row.get("cualitativo", row.get("cualitativa", ""))
            equivalencia = self._equivalencia_egb_basica_desde_cualitativo(cualitativo)
            parts.append(
                "<tr>"
                f"<td>{idx}</td>"
                f"<td class='nomina'>{html.escape(str(row.get('estudiante', '')))}</td>"
                f"{self._build_numeric_cell(promedio, extra_classes='prom-bold')}"
                f"<td>{html.escape(str(cualitativo or ''))}</td>"
                f"<td class='celda-equivalencia'>{html.escape(str(equivalencia or ''))}</td>"
                "</tr>"
            )
        return "".join(parts)

    @staticmethod
    def _equivalencia_egb_basica_desde_cualitativo(cualitativo: object) -> str:
        key = str(cualitativo or "").strip().upper()
        if key in {"A+", "A-", "B+"}:
            return "Destreza o aprendizaje alcanzado"
        if key in {"B-", "C+", "C-"}:
            return "Destreza o aprendizaje en proceso de desarrollo"
        if key in {"D+", "D-", "E+", "E-"}:
            return "Destreza o aprendizaje iniciado"
        return ""

    def _build_simplified_anual_rows_html(self, rows: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for idx, row in enumerate(rows, start=1):
            parts.append(
                "<tr>"
                f"<td>{idx}</td><td class='nomina'>{html.escape(str(row.get('estudiante', '')))}</td>"
                f"{self._build_numeric_cell(row.get('trimestre_1'))}<td>{html.escape(str(row.get('equivalencia_t1', '')))}</td>"
                f"{self._build_numeric_cell(row.get('trimestre_2'))}<td>{html.escape(str(row.get('equivalencia_t2', row.get('cualitativo_t2', ''))))}</td>"
                f"{self._build_numeric_cell(row.get('trimestre_3'))}<td>{html.escape(str(row.get('equivalencia_t3', row.get('cualitativo_t3', ''))))}</td>"
                f"{self._build_numeric_cell(row.get('promedio'), extra_classes='prom-bold')}"
                f"<td>{html.escape(str(row.get('cualitativa_anual', '')))}</td>"
                f"<td class='celda-equivalencia'>{html.escape(str(row.get('equivalencia', row.get('cualitativo_final', ''))))}</td>"
                "</tr>"
            )
        return "".join(parts)

    def _build_simplified_stats_rows_html(self, rows: list[dict[str, Any]], use_anual: bool = False) -> str:
        stats = self._build_simplified_stats(rows, use_anual=use_anual)
        parts: list[str] = []
        for row in stats["rows"]:
            escala = str(row.get("escala", ""))
            row_class = " class='total'" if escala == "TOTAL ESTUDIANTES" else ""
            parts.append(
                f"<tr{row_class}>"
                f"<td class='c-escala'>{html.escape(escala)}</td>"
                f"<td class='c-cantidad'>{html.escape(str(row.get('numero', 0)))}</td>"
                f"<td class='c-pct'>{html.escape(str(row.get('porcentaje', '0,00%')))}</td>"
                "</tr>"
            )
        return "".join(parts)

    def _build_simplified_trimestral_chart_html(self, rows: list[dict[str, Any]], use_anual: bool = False) -> str:
        stats = self._build_simplified_stats(rows, use_anual=use_anual)
        filtered_rows: list[dict[str, Any]] = []
        for row in stats["rows"]:
            escala = str(row.get("escala", "")).strip()
            if escala == "TOTAL ESTUDIANTES":
                continue
            numero = int(row.get("numero", 0) or 0)
            porcentaje = float(str(row.get("porcentaje", "0")).replace("%", "").replace(",", ".") or 0)
            if numero <= 0 or porcentaje < 1:
                continue
            filtered_rows.append({"escala": escala, "numero": numero, "porcentaje": porcentaje})

        if not filtered_rows:
            return "<div style='font-size:10px;color:#666;'>Sin datos para graficar</div>"

        bar_items: list[str] = []
        for item in filtered_rows:
            bar_height = max(4.0, min(120.0, item["porcentaje"] * 1.3))
            pct_text = f"{item['porcentaje']:.2f}".replace(".", ",") + "%"
            bar_items.append(
                "<div class='bar-item'>"
                f"<div class='bar-pct'>{html.escape(pct_text)}</div>"
                f"<div class='bar' style='height:{bar_height:.1f}px'></div>"
                f"<div class='bar-n'>{item['numero']}</div>"
                f"<div class='bar-label'>{html.escape(item['escala'])}</div>"
                "</div>"
            )
        return "<div class='bar-chart'>" + "".join(bar_items) + "</div>"

    def _build_simplified_stats(self, rows: list[dict[str, Any]], use_anual: bool = False) -> dict[str, Any]:
        categories = ["A+", "A-", "B+", "B-", "C+", "C-", "D+", "D-", "E+", "E-"]
        total = len(rows)
        counts = {k: 0 for k in categories}
        for row in rows:
            source = row.get("cualitativo_final") if use_anual else row.get("cualitativo", row.get("cualitativa", ""))
            value = str(source or "").strip().upper()
            if value in counts:
                counts[value] += 1
        data_rows = []
        for cat in categories:
            pct = (counts[cat] / total * 100) if total else 0
            data_rows.append({"escala": cat, "numero": counts[cat], "porcentaje": f"{pct:.2f}".replace(".", ",") + "%"})
        data_rows.append({"escala": "TOTAL ESTUDIANTES", "numero": total, "porcentaje": "100,00%" if total else "0,00%"})
        return {"rows": data_rows}

    def render_animacion_lectura(self, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        template_path = Path(__file__).resolve().parent.parent / "templates" / "reporte_animacion_lectura.html"
        if not template_path.exists():
            return ""
        template = template_path.read_text(encoding="utf-8")
        rows_html = self._build_animacion_rows_html(rows)
        stats_rows_html = self._build_animacion_stats_rows_html(context.get("stats", {}))
        stats = context.get("stats", {}) if isinstance(context.get("stats"), dict) else {}
        values = {
            "reporte_titulo": context.get("reporte_titulo", ""),
            "docente": context.get("docente", ""),
            "curso": context.get("curso", ""),
            "paralelo": context.get("paralelo", ""),
            "nivel": context.get("nivel", ""),
            "fecha": context.get("fecha", ""),
            "anio_lectivo": context.get("anio_lectivo", ""),
            "trimestre": context.get("trimestre", ""),
            "logo_institucion": context.get("logo_institucion", ""),
            "logo_ministerio": context.get("logo_ministerio", ""),
            "rector": context.get("rector", ""),
            "estudiantes_rows_html": rows_html,
            "stats_rows_html": stats_rows_html,
            "stats_total_n": stats.get("total_n", 0),
            "stats_total_p": stats.get("total_p", "0,00%"),
        }
        raw_keys = {"estudiantes_rows_html", "stats_rows_html"}
        pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}|\[\[\s*([a-zA-Z0-9_]+)\s*\]\]")

        def replace_token(match: re.Match[str]) -> str:
            key = match.group(1) or match.group(2) or ""
            value = values.get(key, "")
            return str(value) if key in raw_keys else html.escape(str(value))

        return pattern.sub(replace_token, template)

    def render_orientacion_vocacional(self, context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        template_path = Path(__file__).resolve().parent.parent / "templates" / "reporte_orientacion_vocacional.html"
        if not template_path.exists():
            return ""
        template = template_path.read_text(encoding="utf-8")
        rows_html = self._build_orientacion_rows_html(rows)
        stats_rows_html = self._build_animacion_stats_rows_html(context.get("stats", {}))
        stats = context.get("stats", {}) if isinstance(context.get("stats"), dict) else {}
        values = {
            "reporte_titulo": context.get("reporte_titulo", ""),
            "docente": context.get("docente", ""),
            "curso": context.get("curso", ""),
            "paralelo": context.get("paralelo", ""),
            "nivel": context.get("nivel", ""),
            "fecha": context.get("fecha", ""),
            "anio_lectivo": context.get("anio_lectivo", ""),
            "trimestre": context.get("trimestre", ""),
            "logo_institucion": context.get("logo_institucion", ""),
            "logo_ministerio": context.get("logo_ministerio", ""),
            "rector": context.get("rector", ""),
            "estudiantes_rows_html": rows_html,
            "stats_rows_html": stats_rows_html,
            "stats_total_n": stats.get("total_n", 0),
            "stats_total_p": stats.get("total_p", "0,00%"),
        }
        raw_keys = {"estudiantes_rows_html", "stats_rows_html"}
        pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}|\[\[\s*([a-zA-Z0-9_]+)\s*\]\]")

        def replace_token(match: re.Match[str]) -> str:
            key = match.group(1) or match.group(2) or ""
            value = values.get(key, "")
            return str(value) if key in raw_keys else html.escape(str(value))

        return pattern.sub(replace_token, template)

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
        defs = [(descripcion, sigla) for sigla, descripcion, _rango in ESCALA_CUALITATIVA_ACADEMICA]
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
    def _build_animacion_rows_html(rows: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for row in rows:
            parts.append(
                "<tr>"
                f"<td>{html.escape(str(row.get('nro', '')))}</td>"
                f"<td class='nomina'>{html.escape(str(row.get('nomina', '')))}</td>"
                f"<td>{html.escape(str(row.get('valor', '')))}</td>"
                f"<td>{html.escape(str(row.get('cualitativo', '')))}</td>"
                f"<td>{html.escape(str(row.get('cualitativo_1', '')))}</td>"
                f"<td class='text-desc'>{html.escape(str(row.get('descripcion', '')))}</td>"
                "</tr>"
            )
        return "".join(parts)

    @staticmethod
    def _build_orientacion_rows_html(rows: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for row in rows:
            parts.append(
                "<tr>"
                f"<td>{html.escape(str(row.get('nro', '')))}</td>"
                f"<td class='nomina'>{html.escape(str(row.get('nomina', '')))}</td>"
                f"<td>{html.escape(str(row.get('cualitativo', '')))}</td>"
                f"<td class='text-desc'>{html.escape(str(row.get('descripcion', '')))}</td>"
                "</tr>"
            )
        return "".join(parts)

    @staticmethod
    def _build_animacion_stats_rows_html(stats: dict[str, Any]) -> str:
        rows = stats.get("rows", []) if isinstance(stats, dict) else []
        parts: list[str] = []
        for row in rows:
            parts.append(
                "<tr>"
                f"<td class='c-escala'>{html.escape(str(row.get('escala', '')))}</td>"
                f"<td class='c-cantidad'>{html.escape(str(row.get('numero', 0)))}</td>"
                f"<td class='c-pct'>{html.escape(str(row.get('porcentaje', '0,00%')))}</td>"
                "</tr>"
            )
        return "".join(parts)

    def _build_trimestral_rows_html(self, rows: list[dict[str, Any]]) -> str:
        html_rows: list[str] = []
        for idx, row in enumerate(rows, start=1):
            promedio_final = self._build_numeric_cell(row.get("promedio_final"), extra_classes="prom-bold")
            observacion_raw = str(row.get("observacion", ""))
            observacion = html.escape(observacion_raw)
            html_rows.append(
                "<tr>"
                f"<td>{idx}</td>"
                f"<td class='nomina'>{html.escape(str(row.get('estudiante', '')))}</td>"
                f"{self._build_numeric_cell(row.get('aportes_calificacion'))}"
                f"{self._build_numeric_cell(row.get('aportes_70'))}"
                f"{self._build_numeric_cell(row.get('sumativas_calificacion'))}"
                f"{self._build_numeric_cell(row.get('sumativas_30'))}"
                f"{promedio_final}"
                f"<td>{html.escape(str(row.get('cualitativa', '')))}</td>"
                f"<td>{html.escape(str(row.get('equivalencia', '')))}</td>"
                f"<td class='{self._observation_class(observacion_raw)}'>{observacion}</td>"
                "</tr>"
            )
        for _ in range(len(rows), 34):
            html_rows.append("<tr><td>&nbsp;</td>" + "<td>&nbsp;</td>" * 9 + "</tr>")
        return "".join(html_rows)

    def _build_anual_rows_html(self, rows: list[dict[str, Any]]) -> str:
        html_rows: list[str] = []
        for idx, row in enumerate(rows, start=1):
            observacion_raw = str(row.get("observacion", ""))
            observacion = html.escape(observacion_raw)
            html_rows.append(
                "<tr>"
                f"<td>{idx}</td>"
                f"<td class='nomina'>{html.escape(str(row.get('estudiante', '')))}</td>"
                f"{self._build_numeric_cell(row.get('trimestre_1'))}<td>{html.escape(str(row.get('equivalencia_t1', '')))}</td>"
                f"{self._build_numeric_cell(row.get('trimestre_2'))}<td>{html.escape(str(row.get('equivalencia_t2', '')))}</td>"
                f"{self._build_numeric_cell(row.get('trimestre_3'))}<td>{html.escape(str(row.get('equivalencia_t3', '')))}</td>"
                f"{self._build_numeric_cell(row.get('promedio'), extra_classes='prom-bold')}"
                f"<td>{html.escape(str(row.get('cualitativa_anual', '')))}</td>"
                f"{self._build_numeric_cell(row.get('supletorio'))}"
                f"{self._build_numeric_cell(row.get('promedio_final'), extra_classes='prom-bold')}"
                f"<td>{html.escape(str(row.get('cualitativo_final', '')))}</td>"
                f"<td class='{self._observation_class(observacion_raw)}'>{observacion}</td>"
                "</tr>"
            )
        for _ in range(len(rows), 34):
            html_rows.append("<tr><td>&nbsp;</td>" + "<td>&nbsp;</td>" * 13 + "</tr>")
        return "".join(html_rows)

    def _build_logros_rows_html(self, rows: list[dict[str, Any]]) -> str:
        scale_map = {sigla: rango for sigla, _descripcion, rango in ESCALA_CUALITATIVA_ACADEMICA}
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

    @staticmethod
    def _build_logo_source(path_value: Any, logo_label: str) -> str:
        path = HtmlReportRenderer._normalize_existing_path(path_value)
        if path is None:
            if path_value:
                print(f"[Reportes] Logo {logo_label} no encontrado o ruta inválida: {path_value}")
            return ""
        try:
            mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:{mime_type};base64,{encoded}"
        except Exception:  # noqa: BLE001
            print(f"[Reportes] No se pudo cargar logo {logo_label}: {path}")
            return ""

    @staticmethod
    def _normalize_existing_path(path_value: Any) -> Path | None:
        raw = str(path_value or "").strip().strip('"').strip("'")
        if not raw:
            return None
        try:
            path = Path(raw).expanduser()
            normalized = path if path.is_absolute() else path.resolve()
            return normalized if normalized.exists() else None
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _build_institucion_subtitulo(context: dict[str, Any]) -> str:
        institucion = context.get("institucion", {})
        subtitulo = str(institucion.get("subtitulo") or "").strip()
        if subtitulo:
            return subtitulo
        parroquia = str(institucion.get("parroquia") or "").strip()
        ciudad = str(institucion.get("ciudad") or "").strip()
        return " - ".join([value for value in [parroquia, ciudad] if value])

    @staticmethod
    def _is_empty_value(value: Any) -> bool:
        if value is None:
            return True
        text = str(value).strip()
        return text in {"", "—", "-", "None", "null"}

    @staticmethod
    def _observation_class(observacion: str) -> str:
        normalized = str(observacion or "").strip().lower()
        if normalized in {"aprobado", "apr", "apb"}:
            return "aprobado"
        return "reprobado"

    def _build_numeric_cell(self, value: Any, extra_classes: str = "") -> str:
        classes = [extra_classes] if extra_classes else []
        if self._is_empty_value(value):
            classes.append("sin-datos")
            class_attr = f" class='{' '.join(classes)}'" if classes else ""
            return f"<td{class_attr}>—</td>"
        class_attr = f" class='{' '.join(classes)}'" if classes else ""
        return f"<td{class_attr}>{html.escape(self._fmt(value))}</td>"

    def _build_estadistica_rows_html(self, rows: list[dict[str, Any]]) -> str:
        aprobados = 0
        reprobados = 0
        for row in rows:
            observacion = str(row.get("observacion", "")).strip().lower()
            if observacion in {"aprobado", "apr", "apb"}:
                aprobados += 1
            elif observacion in {"rep", "reprobado", "spl"}:
                reprobados += 1
            elif not self._is_empty_value(row.get("promedio_final")):
                reprobados += 1
        total = aprobados + reprobados
        if total == 0:
            return (
                "<tr><td>Total aprobados</td><td>—</td><td>0</td><td>0.0%</td></tr>"
                "<tr><td>Total reprobados</td><td>—</td><td>0</td><td>0.0%</td></tr>"
            )
        pct_ap = round((aprobados / total) * 100, 2)
        pct_rep = round((reprobados / total) * 100, 2)
        return (
            f"<tr><td>Total aprobados</td><td>—</td><td>{aprobados}</td><td>{pct_ap}%</td></tr>"
            f"<tr><td>Total reprobados</td><td>—</td><td>{reprobados}</td><td>{pct_rep}%</td></tr>"
        )

    def _build_trimestral_chart_svg(self, rows: list[dict[str, Any]]) -> str:
        entries = self._build_logros(rows)
        data = [
            ("DA", entries[0][2], "#10B981"),
            ("AA", entries[1][2], "#3B82F6"),
            ("PA", entries[2][2], "#F59E0B"),
            ("NA", entries[3][2], "#EF4444"),
        ]
        return self._build_pie_chart_svg(data)

    def _build_anual_chart_svg(self, rows: list[dict[str, Any]]) -> str:
        aprobados = 0
        reprobados = 0
        for row in rows:
            observacion = str(row.get("observacion", "")).strip().lower()
            if observacion in {"aprobado", "apr", "apb"}:
                aprobados += 1
            elif observacion in {"rep", "reprobado", "spl"}:
                reprobados += 1
            elif not self._is_empty_value(row.get("promedio_final")):
                reprobados += 1
        return self._build_pie_chart_svg([("Aprobados", aprobados, "#10B981"), ("Reprobados", reprobados, "#EF4444")])

    def _build_pie_chart_svg(self, data: list[tuple[str, int, str]]) -> str:
        total = sum(value for _, value, _ in data)
        if total <= 0:
            return (
                "<svg width='220' height='220' viewBox='0 0 220 220' xmlns='http://www.w3.org/2000/svg'>"
                "<rect width='220' height='220' fill='#F9FAFB'/>"
                "<text x='110' y='115' text-anchor='middle' fill='#6B7280' font-size='16'>Sin datos</text>"
                "</svg>"
            )

        positive_slices = [(label, value, color) for label, value, color in data if value > 0]
        if len(positive_slices) == 1:
            label, value, color = positive_slices[0]
            return (
                "<svg width='320' height='180' viewBox='0 0 320 180' xmlns='http://www.w3.org/2000/svg'>"
                "<rect width='320' height='180' fill='white'/>"
                f"<circle cx='80' cy='80' r='65' fill='{color}'/>"
                f"<rect x='160' y='20' width='12' height='12' fill='{color}'/>"
                f"<text x='178' y='30' font-size='11' fill='#111827'>{html.escape(label)} ({value})</text>"
                "</svg>"
            )

        cx, cy, radius = 80.0, 80.0, 65.0
        current_angle = -math.pi / 2
        segments: list[str] = []
        legend: list[str] = []
        for idx, (label, value, color) in enumerate(data):
            if value <= 0:
                continue
            angle = (value / total) * (2 * math.pi)
            end_angle = current_angle + angle
            x1 = cx + radius * math.cos(current_angle)
            y1 = cy + radius * math.sin(current_angle)
            x2 = cx + radius * math.cos(end_angle)
            y2 = cy + radius * math.sin(end_angle)
            large_arc = 1 if angle > math.pi else 0
            segments.append(
                f"<path d='M {cx:.2f} {cy:.2f} L {x1:.2f} {y1:.2f} A {radius:.2f} {radius:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f} Z' fill='{color}'/>"
            )
            legend.append(
                f"<rect x='160' y='{20 + idx * 24}' width='12' height='12' fill='{color}'/>"
                f"<text x='178' y='{30 + idx * 24}' font-size='11' fill='#111827'>{html.escape(label)} ({value})</text>"
            )
            current_angle = end_angle
        return (
            "<svg width='320' height='180' viewBox='0 0 320 180' xmlns='http://www.w3.org/2000/svg'>"
            "<rect width='320' height='180' fill='white'/>"
            + "".join(segments)
            + "".join(legend)
            + "</svg>"
        )
