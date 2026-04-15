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


    def test_resuelve_logo_desde_institucion(self) -> None:
        path = HtmlReportRenderer._resolve_logo_path(
            {"institucion": {"logo_path": "/tmp/inst.png", "logo_ministerio_path": "/tmp/min.png"}},
            "institucional",
        )
        self.assertEqual(path, "/tmp/inst.png")
        min_path = HtmlReportRenderer._resolve_logo_path(
            {"institucion": {"logo_path": "/tmp/inst.png", "logo_ministerio_path": "/tmp/min.png"}},
            "ministerio",
        )
        self.assertEqual(min_path, "/tmp/min.png")


    def test_path_to_file_uri_acepta_file_uri(self) -> None:
        uri = "file:///tmp/logo.png"
        self.assertEqual(HtmlReportRenderer._path_to_file_uri(uri), uri)



if __name__ == "__main__":
    unittest.main()
