"""Sidebar lateral de navegación."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QPushButton, QSizePolicy, QVBoxLayout

from src.application.services.institution_service import InstitutionService


class Sidebar(QFrame):
    """Barra lateral con accesos a módulos principales."""

    section_selected = Signal(str)

    def __init__(self, institution_service: InstitutionService, app_signals=None) -> None:
        super().__init__()
        self.setObjectName("Card")
        self.setMinimumWidth(150)
        self.setMaximumWidth(220)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.institution_service = institution_service

        self._buttons: dict[str, QPushButton] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        sections = [
            ("dashboard", "Inicio"),
            ("institution", "Institución"),
            ("teachers", "Docentes"),
            ("catalogs", "Catálogos"),
            ("students", "Estudiantes"),
            ("enrollments", "Matrículas"),
            ("teaching_assignments", "Asignaciones"),
            ("grades", "Notas"),
            ("reports", "Reportes"),
            ("attendance", "Asistencias"),
            ("settings", "Utilidades"),
        ]

        for key, text in sections:
            button = QPushButton(text)
            button.clicked.connect(lambda _=False, section=key: self.section_selected.emit(section))
            layout.addWidget(button)
            self._buttons[key] = button

        layout.addStretch(1)

    def select_default(self) -> None:
        self.section_selected.emit("dashboard")
