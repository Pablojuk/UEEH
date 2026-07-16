"""Pruebas del servicio de configuración inicial."""

from __future__ import annotations

import os
import tempfile
import unittest

from src.application.services.setup_service import SetupService
from src.infrastructure.persistence.db import initialize_database


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

    def test_primer_uso_sin_configuracion(self) -> None:
        self.assertTrue(self.service.es_primer_uso())

    def test_creacion_configuracion_inicial_y_hash(self) -> None:
        resultado = self.service.configurar_sistema_inicial("ClaveSegura123")
        self.assertTrue(resultado["creado"])

        row = self.connection.execute(
            "SELECT clave_inicial_hash, clave_inicial_salt, primer_uso_completado "
            "FROM configuracion_sistema WHERE id = 1"
        ).fetchone()

        self.assertIsNotNone(row)
        self.assertNotEqual(row["clave_inicial_hash"], "ClaveSegura123")
        self.assertTrue(row["clave_inicial_salt"])
        self.assertEqual(row["primer_uso_completado"], 1)

    def test_verificacion_clave_correcta(self) -> None:
        self.service.configurar_sistema_inicial("ClaveSegura123")
        self.assertTrue(self.service.validar_clave_maestra("ClaveSegura123"))

    def test_rechazo_clave_incorrecta(self) -> None:
        self.service.configurar_sistema_inicial("ClaveSegura123")
        self.assertFalse(self.service.validar_clave_maestra("ClaveIncorrecta"))

    def test_idempotente_si_ya_configurado(self) -> None:
        primero = self.service.configurar_sistema_inicial("ClaveSegura123")
        segundo = self.service.configurar_sistema_inicial("OtraClave456")

        self.assertTrue(primero["creado"])
        self.assertFalse(segundo["creado"])
        self.assertTrue(self.service.validar_clave_maestra("ClaveSegura123"))
        self.assertFalse(self.service.validar_clave_maestra("OtraClave456"))


if __name__ == "__main__":
    unittest.main()
