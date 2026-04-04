"""Pruebas del servicio de asignaciones académicas."""

from __future__ import annotations

import os
import tempfile
import unittest

from src.application.services.catalog_service import CatalogService
from src.application.services.teacher_service import TeacherService
from src.application.services.teaching_assignment_service import TeachingAssignmentService
from src.infrastructure.persistence.db import initialize_database


class TestTeachingAssignmentService(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp.name
        tmp.close()
        self.connection = initialize_database(self.db_path)

        self.teacher_service = TeacherService(self.connection)
        self.catalog_service = CatalogService(self.connection)
        self.assignment_service = TeachingAssignmentService(self.connection)

        self.teacher_service.crear_docente({
            "id_docente": "D1",
            "nombres": "Ana",
            "apellidos": "Perez",
            "identificacion": "123",
        })
        self.catalog_service.crear_asignatura({"id_asignatura": "A1", "nombre": "Matemática", "codigo": "MAT"})
        self.catalog_service.crear_curso({"id_curso": "C1", "nombre": "Primero", "nivel": "Basica"})
        self.catalog_service.crear_paralelo({"id_paralelo": "P1", "nombre": "A"})
        self.catalog_service.crear_periodo_lectivo({
            "id_periodo": "2025-2026",
            "anio_inicio": 2025,
            "anio_fin": 2026,
            "fecha_inicio": None,
            "fecha_fin": None,
        })

    def tearDown(self) -> None:
        self.connection.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_crear_y_listar_asignacion(self) -> None:
        ok, _ = self.assignment_service.crear_asignacion({
            "docente_id": "D1",
            "asignatura_id": "A1",
            "curso_id": "C1",
            "paralelo_id": "P1",
            "periodo_id": "2025-2026",
        })
        self.assertTrue(ok)
        self.assertEqual(len(self.assignment_service.listar_asignaciones()), 1)

    def test_evitar_duplicados(self) -> None:
        payload = {
            "docente_id": "D1",
            "asignatura_id": "A1",
            "curso_id": "C1",
            "paralelo_id": "P1",
            "periodo_id": "2025-2026",
        }
        self.assignment_service.crear_asignacion(payload)
        ok, _ = self.assignment_service.crear_asignacion(payload)
        self.assertFalse(ok)

    def test_listar_por_docente_y_grupo(self) -> None:
        payload = {
            "docente_id": "D1",
            "asignatura_id": "A1",
            "curso_id": "C1",
            "paralelo_id": "P1",
            "periodo_id": "2025-2026",
        }
        self.assignment_service.crear_asignacion(payload)
        self.assertEqual(len(self.assignment_service.listar_por_docente("D1")), 1)
        self.assertEqual(len(self.assignment_service.listar_por_grupo("C1", "P1", "2025-2026")), 1)
