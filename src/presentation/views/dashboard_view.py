"""Vista de inicio del sistema."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DashboardView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Inicio")
        title.setObjectName("Title")
        subtitle = QLabel("Resumen general del sistema académico")
        subtitle.setObjectName("Subtitle")
        body = QLabel("Módulo en construcción")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(body)
