"""Diálogo de actualización automática para UEEH."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.infrastructure.update_checker import ReleaseInfo
from src.presentation.workers.update_worker import DownloadWorker


class UpdateDialog(QDialog):
    """Diálogo que notifica la disponibilidad de una actualización y permite su descarga."""

    def __init__(self, release_info: ReleaseInfo, current_version: str, parent=None) -> None:
        super().__init__(parent)
        self.release_info = release_info
        self.current_version = current_version
        self.download_worker: DownloadWorker | None = None

        self.setWindowTitle("Actualización Disponible")
        self.setMinimumSize(480, 360)
        self.resize(500, 400)

        # Aplicar estilo al diálogo
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #1e293b;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #334155;
            }
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                text-align: center;
                background-color: #e2e8f0;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 3px;
            }
            QPushButton {
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton#btn-descargar {
                background-color: #2563eb;
                color: white;
                border: none;
            }
            QPushButton#btn-descargar:hover {
                background-color: #1d4ed8;
            }
            QPushButton#btn-descargar:disabled {
                background-color: #93c5fd;
            }
            QPushButton#btn-ignorar {
                background-color: #e2e8f0;
                color: #475569;
                border: 1px solid #cbd5e1;
            }
            QPushButton#btn-ignorar:hover {
                background-color: #cbd5e1;
            }
        """)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Encabezado
        header_label = QLabel("¡Una nueva versión del sistema está disponible!")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e3a8a;")
        layout.addWidget(header_label)

        # Información de versiones
        version_layout = QHBoxLayout()
        self.lbl_current = QLabel(f"Versión instalada: <b>{self.current_version}</b>")
        self.lbl_latest = QLabel(f"Versión nueva: <b>{self.release_info.tag_name}</b>")
        self.lbl_current.setStyleSheet("font-size: 12px; color: #64748b;")
        self.lbl_latest.setStyleSheet("font-size: 12px; color: #10b981; font-weight: bold;")
        version_layout.addWidget(self.lbl_current)
        version_layout.addWidget(self.lbl_latest)
        version_layout.addStretch()
        layout.addLayout(version_layout)

        # Novedades / Release notes
        notes_title = QLabel("Novedades de esta versión:")
        notes_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #334155;")
        layout.addWidget(notes_title)

        self.txt_notes = QTextEdit()
        self.txt_notes.setReadOnly(True)
        self.txt_notes.setPlainText(self.release_info.release_notes or "No se incluyeron notas de versión.")
        layout.addWidget(self.txt_notes)

        # Progreso de descarga
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 11px; font-style: italic; color: #475569;")
        self.lbl_status.setVisible(False)
        layout.addWidget(self.lbl_status)

        # Botones de acción
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()

        self.btn_ignorar = QPushButton("Ignorar por ahora")
        self.btn_ignorar.setObjectName("btn-ignorar")
        self.btn_ignorar.clicked.connect(self.reject)

        self.btn_descargar = QPushButton("Descargar actualización")
        self.btn_descargar.setObjectName("btn-descargar")
        self.btn_descargar.clicked.connect(self._start_download)

        self.button_layout.addWidget(self.btn_ignorar)
        self.button_layout.addWidget(self.btn_descargar)
        layout.addLayout(self.button_layout)

    def _start_download(self) -> None:
        if not self.release_info.download_url:
            self.lbl_status.setText(
                f"No hay un instalador directo disponible. Puede descargarla manualmente en:\n{self.release_info.html_url}"
            )
            self.lbl_status.setVisible(True)
            self.lbl_status.setStyleSheet("color: #b91c1c; font-size: 11px;")
            return

        # Deshabilitar botones e iniciar descarga
        self.btn_descargar.setEnabled(False)
        self.btn_ignorar.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setVisible(True)
        self.lbl_status.setText("Iniciando descarga...")

        # Determinar directorio de descargas del usuario de forma segura
        downloads_dir = Path(os.path.expanduser("~")) / "Downloads"
        if not downloads_dir.exists():
            downloads_dir = Path.home()

        # Nombre del archivo basado en la URL
        filename = self.release_info.download_url.split("/")[-1]
        dest_path = downloads_dir / filename

        self.download_worker = DownloadWorker(self.release_info.download_url, dest_path, self.release_info.expected_hash)
        self.download_worker.progress.connect(self._update_progress)
        self.download_worker.finished.connect(self._download_success)
        self.download_worker.error_occurred.connect(self._download_error)
        self.download_worker.start()

    def _update_progress(self, val: int) -> None:
        self.progress_bar.setValue(val)
        self.lbl_status.setText(f"Descargando: {val}% completado...")

    def _download_success(self, file_path: str) -> None:
        self.progress_bar.setValue(100)
        self.lbl_status.setStyleSheet("color: #15803d; font-weight: bold;")
        self.lbl_status.setText(f"Descarga finalizada con éxito.\nGuardado en: {file_path}")

        # Cambiar el botón ignorar por "Cerrar" y remover botón descargar
        self.btn_ignorar.setText("Cerrar")
        self.btn_ignorar.setEnabled(True)
        self.btn_descargar.setVisible(False)

        # Preguntar/avisar al usuario para ejecutar la instalación y cerrar la aplicación
        QMessageBox.information(
            self,
            "Descarga completada",
            "Descarga completada. El sistema se cerrará automáticamente para iniciar la instalación."
        )

        try:
            if hasattr(os, "startfile"):
                os.startfile(file_path)
            else:
                import subprocess
                if sys.platform == "win32":
                    subprocess.Popen([file_path], shell=True)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", file_path])
                else:
                    subprocess.Popen(["xdg-open", file_path])
            
            # Cerrar la aplicación de forma segura para evitar bloquear archivos al instalar
            QApplication.quit()
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Error al ejecutar instalador",
                f"No se pudo iniciar el instalador automáticamente.\n"
                f"Puede ejecutarlo manualmente desde:\n{file_path}\n\nDetalle: {exc}"
            )

    def _download_error(self, err_msg: str) -> None:
        self.progress_bar.setVisible(False)
        self.lbl_status.setStyleSheet("color: #b91c1c;")
        self.lbl_status.setText(f"Ocurrió un error al descargar: {err_msg}")
        self.btn_descargar.setEnabled(True)
        self.btn_ignorar.setEnabled(True)
