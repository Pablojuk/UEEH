"""Bus de señales global para refresco entre vistas."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):
    """Señales de alto nivel para sincronizar cambios de datos."""

    data_changed = Signal(str)
