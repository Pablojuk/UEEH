"""Pruebas de respaldo y restauración de SQLite (corregido para Windows)."""

from __future__ import annotations

import gc
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.application.services.backup_service import BackupService
from src.infrastructure.persistence.db import initialize_database


class TestBackupService(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "origen.db"
        self.conn = initialize_database(str(self.db_path))
        with self.conn:
            self.conn.execute("INSERT INTO cursos (id_curso, nombre, nivel) VALUES (?, ?, ?)", ("C1", "Primero", "Basica"))
        self.conn.close()
        self.service = BackupService(str(self.db_path))

    def tearDown(self) -> None:
        if hasattr(self, "conn") and self.conn:
            try:
                self.conn.close()
            except Exception:
                pass

        gc.collect()

        try:
            self.tmp_dir.cleanup()
        except OSError:
            pass

    def test_crear_respaldo_en_ruta_valida(self) -> None:
        backup_path = Path(self.tmp_dir.name) / "respaldo.db"
        ok, message = self.service.crear_respaldo(str(backup_path))
        self.assertTrue(ok)
        self.assertTrue(backup_path.exists())
        self.assertIn("Respaldo creado", message)

    def test_manejar_ruta_invalida(self) -> None:
        ok, message = self.service.crear_respaldo("")
        self.assertFalse(ok)
        self.assertIn("Error al crear respaldo", message)

    def test_detectar_archivo_inexistente_al_restaurar(self) -> None:
        missing = Path(self.tmp_dir.name) / "no_existe.db"
        ok, message = self.service.restaurar_desde_respaldo(str(missing))
        self.assertFalse(ok)
        self.assertIn("no existe", message)

    def test_restaurar_base_valida_de_prueba(self) -> None:
        backup_path = Path(self.tmp_dir.name) / "respaldo.db"
        self.service.crear_respaldo(str(backup_path))

        conn_edit = sqlite3.connect(str(self.db_path))
        try:
            conn_edit.execute("DELETE FROM cursos")
            conn_edit.commit()
        finally:
            conn_edit.close()

        ok, _ = self.service.restaurar_desde_respaldo(str(backup_path))
        self.assertTrue(ok)

        conn_check = sqlite3.connect(str(self.db_path))
        try:
            count = conn_check.execute("SELECT COUNT(*) FROM cursos").fetchone()[0]
        finally:
            conn_check.close()

        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
