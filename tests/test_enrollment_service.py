"""Pruebas del servicio de matrículas."""

from __future__ import annotations

import os
import tempfile
import unittest

from src.application.services.catalog_service import CatalogService
from src.application.services.enrollment_service import EnrollmentService
from src.application.services.student_service import StudentService
from src.infrastructure.persistence.db import initialize_database


class TestEnrollmentService(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp.name
        tmp.close()
        self.connection = initialize_database(self.db_path)

        self.student_service = StudentService(self.connection)
        self.catalog_service = CatalogService(self.connection)
        self.enrollment_service = EnrollmentService(self.connection)

        self.student_service.crear_estudiante({"nombres": "Ana", "apellidos": "Perez", "identificacion": "1"})
        self.catalog_service.crear_curso({"id_curso": "C1", "nombre": "Primero", "nivel": "Basica"})
        self.catalog_service.crear_paralelo({"id_paralelo": "P1", "nombre": "A"})
        self.catalog_service.crear_periodo_lectivo({
            "id_periodo": "2025-2026",
            "anio_inicio": 2025,
            "anio_fin": 2026,
            "fecha_inicio": None,
            "fecha_fin": None,
        })

        self.student_id = self.student_service.listar_estudiantes()[0]["id_estudiante"]

    def tearDown(self) -> None:
        self.connection.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_crear_y_listar_matricula(self) -> None:
        ok, _ = self.enrollment_service.crear_matricula({
            "estudiante_id": self.student_id,
            "curso_id": "C1",
            "paralelo_id": "P1",
            "periodo_id": "2025-2026",
        })
        self.assertTrue(ok)
        self.assertEqual(len(self.enrollment_service.listar_matriculas()), 1)

    def test_evitar_duplicados(self) -> None:
        payload = {
            "estudiante_id": self.student_id,
            "curso_id": "C1",
            "paralelo_id": "P1",
            "periodo_id": "2025-2026",
        }
        self.enrollment_service.crear_matricula(payload)
        ok, message = self.enrollment_service.crear_matricula(payload)
        self.assertFalse(ok)
        self.assertIn("duplicada", message.lower())

    def test_listar_por_grupo(self) -> None:
        self.enrollment_service.crear_matricula({
            "estudiante_id": self.student_id,
            "curso_id": "C1",
            "paralelo_id": "P1",
            "periodo_id": "2025-2026",
        })
        rows = self.enrollment_service.listar_por_grupo("C1", "P1", "2025-2026")
        self.assertEqual(len(rows), 1)

    def test_eliminar_matricula(self) -> None:
        self.enrollment_service.crear_matricula({
            "estudiante_id": self.student_id,
            "curso_id": "C1",
            "paralelo_id": "P1",
            "periodo_id": "2025-2026",
        })
        enrollment_id = self.enrollment_service.listar_matriculas()[0]["id_matricula"]
        ok, _ = self.enrollment_service.eliminar_matricula(enrollment_id)
        self.assertTrue(ok)
        self.assertEqual(len(self.enrollment_service.listar_matriculas()), 0)
