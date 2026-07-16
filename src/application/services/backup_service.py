"""Servicio de respaldo y restauración de base SQLite."""

from __future__ import annotations

import gc
import os
import sqlite3
from datetime import datetime
from pathlib import Path


class BackupService:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path).expanduser().resolve()

    def obtener_ruta_db_actual(self) -> str:
        return str(self.db_path)

    def nombre_respaldo_sugerido(self) -> str:
        return f"respaldo_sistema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    def crear_respaldo(self, destination_path: str) -> tuple[bool, str]:
        source_conn: sqlite3.Connection | None = None
        backup_conn: sqlite3.Connection | None = None
        try:
            destination = self._resolve_destination(destination_path)
            destination.parent.mkdir(parents=True, exist_ok=True)

            source_conn = sqlite3.connect(str(self.db_path))
            backup_conn = sqlite3.connect(str(destination))
            source_conn.backup(backup_conn)

            return True, f"Respaldo creado: {destination}"
        except Exception as exc:
            return False, f"Error al crear respaldo: {exc}"
        finally:
            if backup_conn is not None:
                backup_conn.close()
            if source_conn is not None:
                source_conn.close()
            gc.collect()

    def validar_directorio_respaldo(self, directory_path: str) -> tuple[bool, str]:
        directory = Path(directory_path).expanduser().resolve()
        if not directory.exists() or not directory.is_dir():
            return False, "La carpeta seleccionada no existe"
        if not os.access(str(directory), os.W_OK):
            return False, "La carpeta seleccionada no tiene permisos de escritura"
        return True, "Carpeta válida"

    def crear_respaldo_en_directorio(self, directory_path: str) -> tuple[bool, str]:
        ok, message = self.validar_directorio_respaldo(directory_path)
        if not ok:
            return False, message
        destination = Path(directory_path).expanduser().resolve() / self.nombre_respaldo_sugerido()
        return self.crear_respaldo(str(destination))

    def restaurar_desde_respaldo(self, backup_path: str) -> tuple[bool, str]:
        source_conn: sqlite3.Connection | None = None
        target_conn: sqlite3.Connection | None = None
        test_conn: sqlite3.Connection | None = None
        try:
            source = Path(backup_path).expanduser().resolve()
            if not source.exists() or not source.is_file():
                return False, "El archivo de respaldo no existe"

            if source.suffix.lower() != ".db":
                return False, "El archivo seleccionado no es una base .db"

            # Conexión de prueba con cierre explícito
            test_conn = sqlite3.connect(str(source))
            test_conn.execute("PRAGMA schema_version;").fetchone()
            test_conn.close()
            test_conn = None

            source_conn = sqlite3.connect(str(source))
            target_conn = sqlite3.connect(str(self.db_path))
            source_conn.backup(target_conn)

            return True, "Restauración completada. Reinicie la aplicación para aplicar cambios"
        except Exception as exc:
            return False, f"Error al restaurar respaldo: {exc}"
        finally:
            if test_conn is not None:
                test_conn.close()
            if target_conn is not None:
                target_conn.close()
            if source_conn is not None:
                source_conn.close()
            gc.collect()

    def _resolve_destination(self, destination_path: str) -> Path:
        text = str(destination_path or "").strip()
        if not text:
            raise ValueError("Ruta de destino inválida")

        path = Path(text).expanduser().resolve()
        if path.is_dir() or path.suffix == "":
            return path / self.nombre_respaldo_sugerido()
        if path.suffix.lower() != ".db":
            return path.with_suffix(".db")
        return path
