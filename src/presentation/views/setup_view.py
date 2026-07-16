"""Vista de configuración inicial del sistema."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from src.application.services.institution_service import InstitutionService
from src.application.services.setup_service import SetupService


class SetupView(QDialog):
    def __init__(self, setup_service: SetupService, institution_service: InstitutionService) -> None:
        super().__init__()
        self.setup_service = setup_service
        self.institution_service = institution_service

        self.setWindowTitle("Configuración inicial")
        self.setMinimumWidth(460)

        root = QVBoxLayout(self)

        title = QLabel("Primer uso")
        title.setObjectName("Title")
        subtitle = QLabel("Configure los datos básicos de la institución")
        subtitle.setObjectName("Subtitle")

        form = QFormLayout()

        self.institution_input = QLineEdit()

        form.addRow("Institución", self.institution_input)

        self.save_button = QPushButton("Guardar configuración")
        self.save_button.clicked.connect(self._on_save)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(form)
        root.addWidget(self.save_button)

    def _on_save(self) -> None:
        institution_name = self.institution_input.text().strip()

        if not institution_name:
            QMessageBox.warning(self, "Validación", "El nombre de la institución es obligatorio.")
            return

        result = self.setup_service.configurar_sistema_inicial()
        if not result["creado"]:
            QMessageBox.information(self, "Información", result["mensaje"])
            self.reject()
            return

        self.institution_service.crear_o_actualizar(nombre=institution_name, jornada="Por definir")
        QMessageBox.information(self, "Éxito", "Configuración inicial guardada correctamente.")
        self.accept()
