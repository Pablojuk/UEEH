"""Pruebas de configuración inicial y compatibilidad heredada en V4."""

from __future__ import annotations

import os
import tempfile
import unittest

from src.application.services.setup_service import SetupService
from src.infrastructure.persistence.db import initialize_database
from src.shared.security import generar_salt, hash_clave


class TestSetupService(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp.name
        tmp.close()
        self.connection = initialize_database(self.db_path)
        self.service = SetupService(self.connection)

    def tearDown(self) -> None:
        self.connection.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _insert_legacy_configuration(self, completed: int = 1) -> tuple[str, str]:
        salt = generar_salt()
        password_hash = hash_clave("Clave-Legada-Sintética", salt)
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO configuracion_sistema (
                    id, clave_inicial_hash, clave_inicial_salt,
                    primer_uso_completado, escala_maxima, escala_minima,
                    correo_recuperacion, licencia_activada, fecha_primer_inicio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (1, password_hash, salt, completed, 10.0, 0.0, None, 1, None),
            )
        return password_hash, salt

    def test_primer_uso_sin_configuracion(self) -> None:
        self.assertTrue(self.service.es_primer_uso())

    def test_creacion_configuracion_inicial_sin_credenciales(self) -> None:
        resultado = self.service.configurar_sistema_inicial()
        row = self.connection.execute(
            "SELECT clave_inicial_hash, clave_inicial_salt, correo_recuperacion, "
            "primer_uso_completado FROM configuracion_sistema WHERE id = 1"
        ).fetchone()

        self.assertTrue(resultado["creado"])
        self.assertIsNone(row["clave_inicial_hash"])
        self.assertIsNone(row["clave_inicial_salt"])
        self.assertIsNone(row["correo_recuperacion"])
        self.assertEqual(row["primer_uso_completado"], 1)

    def test_configuracion_es_idempotente(self) -> None:
        primero = self.service.configurar_sistema_inicial()
        segundo = self.service.configurar_sistema_inicial()

        self.assertTrue(primero["creado"])
        self.assertFalse(segundo["creado"])
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM configuracion_sistema"
            ).fetchone()[0],
            1,
        )

    def test_configuracion_existente_preserva_hash_y_salt(self) -> None:
        password_hash, salt = self._insert_legacy_configuration(completed=0)

        resultado = self.service.configurar_sistema_inicial()
        row = self.connection.execute(
            "SELECT clave_inicial_hash, clave_inicial_salt, primer_uso_completado "
            "FROM configuracion_sistema WHERE id = 1"
        ).fetchone()

        self.assertTrue(resultado["creado"])
        self.assertEqual(row["clave_inicial_hash"], password_hash)
        self.assertEqual(row["clave_inicial_salt"], salt)
        self.assertEqual(row["primer_uso_completado"], 1)

    def test_verificador_heredado_conserva_comparacion_segura(self) -> None:
        self._insert_legacy_configuration()

        self.assertTrue(self.service.validar_clave_maestra("Clave-Legada-Sintética"))
        self.assertFalse(self.service.validar_clave_maestra("Clave-Incorrecta-Sintética"))


if __name__ == "__main__":
    unittest.main()
