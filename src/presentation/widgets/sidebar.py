"""Sidebar lateral de navegación."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from src.application.services.institution_service import InstitutionService
from src.presentation.app_signals import AppSignals


class Sidebar(QFrame):
    """Barra lateral con accesos a módulos principales."""

    section_selected = Signal(str)

    def __init__(self, institution_service: InstitutionService, app_signals: AppSignals | None = None) -> None:
        super().__init__()
        self.setObjectName("Card")
        self.setFixedWidth(220)
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
            ("settings", "Utilidades"),
        ]

        for key, text in sections:
            button = QPushButton(text)
            button.clicked.connect(lambda _=False, section=key: self.section_selected.emit(section))
            layout.addWidget(button)
            self._buttons[key] = button

        layout.addStretch(1)

        layout.addWidget(QLabel("Logo de: Ministerio de Educación, Deporte y Cultura"))
        self.logo_ministerio_label = QLabel("Logo ministerial")
        self.logo_ministerio_label.setAlignment(Qt.AlignCenter)
        self.logo_ministerio_label.setFixedHeight(90)
        self.logo_ministerio_label.setStyleSheet("border: 1px dashed #cbd5e1; color: #94a3b8; border-radius: 8px;")
        layout.addWidget(self.logo_ministerio_label)

        layout.addWidget(QLabel("Logo Institucional"))
        self.logo_label = QLabel("Logo institucional")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedHeight(90)
        self.logo_label.setStyleSheet("border: 1px dashed #cbd5e1; color: #94a3b8; border-radius: 8px;")
        layout.addWidget(self.logo_label)

        self.refresh_logo()
        if app_signals:
            app_signals.data_changed.connect(self._on_data_changed)

    def _on_data_changed(self, scope: str) -> None:
        if scope in {"institution", "all"}:
            self.refresh_logo()

    def refresh_logo(self) -> None:
        institution = self.institution_service.obtener_actual() or {}
        self._apply_logo(self.logo_ministerio_label, institution.get("logo_ministerio_path"), "Logo ministerial")
        self._apply_logo(self.logo_label, institution.get("logo_path"), "Logo institucional")

    @staticmethod
    def _apply_logo(label: QLabel, logo_path: str | None, placeholder: str) -> None:
        if logo_path and Path(logo_path).exists():
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                label.setPixmap(pixmap.scaled(180, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                label.setStyleSheet("border: none;")
                return
        label.setPixmap(QPixmap())
        label.setText(placeholder)
        label.setStyleSheet("border: 1px dashed #cbd5e1; color: #94a3b8; border-radius: 8px;")

    def select_default(self) -> None:
        self.section_selected.emit("dashboard")
