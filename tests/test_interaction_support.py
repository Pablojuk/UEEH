"""Pruebas de selección, copiado y menús contextuales globales."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QEvent, QItemSelectionModel, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QTableWidget, QTableWidgetItem
except ImportError:  # pragma: no cover
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestInteractionSupport(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        from src.presentation.widgets.interaction_support import install_global_interaction_support

        cls.support = install_global_interaction_support(cls.app)

    @staticmethod
    def _table() -> QTableWidget:
        table = QTableWidget(2, 3)
        table.setHorizontalHeaderLabels(["ID", "Nombre", "Estado"])
        table.setColumnHidden(0, True)
        table.setItem(0, 0, QTableWidgetItem("ID-OCULTO"))
        table.setItem(0, 1, QTableWidgetItem("Ana"))
        combo = QComboBox()
        combo.addItems(["Activo", "Inactivo"])
        combo.setCurrentText("Inactivo")
        table.setCellWidget(0, 2, combo)
        table.setItem(1, 1, QTableWidgetItem("Luis"))
        table.setItem(1, 2, QTableWidgetItem("Activo"))
        for row in range(2):
            for column in (1, 2):
                table.selectionModel().select(table.model().index(row, column), QItemSelectionModel.Select)
        return table

    def test_copia_tsv_visible_e_incluye_widget_de_celda(self) -> None:
        from src.presentation.widgets.interaction_support import copy_table_selection

        table = self._table()
        copied = copy_table_selection(table)
        self.assertEqual(copied, "Ana\tInactivo\nLuis\tActivo")
        self.assertEqual(self.app.clipboard().text(), copied)
        self.assertNotIn("ID-OCULTO", copied)

    def test_ctrl_a_y_ctrl_c_operan_sobre_tabla(self) -> None:
        table = self._table()
        table.clearSelection()
        QApplication.sendEvent(table, QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.ControlModifier))
        self.assertEqual(len(table.selectedIndexes()), 4)
        QApplication.sendEvent(table, QKeyEvent(QEvent.KeyPress, Qt.Key_C, Qt.ControlModifier))
        self.assertEqual(self.app.clipboard().text(), "Ana\tInactivo\nLuis\tActivo")

    def test_menus_en_espanol_y_campo_solo_lectura_protegido(self) -> None:
        from src.presentation.widgets.interaction_support import build_edit_context_menu, build_table_context_menu

        table_actions = [a.text() for a in build_table_context_menu(self._table()).actions()]
        self.assertEqual(table_actions, ["Copiar", "Seleccionar todo"])
        field = QLineEdit("Dato")
        field.selectAll()
        field.setReadOnly(True)
        actions = {a.text(): a for a in build_edit_context_menu(field).actions() if a.text()}
        self.assertEqual(
            list(actions),
            ["Deshacer", "Rehacer", "Cortar", "Copiar", "Pegar", "Eliminar", "Seleccionar todo"],
        )
        self.assertTrue(actions["Copiar"].isEnabled())
        for name in ("Cortar", "Pegar", "Eliminar"):
            self.assertFalse(actions[name].isEnabled())

    def test_etiqueta_informativa_se_puede_copiar(self) -> None:
        from src.presentation.widgets.interaction_support import build_label_context_menu, enable_copyable_label

        label = QLabel("Información sintética")
        enable_copyable_label(label)
        self.assertTrue(label.property("copyableText"))
        menu = build_label_context_menu(label)
        self.assertEqual([a.text() for a in menu.actions()], ["Copiar", "Seleccionar todo"])
        menu.actions()[0].trigger()
        self.assertEqual(self.app.clipboard().text(), "Información sintética")
