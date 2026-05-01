"""Pruebas de comportamiento para Animación a la Lectura."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None
    Qt = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestAnimacionLecturaView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_scroll_horizontal_visible_en_tabla_central(self) -> None:
        from src.presentation.views.animacion_lectura_view import AnimacionLecturaView

        view = AnimacionLecturaView()
        view.level_combo.setCurrentIndex(view.level_combo.findData("superior"))
        view.set_students([{"estudiante_id": "E1", "estudiante": "López María"}], selected_level="superior")

        self.assertEqual(view.center_table.horizontalScrollBarPolicy(), Qt.ScrollBarAlwaysOn)
        self.assertGreater(view.center_table.columnCount(), 0)

    def test_nombre_pdf_se_genera_desde_combo_asignacion(self) -> None:
        from src.presentation.views.animacion_lectura_view import AnimacionLecturaView

        view = AnimacionLecturaView()
        view.report_assignment_combo.clear()
        view.report_assignment_combo.addItem("Animación a la Lectura | 1ro BGU-A | Docente | 2026-2027", "AS1")
        base = view._build_export_filename_base()
        self.assertIn("Animación_a_la_Lectura", base)
        self.assertNotIn("|", base)

    def test_cambio_firmantes_refresca_vista_previa_en_reportes(self) -> None:
        from src.presentation.views.animacion_lectura_view import AnimacionLecturaView

        view = AnimacionLecturaView()
        view.set_reports_mode(True)
        calls = {"count": 0}
        view._refresh_preview_if_reports_mode = lambda: calls.__setitem__("count", calls["count"] + 1)
        view.sign_docente_combo.addItem("Docente 1", "Docente 1")
        view.sign_docente_combo.setCurrentIndex(view.sign_docente_combo.count() - 1)
        self.assertGreaterEqual(calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
