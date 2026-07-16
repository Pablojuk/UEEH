"""Pruebas básicas del renderizador HTML institucional."""

from __future__ import annotations

import unittest

from src.infrastructure.exporters.html_report_renderer import HtmlReportRenderer


class TestHtmlReportRenderer(unittest.TestCase):
    def test_leyenda_usa_descripciones_y_limites_de_la_escala_central(self) -> None:
        renderer = HtmlReportRenderer()
        html = renderer._build_logros_rows_html(
            [{"equivalencia": "DA"}, {"equivalencia": "AA"}, {"equivalencia": "PA"}, {"equivalencia": "NA"}]
        )
        self.assertIn("Domina los aprendizajes requeridos", html)
        self.assertIn("Está próximo a alcanzar los aprendizajes requeridos", html)
        self.assertIn("4,01 - 6,99", html)
        self.assertIn("≤ 4,00", html)
        self.assertNotIn("&lt;= 5", html)

    def test_render_anual_incluye_tabla_de_notas(self) -> None:
        renderer = HtmlReportRenderer()
        html = renderer.render(
            {
                "report_type": "anual",
                "institucion_nombre": "UEEH",
                "docente_nombre": "Ana Perez",
                "asignatura_nombre": "Matemática",
                "curso_nombre": "Primero",
                "paralelo_nombre": "A",
                "firmantes": {},
                "institucion": {},
            },
            [
                {
                    "estudiante": "Lopez Maria",
                    "trimestre_1": 9,
                    "equivalencia_t1": "DA",
                    "trimestre_2": 8,
                    "equivalencia_t2": "AA",
                    "trimestre_3": 9,
                    "equivalencia_t3": "DA",
                    "promedio": 8.67,
                    "cualitativa_anual": "DA",
                    "supletorio": None,
                    "promedio_final": 8.67,
                    "cualitativo_final": "A",
                    "observacion": "Aprobado",
                }
            ],
        )
        self.assertIn("Lopez Maria", html)
        self.assertIn("class='nomina'", html)
        self.assertIn("<svg", html)

    def test_reporte_anual_normal_usa_a4_horizontal_y_ancho_flexible(self) -> None:
        renderer = HtmlReportRenderer()
        html = renderer.render(
            {
                "report_type": "anual",
                "institucion_nombre": "UEEH",
                "docente_nombre": "Docente de Prueba",
                "asignatura_nombre": "Matemática",
                "curso_nombre": "Décimo de EGB",
                "paralelo_nombre": "A",
                "firmantes": {},
                "institucion": {},
            },
            [
                {
                    "estudiante": "Apellidos Sintéticos Muy Extensos Nombres de Prueba",
                    "trimestre_1": 9,
                    "trimestre_2": 8,
                    "trimestre_3": 9,
                    "promedio": 8.67,
                    "promedio_final": 8.67,
                    "observacion": "Aprobado",
                }
            ],
        )
        self.assertEqual(html.count("size: A4 landscape"), 1)
        self.assertNotIn("size: A4 portrait", html)
        self.assertNotIn("width: 794px", html)
        self.assertIn("width: min(1120px, 100%);", html)
        self.assertIn("table.principal col.c-nomina  { width: 24%; }", html)
        self.assertIn("table.principal col.c-obs     { width: 11%; }", html)
        self.assertIn("overflow-wrap: anywhere", html)
        self.assertIn("Apellidos Sintéticos Muy Extensos Nombres de Prueba", html)
        self.assertIn("margin-top: 60px;", html)

    def test_reporte_anual_normal_no_agrega_filas_vacias_que_fuercen_otra_pagina(self) -> None:
        html = HtmlReportRenderer()._build_anual_rows_html(
            [{"estudiante": "Estudiante Sintético", "promedio_final": 8, "observacion": "Aprobado"}]
        )
        self.assertEqual(html.count("<tr>"), 1)

    def test_reporte_trimestral_normal_usa_a4_horizontal_y_ancho_util(self) -> None:
        html = HtmlReportRenderer().render(
            {
                "report_type": "trimestral",
                "trimestre_num": 2,
                "institucion_nombre": "UEEH",
                "docente_nombre": "Docente Sintético",
                "asignatura_nombre": "Lengua y Literatura",
                "curso_nombre": "Décimo EGB",
                "paralelo_nombre": "A",
                "firmantes": {},
                "institucion": {},
            },
            [{"estudiante": "Maldonado Villavicencio María Fernanda", "promedio_final": 8.75}],
        )
        self.assertEqual(html.count("size: A4 landscape"), 1)
        self.assertNotIn("size: A4 portrait", html)
        self.assertNotIn("width: 210mm", html)
        self.assertNotIn("width: 794px", html)
        self.assertIn("width: min(1120px, 100%);", html)
        self.assertIn("table.principal col.c-num    { width: 3%; }", html)
        self.assertIn("table.principal col.c-nomina { width: 26%; }", html)
        self.assertIn("table.principal col.c-obs    { width: 12%; }", html)

    def test_reporte_trimestral_normal_no_agrega_filas_vacias(self) -> None:
        html = HtmlReportRenderer()._build_trimestral_rows_html(
            [{"estudiante": "Estudiante Sintético", "promedio_final": 8, "observacion": "Aprobado"}]
        )
        self.assertEqual(html.count("<tr>"), 1)

    def test_reporte_trimestral_simplificado_conserva_a4_vertical_sin_desborde(self) -> None:
        html = HtmlReportRenderer().render(
            {
                "report_type": "trimestral",
                "is_simplified_trimestral": True,
                "institucion_nombre": "UEEH",
                "docente_nombre": "Docente Sintético",
                "asignatura_nombre": "Matemática",
                "curso_nombre": "Segundo de EGB",
                "paralelo_nombre": "A",
                "firmantes": {},
                "institucion": {},
            },
            [{"estudiante": "Maldonado Villavicencio María Fernanda", "promedio_trimestral": 8.75}],
        )
        self.assertEqual(html.count("size: A4 portrait"), 1)
        self.assertNotIn("size: A4 landscape", html)
        self.assertIn("width: min(794px, 100%);", html)
        self.assertIn(".hoja { width: 100%; max-width: none;", html)
        self.assertIn("table.principal col.c-num { width: 5%; }", html)
        self.assertIn("table.principal col.c-equiv { width: 35%; }", html)

    def test_render_anual_simplificado_no_muestra_supletorio(self) -> None:
        renderer = HtmlReportRenderer()
        html = renderer.render(
            {
                "report_type": "anual",
                "is_simplified_anual": True,
                "institucion_nombre": "UEEH",
                "docente_nombre": "Ana Perez",
                "asignatura_nombre": "Matemática",
                "curso_nombre": "3ro de EGB-A",
                "paralelo_nombre": "A",
                "firmantes": {},
                "institucion": {},
            },
            [{"estudiante": "Lopez Maria", "trimestre_1": 8, "equivalencia_t1": "A-", "trimestre_2": 9, "equivalencia_t2": "A+", "trimestre_3": 8, "equivalencia_t3": "A-", "promedio": 8.33, "cualitativa_anual": "A-", "cualitativo_final": "A-", "observacion": "APB"}],
        )
        self.assertNotIn("Supletorio", html)
        self.assertNotIn("Promedio Final", html)
        self.assertIn("Equivalencia", html)
        self.assertEqual(html.count("size: A4 portrait"), 1)
        self.assertIn("width: min(794px, 100%);", html)
        self.assertIn("margin-top: 60px;", html)

    def test_estadistica_anual_trata_spl_como_reprobado(self) -> None:
        renderer = HtmlReportRenderer()
        stats = renderer._build_estadistica_rows_html([
            {"observacion": "APB", "promedio_final": 9},
            {"observacion": "SPL", "promedio_final": 5},
        ])
        self.assertIn("Total aprobados", stats)
        self.assertIn(">1<", stats)
        self.assertIn("Total reprobados", stats)

    def test_grafica_pastel_anual_muestra_100_por_ciento(self) -> None:
        renderer = HtmlReportRenderer()
        svg = renderer._build_anual_chart_svg([
            {"observacion": "APB", "promedio_final": 9},
            {"observacion": "Aprobado", "promedio_final": 8},
        ])
        self.assertIn("<svg", svg)
        self.assertIn("<circle", svg)
        self.assertIn("Aprobados (2)", svg)

    def test_render_animacion_lectura_incluye_tabla_seis_columnas(self) -> None:
        renderer = HtmlReportRenderer()
        html = renderer.render_animacion_lectura(
            {
                "reporte_titulo": "ANIMACIÓN A LA LECTURA - TRIMESTRE 1",
                "docente": "Ana Pérez",
                "curso": "8vo",
                "paralelo": "A",
                "nivel": "Básica Media",
                "fecha": "2026-04-24",
                "anio_lectivo": "2025-2026",
                "trimestre": "TRIMESTRE 1",
                "logo_institucion": "",
                "logo_ministerio": "",
                "rector": "Rector",
                "stats": {
                    "rows": [
                        {"escala": "A", "numero": 1, "porcentaje": "100,00%"},
                        {"escala": "B", "numero": 0, "porcentaje": "0,00%"},
                    ],
                    "total_n": 1,
                    "total_p": "100,00%",
                },
            },
            [
                {
                    "nro": "1",
                    "nomina": "Lopez Maria",
                    "valor": "8.50",
                    "cualitativo": "B+",
                    "cualitativo_1": "B",
                    "descripcion": "Gusto por la lectura en desarrollo intermedio",
                }
            ],
        )
        self.assertIn("<table class=\"principal\">", html)
        self.assertIn("Nómina de Estudiantes", html)
        self.assertGreaterEqual(html.count("<th"), 9)
        self.assertIn("Gusto por la lectura en desarrollo intermedio", html)
        self.assertIn("ESCALA CUALITATIVA", html)
        self.assertIn("TOTAL ESTUDIANTES", html)
        self.assertIn("Frecuencia por Escala Cualitativa", html)
        self.assertIn("id=\"bar-chart\"", html)
        self.assertIn("txtPorcentaje", html)

    def test_render_orientacion_vocacional_tabla_descripcion_y_estadistica(self) -> None:
        renderer = HtmlReportRenderer()
        html = renderer.render_orientacion_vocacional(
            {
                "reporte_titulo": "ORIENTACIÓN VOCACIONAL Y PROFESIONAL - TRIMESTRE 1",
                "docente": "Ana Pérez",
                "curso": "10mo",
                "paralelo": "A",
                "nivel": "Básica Superior",
                "fecha": "2026-04-27",
                "anio_lectivo": "2025-2026",
                "trimestre": "TRIMESTRE 1",
                "logo_institucion": "",
                "logo_ministerio": "",
                "rector": "Rector",
                "stats": {
                    "rows": [
                        {"escala": "A+", "numero": 1, "porcentaje": "50,00%"},
                        {"escala": "A-", "numero": 1, "porcentaje": "50,00%"},
                        {"escala": "B+", "numero": 0, "porcentaje": "0,00%"},
                    ],
                    "total_n": 2,
                    "total_p": "100,00%",
                },
            },
            [
                {"nro": "1", "nomina": "Lopez Maria", "cualitativo": "A+", "descripcion": "Siempre"},
                {"nro": "2", "nomina": "Perez Juan", "cualitativo": "A-", "descripcion": "Frecuentemente"},
            ],
        )
        self.assertIn("ORIENTACIÓN VOCACIONAL Y PROFESIONAL", html)
        self.assertIn("<th>Cualitativo</th>", html)
        self.assertIn("<th>Descripción</th>", html)
        self.assertIn("Siempre", html)
        self.assertIn("Frecuentemente", html)
        self.assertIn("A+", html)
        self.assertIn("A-", html)
        self.assertIn("B+", html)
        self.assertIn("TOTAL ESTUDIANTES", html)
        self.assertIn("@media print", html)
        self.assertIn("@page { size: A4 portrait; margin: 10mm; }", html)


if __name__ == "__main__":
    unittest.main()
