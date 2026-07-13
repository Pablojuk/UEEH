"""Pruebas de comportamiento para Animación a la Lectura."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QEvent, QItemSelectionModel, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QAbstractItemView, QApplication
except ImportError:  # pragma: no cover
    QApplication = None
    Qt = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestAnimacionLecturaView(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        from src.presentation.widgets.interaction_support import install_global_interaction_support

        install_global_interaction_support(cls.app)

    def test_tabla_permite_seleccion_multiple_y_copia_tsv(self) -> None:
        from src.presentation.views.animacion_lectura_view import AnimacionLecturaView
        from src.presentation.widgets.interaction_support import build_table_context_menu

        view = AnimacionLecturaView()
        view.level_combo.setCurrentIndex(view.level_combo.findData("superior"))
        view.set_students([{"estudiante_id": "E1", "estudiante": "López María"}], selected_level="superior")
        table = view.matrix_table
        row = 3
        indicator_col = view._indicator_start_col
        table.item(row, indicator_col).setText("8.50")
        table.setColumnHidden(0, True)
        for column in (0, 1, indicator_col):
            table.selectionModel().select(table.model().index(row, column), QItemSelectionModel.Select)

        self.assertEqual(table.selectionMode(), QAbstractItemView.ExtendedSelection)
        self.assertTrue(table.item(0, 1).flags() & Qt.ItemIsSelectable)
        self.assertTrue(table.item(row, indicator_col).flags() & Qt.ItemIsSelectable)
        QApplication.sendEvent(table, QKeyEvent(QEvent.KeyPress, Qt.Key_C, Qt.ControlModifier))
        self.assertEqual(self.app.clipboard().text(), "López María\t8.50")
        self.assertNotIn("1\t", self.app.clipboard().text())
        self.assertEqual(
            [action.text() for action in build_table_context_menu(table).actions()],
            ["Copiar", "Seleccionar todo"],
        )

        table.clearSelection()
        QApplication.sendEvent(table, QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.ControlModifier))
        self.assertGreater(len(table.selectedIndexes()), 2)

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
