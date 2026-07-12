"""Ajuste compacto de columnas según texto y DPI de pantalla."""

from __future__ import annotations

import math

from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QApplication, QHeaderView, QTableWidget


CENTIMETERS_PER_INCH = 2.54
FALLBACK_DPI = 96.0


def centimeters_to_pixels(table: QTableWidget, centimeters: float) -> int:
    """Convierte centímetros a píxeles usando el DPI lógico de la pantalla."""
    screen = table.screen() or QApplication.primaryScreen()
    dpi = float(screen.logicalDotsPerInchX()) if screen is not None else FALLBACK_DPI
    if dpi <= 0:
        dpi = FALLBACK_DPI
    return max(1, math.ceil((dpi * centimeters) / CENTIMETERS_PER_INCH))


def fit_table_columns_to_text(table: QTableWidget, right_margin_cm: float = 1.0) -> None:
    """Ajusta cada columna visible al texto más largo más un margen derecho."""
    header = table.horizontalHeader()
    header.setStretchLastSection(False)
    right_margin = centimeters_to_pixels(table, right_margin_cm)
    header_metrics = QFontMetrics(header.font())
    cell_metrics = QFontMetrics(table.font())

    for column in range(table.columnCount()):
        if table.isColumnHidden(column):
            continue

        header_item = table.horizontalHeaderItem(column)
        longest_width = header_metrics.horizontalAdvance(header_item.text()) if header_item is not None else 0

        for row in range(table.rowCount()):
            item = table.item(row, column)
            if item is not None:
                longest_width = max(longest_width, cell_metrics.horizontalAdvance(item.text()))

        header.setSectionResizeMode(column, QHeaderView.Interactive)
        header.resizeSection(column, longest_width + right_margin)
