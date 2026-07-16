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
        self.catalog_service.crear_asignatura(
            {"id_asignatura": "A2", "nombre": "Orientación Vocacional y Profesional", "codigo": "OVP"}
        )
        self.catalog_service.crear_curso({"id_curso": "C1", "nombre": "Primero", "nivel": "Basica"})
        self.catalog_service.crear_curso({"id_curso": "C8", "nombre": "8vo de EGB", "nivel": "Básica Superior"})
        self.catalog_service.crear_paralelo({"id_paralelo": "P-TA", "nombre": "P-TA"})
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
            "paralelo_id": "P-TA",
            "periodo_id": "2025-2026",
        })
        self.assertTrue(ok)
        self.assertEqual(len(self.assignment_service.listar_asignaciones()), 1)

    def test_evitar_duplicados(self) -> None:
        payload = {
            "docente_id": "D1",
            "asignatura_id": "A1",
            "curso_id": "C1",
            "paralelo_id": "P-TA",
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
            "paralelo_id": "P-TA",
            "periodo_id": "2025-2026",
        }
        self.assignment_service.crear_asignacion(payload)
        self.assertEqual(len(self.assignment_service.listar_por_docente("D1")), 1)
        self.assertEqual(len(self.assignment_service.listar_por_grupo("C1", "P-TA", "2025-2026")), 1)

    def test_eliminar_asignacion(self) -> None:
        ok, _ = self.assignment_service.crear_asignacion({
            "docente_id": "D1",
            "asignatura_id": "A1",
            "curso_id": "C1",
            "paralelo_id": "P-TA",
            "periodo_id": "2025-2026",
        })
        self.assertTrue(ok)
        assignment_id = self.assignment_service.listar_asignaciones()[0]["id_asignacion"]
        deleted, _ = self.assignment_service.eliminar_asignacion(assignment_id)
        self.assertTrue(deleted)
        self.assertEqual(len(self.assignment_service.listar_asignaciones()), 0)

    def _crear_asignacion_con_dependencias(self) -> str:
        ok, _ = self.assignment_service.crear_asignacion({
            "docente_id": "D1", "asignatura_id": "A1", "curso_id": "C8",
            "paralelo_id": "P-TA", "periodo_id": "2025-2026",
        })
        self.assertTrue(ok)
        assignment_id = self.assignment_service.listar_asignaciones()[0]["id_asignacion"]
        self.connection.execute(
            "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres) VALUES (?, ?, ?, ?)",
            ("E1", "EST-001", "Prueba", "Estudiante"),
        )
        self.connection.execute(
            "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id) "
            "VALUES (?, ?, ?, ?, ?)", ("M1", "E1", "C8", "P-TA", "2025-2026"),
        )
        statements = (
            ("INSERT INTO grade_records (id_registro, estudiante_id, asignacion_id, trimestre_num) VALUES (?, ?, ?, 1)", ("GR1", "E1", assignment_id)),
            ("INSERT INTO final_supplementary (id_supletorio, estudiante_id, asignacion_id) VALUES (?, ?, ?)", ("FS1", "E1", assignment_id)),
            ("INSERT INTO grade_activity_config (id_config, asignacion_id, trimestre_num, numero_actividades) VALUES (?, ?, 1, 2)", ("GC1", assignment_id)),
            ("INSERT INTO acompanamiento_evaluaciones (id_evaluacion, asignacion_id, trimestre_num, estudiante_id, habilidad_clave, valor) VALUES (?, ?, 1, ?, 'H1', 'Siempre')", ("AC1", assignment_id, "E1")),
            ("INSERT INTO acompanamiento_habilidades_config (id_config, asignacion_id, trimestre_num, habilidad_clave, visible) VALUES (?, ?, 1, 'H1', 1)", ("AH1", assignment_id)),
            ("INSERT INTO animacion_lectura_evaluaciones (id_evaluacion, asignacion_id, trimestre_num, nivel, estudiante_id) VALUES (?, ?, 1, '8', ?)", ("AL1", assignment_id, "E1")),
            ("INSERT INTO orientacion_vocacional_evaluaciones (id_evaluacion, asignacion_id, trimestre_num, curso_clave, estudiante_id, respuestas_json) VALUES (?, ?, 1, '8', ?, '{}')", ("OV1", assignment_id, "E1")),
            ("INSERT INTO attendance_records (id, assignment_id, student_id, date, created_at, updated_at) VALUES (?, ?, ?, '2025-01-01', '2025-01-01', '2025-01-01')", ("AT1", assignment_id, "E1")),
            ("INSERT INTO attendance_justifications (id, assignment_id, student_id, date, reason, created_at) VALUES (?, ?, ?, '2025-01-01', 'Prueba', '2025-01-01')", ("AJ1", assignment_id, "E1")),
        )
        for statement, params in statements:
            self.connection.execute(statement, params)
        self.connection.commit()
        return assignment_id

    def test_eliminar_asignacion_borra_dependencias_y_conserva_entidades(self) -> None:
        assignment_id = self._crear_asignacion_con_dependencias()
        expected = {table: 1 for table, _ in self.assignment_service.DEPENDENT_ASSIGNMENT_TABLES}
        self.assertEqual(self.assignment_service.contar_registros_dependientes(assignment_id), expected)

        deleted, message = self.assignment_service.eliminar_asignacion(assignment_id)

        self.assertTrue(deleted, message)
        self.assertEqual(
            self.assignment_service.contar_registros_dependientes(assignment_id),
            {table: 0 for table in expected},
        )
        for table, key in (("docentes", "id_docente = 'D1'"), ("estudiantes", "id_estudiante = 'E1'"), ("matriculas", "id_matricula = 'M1'")):
            total = self.connection.execute(f"SELECT COUNT(1) AS total FROM {table} WHERE {key}").fetchone()["total"]
            self.assertEqual(total, 1, table)

    def test_eliminar_asignacion_revierte_todo_si_falla(self) -> None:
        assignment_id = self._crear_asignacion_con_dependencias()
        self.connection.execute(
            "CREATE TRIGGER impedir_borrado_asignacion BEFORE DELETE ON asignaciones_docente "
            "BEGIN SELECT RAISE(ABORT, 'fallo forzado'); END"
        )

        deleted, message = self.assignment_service.eliminar_asignacion(assignment_id)

        self.assertFalse(deleted)
        self.assertIn("no se aplicaron cambios", message.lower())
        self.assertIsNotNone(self.assignment_service.repo.obtener_por_id(assignment_id))
        self.assertEqual(
            self.assignment_service.contar_registros_dependientes(assignment_id),
            {table: 1 for table, _ in self.assignment_service.DEPENDENT_ASSIGNMENT_TABLES},
        )

    def test_bloquea_orientacion_en_curso_no_permitido(self) -> None:
        ok, message = self.assignment_service.crear_asignacion(
            {
                "docente_id": "D1",
                "asignatura_id": "A2",
                "curso_id": "C1",
                "paralelo_id": "P-TA",
                "periodo_id": "2025-2026",
            }
        )
        self.assertFalse(ok)
        self.assertIn("solo corresponde", message.lower())

    def test_permita_orientacion_en_8vo(self) -> None:
        ok, message = self.assignment_service.crear_asignacion(
            {
                "docente_id": "D1",
                "asignatura_id": "A2",
                "curso_id": "C8",
                "paralelo_id": "P-TA",
                "periodo_id": "2025-2026",
            }
        )
        self.assertTrue(ok)
        self.assertIn("creada", message.lower())
