"""Vista de acceso por clave maestra."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from src.application.services.setup_service import SetupService


class LoginView(QDialog):
    def __init__(self, setup_service: SetupService) -> None:
        super().__init__()
        self.setup_service = setup_service

        self.setWindowTitle("Acceso al sistema")
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)

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
        self.login_button.clicked.connect(self._on_login)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(form)
        root.addWidget(self.login_button)

    def _on_login(self) -> None:
        password = self.password_input.text().strip()
        if not password:
            QMessageBox.warning(self, "Validación", "Debe ingresar la clave maestra.")
            return

        if self.setup_service.validar_clave_maestra(password):
            self.accept()
            return

        QMessageBox.critical(self, "Acceso denegado", "Clave maestra incorrecta.")
