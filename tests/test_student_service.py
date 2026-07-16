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

    def test_ordenar_estudiantes_por_codigo_para_presentacion(self) -> None:
        rows = [
            {"id_estudiante": "N2", "codigo": "zeta"},
            {"id_estudiante": "V100", "codigo": "EST-100"},
            {"id_estudiante": "E1", "codigo": ""},
            {"id_estudiante": "V10", "codigo": "EST-010"},
            {"id_estudiante": "N1", "codigo": "Alpha"},
            {"id_estudiante": "V2", "codigo": "est-002"},
            {"id_estudiante": "N3", "codigo": "alpha"},
            {"id_estudiante": "V9", "codigo": "EST-009"},
            {"id_estudiante": "E2", "codigo": None},
            {"id_estudiante": "V1", "codigo": "EST-001"},
        ]

        ordered = self.service.ordenar_estudiantes_por_codigo(rows)

        self.assertEqual(
            [row["id_estudiante"] for row in ordered],
            ["V1", "V2", "V9", "V10", "V100", "N1", "N3", "N2", "E1", "E2"],
        )
        self.assertEqual(rows[0]["id_estudiante"], "N2")
