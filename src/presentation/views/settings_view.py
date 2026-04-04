"""Vista de utilidades del sistema: respaldo y restauración."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.application.services.backup_service import BackupService


class SettingsView(QWidget):
    def __init__(self, backup_service: BackupService, app_version: str = "1.0.0") -> None:
        super().__init__()
        self.backup_service = backup_service

        root = QVBoxLayout(self)

        title = QLabel("Utilidades del Sistema")
        title.setObjectName("Title")
        subtitle = QLabel("Respaldo y restauración de base de datos")
        subtitle.setObjectName("Subtitle")

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)

        self.version_label = QLabel(app_version)
        self.db_path_label = QLabel(self.backup_service.obtener_ruta_db_actual())
        self.db_path_label.setWordWrap(True)

        self.backup_button = QPushButton("Crear respaldo")
        self.backup_button.clicked.connect(self.create_backup)
        self.restore_button = QPushButton("Restaurar respaldo")
        self.restore_button.clicked.connect(self.restore_backup)

        form.addRow("Versión", self.version_label)
        form.addRow("Ruta DB", self.db_path_label)
        form.addRow(self.backup_button)
        form.addRow(self.restore_button)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(card)
        root.addStretch(1)

    def create_backup(self) -> None:
        default_name = self.backup_service.nombre_respaldo_sugerido()
        selected_path, _ = QFileDialog.getSaveFileName(self, "Guardar respaldo", default_name, "SQLite DB (*.db)")
        if not selected_path:
            return

        ok, message = self.backup_service.crear_respaldo(selected_path)
        if ok:
            QMessageBox.information(self, "Éxito", message)
        else:
            QMessageBox.warning(self, "Error", message)

    def restore_backup(self) -> None:
        selected_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar respaldo", "", "SQLite DB (*.db)")
        if not selected_path:
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar restauración",
            "Esta acción reemplazará la base actual. ¿Desea continuar?",
        )
        if confirm != QMessageBox.Yes:
            return

        ok, message = self.backup_service.restaurar_desde_respaldo(selected_path)
        if ok:
            QMessageBox.information(self, "Éxito", message)
        else:
            QMessageBox.warning(self, "Error", message)
