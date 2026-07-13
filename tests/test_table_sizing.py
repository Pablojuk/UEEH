"""Pruebas del ajuste compacto de columnas según texto y DPI."""

from __future__ import annotations

import math
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QFont, QFontMetrics
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QHeaderView, QTableWidget, QTableWidgetItem
except ImportError:  # pragma: no cover
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 no está instalado en el entorno")
class TestTableSizing(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_ajusta_texto_mas_largo_mas_un_centimetro(self) -> None:
        from src.presentation.widgets.table_sizing import centimeters_to_pixels, fit_table_columns_to_text

        table = QTableWidget(2, 3)
        font = QFont("Arial")
        font.setPointSizeF(10.0)
        table.setFont(font)
        table.horizontalHeader().setFont(font)
        table.setHorizontalHeaderLabels(["ID", "Nombre", "Encabezado más largo"])
        table.setItem(0, 0, QTableWidgetItem("ID-001"))
        table.setItem(0, 1, QTableWidgetItem("Texto breve"))
        table.setItem(1, 1, QTableWidgetItem("Texto sintético considerablemente más largo"))
        table.setItem(0, 2, QTableWidgetItem("Corto"))
        table.setColumnHidden(0, True)

        fit_table_columns_to_text(table)

        margin = centimeters_to_pixels(table, 1.0)
        header_metrics = QFontMetrics(table.horizontalHeader().font())
        cell_metrics = QFontMetrics(table.font())
        expected_name_width = max(
            header_metrics.horizontalAdvance("Nombre"),
            cell_metrics.horizontalAdvance("Texto breve"),
            cell_metrics.horizontalAdvance("Texto sintético considerablemente más largo"),
        ) + margin
        expected_header_width = max(
            header_metrics.horizontalAdvance("Encabezado más largo"),
            cell_metrics.horizontalAdvance("Corto"),
        ) + margin

        self.assertTrue(table.isColumnHidden(0))
        self.assertEqual(table.columnWidth(1), expected_name_width)
        self.assertEqual(table.columnWidth(2), expected_header_width)
        self.assertEqual(table.horizontalHeader().sectionResizeMode(1), QHeaderView.Interactive)
        self.assertEqual(table.horizontalHeader().sectionResizeMode(2), QHeaderView.Interactive)
        self.assertEqual(table.horizontalScrollBarPolicy(), Qt.ScrollBarAsNeeded)
        self.assertEqual(table.sizeAdjustPolicy(), QAbstractScrollArea.AdjustIgnored)

    def test_conversion_de_un_centimetro_usa_dpi_logico(self) -> None:
        from src.presentation.widgets.table_sizing import centimeters_to_pixels

        table = QTableWidget(0, 1)
        screen = table.screen() or QApplication.primaryScreen()
        expected = max(1, math.ceil(screen.logicalDotsPerInchX() / 2.54))
        self.assertEqual(centimeters_to_pixels(table, 1.0), expected)
