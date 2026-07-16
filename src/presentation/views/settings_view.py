"""Vista de utilidades del sistema: respaldo y restauración."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.application.services.backup_service import BackupService
from src.version import __version__
from src.presentation.workers.update_worker import UpdateCheckWorker
from src.presentation.widgets.update_dialog import UpdateDialog


class SettingsView(QWidget):
    def __init__(self, backup_service: BackupService, app_version: str = __version__) -> None:
        super().__init__()
        self.backup_service = backup_service
        self.selected_backup_dir = ""
        self.update_worker: UpdateCheckWorker | None = None

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
        self.backup_dir_label = QLabel("No seleccionada")
        self.backup_dir_label.setWordWrap(True)

        self.select_folder_button = QPushButton("Seleccionar carpeta")
        self.select_folder_button.clicked.connect(self.select_backup_folder)
        self.backup_button = QPushButton("Crear respaldo")
        self.backup_button.clicked.connect(self.create_backup)
        self.restore_button = QPushButton("Restaurar respaldo")
        self.restore_button.clicked.connect(self.restore_backup)
        self.check_updates_button = QPushButton("Buscar actualizaciones")
        self.check_updates_button.clicked.connect(self.check_for_updates_manual)

        actions_row = QHBoxLayout()
        actions_row.addWidget(self.select_folder_button)
        actions_row.addWidget(self.backup_button)
        actions_row.addWidget(self.restore_button)
        actions_row.addWidget(self.check_updates_button)

        form.addRow("Versión", self.version_label)
        form.addRow("Ruta DB", self.db_path_label)
        form.addRow("Carpeta respaldo", self.backup_dir_label)
        form.addRow(actions_row)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(card)
        root.addStretch(1)

    def select_backup_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de respaldo")
        if not directory:
            return
        ok, message = self.backup_service.validar_directorio_respaldo(directory)
        if not ok:
            QMessageBox.warning(self, "Ruta inválida", message)
            return
        self.selected_backup_dir = directory
        self.backup_dir_label.setText(directory)

    def create_backup(self) -> None:
        if self.selected_backup_dir:
            ok, message = self.backup_service.crear_respaldo_en_directorio(self.selected_backup_dir)
        else:
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

    def check_for_updates_manual(self) -> None:
        self.check_updates_button.setEnabled(False)
        self.check_updates_button.setText("Buscando...")

        self.update_worker = UpdateCheckWorker(self.version_label.text())
        self.update_worker.update_available.connect(self._on_update_available_manual)
        self.update_worker.no_update.connect(self._on_no_update_manual)
        self.update_worker.error_occurred.connect(self._on_update_error_manual)
        self.update_worker.start()

    def _on_update_available_manual(self, release_info) -> None:
        self.check_updates_button.setEnabled(True)
        self.check_updates_button.setText("Buscar actualizaciones")
        dialog = UpdateDialog(release_info, self.version_label.text(), self)
        dialog.exec()

    def _on_no_update_manual(self) -> None:
        self.check_updates_button.setEnabled(True)
        self.check_updates_button.setText("Buscar actualizaciones")
        QMessageBox.information(self, "Actualización", "El sistema ya se encuentra actualizado a la última versión.")

    def _on_update_error_manual(self, error_msg: str) -> None:
        self.check_updates_button.setEnabled(True)
        self.check_updates_button.setText("Buscar actualizaciones")
        QMessageBox.warning(self, "Error", f"No se pudo comprobar la actualización:\n{error_msg}")
