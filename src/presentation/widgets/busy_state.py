"""Utilidades visuales simples para acciones de botones potencialmente lentas."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton


@contextmanager
def busy_button(button: QPushButton | None, busy_text: str | None = None) -> Iterator[None]:
    """Muestra cursor de espera y deshabilita temporalmente un botón."""
    app = QApplication.instance()
    original_text = button.text() if button is not None else ""
    cursor_overridden = False
    try:
        if app is not None:
            app.setOverrideCursor(Qt.WaitCursor)
            cursor_overridden = True
        if button is not None:
            button.setEnabled(False)
            if busy_text:
                button.setText(busy_text)
        if app is not None:
            app.processEvents()
        yield
    finally:
        try:
            if button is not None:
                button.setText(original_text)
                button.setEnabled(True)
        finally:
            if app is not None and cursor_overridden:
                app.restoreOverrideCursor()
                app.processEvents()
