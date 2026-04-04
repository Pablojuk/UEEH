"""Pruebas del servicio de estudiantes."""

from __future__ import annotations

import os
import tempfile
import unittest

from src.application.services.student_service import StudentService
from src.infrastructure.persistence.db import initialize_database


class TestStudentService(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp.name
        tmp.close()
        self.connection = initialize_database(self.db_path)
        self.service = StudentService(self.connection)

    def tearDown(self) -> None:
        self.connection.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_crear_y_listar_estudiante(self) -> None:
        ok, _ = self.service.crear_estudiante({"nombres": "Ana", "apellidos": "Pérez", "identificacion": "123"})
        self.assertTrue(ok)
        self.assertEqual(len(self.service.listar_estudiantes()), 1)

    def test_buscar_estudiante(self) -> None:
        self.service.crear_estudiante({"nombres": "Luis", "apellidos": "García", "identificacion": "999"})
        found = self.service.buscar_estudiantes("luis")
        self.assertEqual(len(found), 1)

    def test_evitar_duplicado_por_identificacion(self) -> None:
        self.service.crear_estudiante({"nombres": "Ana", "apellidos": "Pérez", "identificacion": "123"})
        ok, message = self.service.crear_estudiante({"nombres": "Ana2", "apellidos": "Pérez2", "identificacion": "123"})
        self.assertFalse(ok)
        self.assertIn("Duplicado", message)

    def test_permite_sin_codigo_estudiante(self) -> None:
        ok, _ = self.service.crear_estudiante({"nombres": "Mario", "apellidos": "Lopez", "identificacion": None})
        self.assertTrue(ok)
        row = self.service.listar_estudiantes()[0]
        self.assertTrue(row["codigo"].startswith("AUTO-"))
