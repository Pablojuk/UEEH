"""Pruebas básicas del renderizador HTML institucional."""

from __future__ import annotations

import unittest

from src.infrastructure.exporters.html_report_renderer import HtmlReportRenderer


class TestHtmlReportRenderer(unittest.TestCase):
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
        self.assertEqual(html.count("<th class="), 6)
        self.assertIn("Gusto por la lectura en desarrollo intermedio", html)
        self.assertIn("ESCALA CUALITATIVA", html)
        self.assertIn("TOTAL ESTUDIANTES", html)


if __name__ == "__main__":
    unittest.main()
