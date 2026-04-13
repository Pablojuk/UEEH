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


if __name__ == "__main__":
    unittest.main()
