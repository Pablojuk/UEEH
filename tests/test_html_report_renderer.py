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
