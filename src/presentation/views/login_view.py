"""Vista de acceso por clave maestra con recuperación por correo electrónico."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.application.services.setup_service import SetupService
from src.presentation.workers.email_worker import EmailSendWorker


class LoginView(QDialog):
    def __init__(self, setup_service: SetupService) -> None:
        super().__init__()
        self.setup_service = setup_service
        self.email_worker: EmailSendWorker | None = None

        self.setWindowTitle("Acceso al sistema")
        self.setMinimumWidth(420)

        # Aplicar estilo unificado
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QLabel#Title {
                font-size: 20px;
                font-weight: bold;
                color: #1e3a8a;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#Subtitle {
                font-size: 12px;
                color: #64748b;
                margin-bottom: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #334155;
            }
            QPushButton#btn-entrar {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QPushButton#btn-entrar:hover {
                background-color: #1d4ed8;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(10)

        title = QLabel("Ingresar")
        title.setObjectName("Title")
        subtitle = QLabel("Ingrese la clave maestra para continuar")
        subtitle.setObjectName("Subtitle")

        form = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._on_login)
        form.addRow("Clave maestra", self.password_input)

        self.login_button = QPushButton("Entrar")
        self.login_button.setObjectName("btn-entrar")
        self.login_button.clicked.connect(self._on_login)

        # Enlace de recuperación
        self.recover_link = QLabel("<a href='#'>¿Olvidó su clave maestra?</a>")
        self.recover_link.setTextFormat(Qt.RichText)
        self.recover_link.setAlignment(Qt.AlignCenter)
        self.recover_link.linkActivated.connect(self._recover_password)
        self.recover_link.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                margin-top: 10px;
            }
            QLabel a {
                color: #2563eb;
                text-decoration: underline;
                font-weight: bold;
            }
        """)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(form)
        root.addWidget(self.login_button)
        root.addWidget(self.recover_link)

    def _on_login(self) -> None:
        password = self.password_input.text().strip()
        if not password:
            QMessageBox.warning(self, "Validación", "Debe ingresar la clave maestra.")
            return

        if self.setup_service.validar_clave_maestra(password):
            self.accept()
            return

        QMessageBox.critical(self, "Acceso denegado", "Clave maestra incorrecta.")

    def _recover_password(self) -> None:
        email = self.setup_service.get_recovery_email()
        if not email:
            QMessageBox.warning(
                self,
                "Recuperación de Clave",
                "No se ha registrado ningún correo de recuperación en el sistema.\n"
                "Comuníquese con soporte o configure uno desde el menú de Ajustes."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar recuperación",
            f"Se enviará un correo con una nueva clave maestra temporal a la dirección registrada:\n"
            f"--> {email}\n\n¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        # Generar clave temporal
        ok, nueva_clave = self.setup_service.recover_master_key()
        if not ok:
            QMessageBox.critical(self, "Error", f"No se pudo resetear la clave: {nueva_clave}")
            return

        # Deshabilitar UI temporalmente y cambiar cursor
        self.login_button.setEnabled(False)
        self.password_input.setEnabled(False)
        self.recover_link.setEnabled(False)
        self.setCursor(Qt.WaitCursor)

        # Iniciar worker asíncrono
        self.email_worker = EmailSendWorker(email, nueva_clave)
        self.email_worker.success.connect(self._on_email_success)
        self.email_worker.failure.connect(self._on_email_failure)
        self.email_worker.start()

    def _on_email_success(self, msg: str) -> None:
        self._restore_ui()
        QMessageBox.information(self, "Recuperación de Clave", msg)

    def _on_email_failure(self, err_msg: str) -> None:
        self._restore_ui()
        QMessageBox.warning(
            self,
            "Error de Envío",
            f"No se pudo enviar el correo de recuperación.\n"
            f"Detalle: {err_msg}\n\n"
            f"Por favor, verifique su conexión a internet e intente de nuevo."
        )

    def _restore_ui(self) -> None:
        self.login_button.setEnabled(True)
        self.password_input.setEnabled(True)
        self.recover_link.setEnabled(True)
        self.unsetCursor()

