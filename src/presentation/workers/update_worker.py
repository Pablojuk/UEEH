"""Workers asíncronos para comprobar y descargar actualizaciones en segundo plano."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import QThread, Signal

from src.infrastructure.update_checker import ReleaseInfo, UpdateChecker


class UpdateCheckWorker(QThread):
    """Worker para comprobar actualizaciones sin bloquear el hilo principal."""

    update_available = Signal(ReleaseInfo)
    no_update = Signal()
    error_occurred = Signal(str)

    def __init__(self, current_version: str, parent=None) -> None:
        super().__init__(parent)
        self.current_version = current_version
        self.checker = UpdateChecker()

    def run(self) -> None:
        try:
            info = self.checker.check_latest()
            if info is None:
                self.error_occurred.emit("No se pudo comprobar la actualización (error de red o API).")
                return

            if self.checker.is_update_available(self.current_version, info.tag_name):
                self.update_available.emit(info)
            else:
                self.no_update.emit()
        except Exception as e:
            self.error_occurred.emit(f"Error al verificar actualización: {str(e)}")


class DownloadWorker(QThread):
    """Worker para descargar el ejecutable de actualización en segundo plano."""

    progress = Signal(int)
    finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, url: str, dest_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.url = url
        self.dest_path = dest_path
        self.checker = UpdateChecker()

    def run(self) -> None:
        try:
            self.checker.download_asset(
                url=self.url,
                dest_path=self.dest_path,
                progress_callback=self._emit_progress
            )
            self.finished.emit(str(self.dest_path))
        except Exception as e:
            self.error_occurred.emit(f"Error al descargar la actualización: {str(e)}")

    def _emit_progress(self, percentage: int) -> None:
        self.progress.emit(percentage)
