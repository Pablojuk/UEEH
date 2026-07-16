"""Diálogo de activación de licencia y versión de prueba para UEEH."""

from __future__ import annotations

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.application.services.setup_service import SetupService


class LicenseDialog(QDialog):
    """Ventana de validación de Licencia Permanente vs Período de Prueba de 30 días."""

    def __init__(self, setup_service: SetupService, parent=None) -> None:
        super().__init__(parent)
        self.setup_service = setup_service
        self.trial_days = self.setup_service.get_trial_days_remaining()
        self.is_expired = self.trial_days <= 0

        self.setWindowTitle("Activación de Licencia UEEH")
        self.setMinimumSize(450, 300)
        self.resize(480, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Estilo premium consistente con la aplicación
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #1e293b;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #334155;
            }
            QLineEdit:focus {
                border: 2px solid #2563eb;
            }
            QPushButton {
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QPushButton#btn-activar {
                background-color: #2563eb;
                color: white;
                border: none;
            }
            QPushButton#btn-activar:hover {
                background-color: #1d4ed8;
            }
            QPushButton#btn-prueba {
                background-color: #e2e8f0;
                color: #475569;
                border: 1px solid #cbd5e1;
            }
            QPushButton#btn-prueba:hover {
                background-color: #cbd5e1;
            }
            QPushButton#btn-salir {
                background-color: #f1f5f9;
                color: #ef4444;
                border: 1px solid #fecaca;
            }
            QPushButton#btn-salir:hover {
                background-color: #fee2e2;
            }
        """)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Encabezado
        self.lbl_title = QLabel("Activación del Sistema Académico UEEH")
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e3a8a;")
        layout.addWidget(self.lbl_title)

        # Estado del período de prueba
        self.lbl_status = QLabel()
        self.lbl_status.setWordWrap(True)
        if self.is_expired:
            self.lbl_status.setText(
                "❌ <b>Su período de prueba de 30 días ha finalizado.</b><br>"
                "Por favor, ingrese su Licencia Permanente para continuar utilizando el sistema."
            )
            self.lbl_status.setStyleSheet("color: #b91c1c; font-size: 13px;")
        else:
            self.lbl_status.setText(
                f"ℹ️ El sistema se encuentra en modo de prueba. "
                f"Le restan <b>{self.trial_days} días</b> de evaluación pública."
            )
            self.lbl_status.setStyleSheet("color: #2563eb; font-size: 13px;")
        layout.addWidget(self.lbl_status)

        # Entrada de Clave de Licencia
        input_label = QLabel("Clave de Licencia Permanente:")
        input_label.setStyleSheet("font-weight: bold; color: #475569; font-size: 12px;")
        layout.addWidget(input_label)

        self.txt_license = QLineEdit()
        self.txt_license.setPlaceholderText("Pegue su código de licencia en Base64 aquí...")
        layout.addWidget(self.txt_license)

        # Botones de Acción
        self.button_layout = QHBoxLayout()
        
        self.btn_salir = QPushButton("Salir")
        self.btn_salir.setObjectName("btn-salir")
        self.btn_salir.clicked.connect(self.close_app)
        self.button_layout.addWidget(self.btn_salir)
        
        self.button_layout.addStretch()

        if not self.is_expired:
            self.btn_prueba = QPushButton("Continuar Evaluación")
            self.btn_prueba.setObjectName("btn-prueba")
            self.btn_prueba.clicked.connect(self.continue_trial)
            self.button_layout.addWidget(self.btn_prueba)

        self.btn_activar = QPushButton("Activar Licencia")
        self.btn_activar.setObjectName("btn-activar")
        self.btn_activar.clicked.connect(self.activate_license)
        self.button_layout.addWidget(self.btn_activar)

        layout.addLayout(self.button_layout)

    def activate_license(self) -> None:
        key = self.txt_license.text()
        if not key.strip():
            QMessageBox.warning(self, "Entrada inválida", "Por favor, introduzca una clave de licencia.")
            return

        success = self.setup_service.activate_license(key)
        if success:
            QMessageBox.information(
                self,
                "Activación Exitosa",
                "¡El sistema ha sido activado permanentemente con éxito!\nMuchas gracias por su confianza."
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Licencia Inválida",
                "El código de licencia ingresado es incorrecto o está corrupto.\n"
                "Por favor, verifique el código e intente de nuevo."
            )

    def continue_trial(self) -> None:
        self.accept()

    def close_app(self) -> None:
        self.reject()
        sys.exit(0)

    def reject(self) -> None:
        # Asegurar que cerrar el diálogo con la 'X' superior también aborte la app si no hay licencia
        super().reject()
        if self.is_expired:
            sys.exit(0)
