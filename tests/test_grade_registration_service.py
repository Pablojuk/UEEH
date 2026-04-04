"""Pruebas del servicio de registro de notas."""

from __future__ import annotations

import unittest

from src.application.services.grade_registration_service import GradeRegistrationService
from src.infrastructure.persistence.db import initialize_database


class TestGradeRegistrationService(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = initialize_database(":memory:")
        self.service = GradeRegistrationService(self.conn)
        self._seed_context()

    def tearDown(self) -> None:
        self.conn.close()

    def _seed_context(self) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO docentes (id_docente, nombres, apellidos, identificacion, activo) VALUES (?, ?, ?, ?, ?)",
                ("D1", "Ana", "Perez", "123", 1),
            )
            self.conn.execute(
                "INSERT INTO asignaturas (id_asignatura, nombre, codigo) VALUES (?, ?, ?)",
                ("A1", "Matematica", "MAT"),
            )
            self.conn.execute(
                "INSERT INTO cursos (id_curso, nombre, nivel) VALUES (?, ?, ?)",
                ("C1", "Primero", "Basica"),
            )
            self.conn.execute("INSERT INTO paralelos (id_paralelo, nombre) VALUES (?, ?)", ("P1", "A"))
            self.conn.execute(
                "INSERT INTO periodos_lectivos (id_periodo, anio_inicio, anio_fin, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?, ?)",
                ("2025-2026", 2025, 2026, None, None),
            )
            self.conn.execute(
                "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres, identificacion) VALUES (?, ?, ?, ?, ?)",
                ("E1", "EST-1", "Lopez", "Maria", "999"),
            )
            self.conn.execute(
                "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id, numero_lista) VALUES (?, ?, ?, ?, ?, ?)",
                ("M1", "E1", "C1", "P1", "2025-2026", 1),
            )
            self.conn.execute(
                "INSERT INTO asignaciones_docente (id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) VALUES (?, ?, ?, ?, ?, ?)",
                ("AS1", "D1", "A1", "C1", "P1", "2025-2026"),
            )

    def test_cargar_estudiantes_de_contexto_valido(self) -> None:
        rows = self.service.cargar_registro("AS1", 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["estudiante_id"], "E1")

    def test_guardar_notas_nuevas(self) -> None:
        ok, _ = self.service.guardar_registros(
            "AS1",
            1,
            [
                {
                    "estudiante_id": "E1",
                    "actividad_1": 9,
                    "mejora_1": 10,
                    "actividad_2": 8,
                    "mejora_2": None,
                    "actividad_3": 7,
                    "mejora_3": 8,
                    "proyecto": 9,
                    "evaluacion": 8,
                    "refuerzo": 7,
                    "mejora_sumativa": 10,
                }
            ],
        )
        self.assertTrue(ok)

        row = self.conn.execute(
            "SELECT * FROM grade_records WHERE estudiante_id = ? AND asignacion_id = ? AND trimestre_num = ?",
            ("E1", "AS1", 1),
        ).fetchone()
        self.assertIsNotNone(row)

    def test_actualizar_notas_existentes_sin_duplicar(self) -> None:
        self.service.guardar_registros("AS1", 1, [{"estudiante_id": "E1", "actividad_1": 7, "proyecto": 7}])
        self.service.guardar_registros("AS1", 1, [{"estudiante_id": "E1", "actividad_1": 10, "proyecto": 9}])

        count = self.conn.execute(
            "SELECT COUNT(*) AS total FROM grade_records WHERE estudiante_id = ? AND asignacion_id = ? AND trimestre_num = ?",
            ("E1", "AS1", 1),
        ).fetchone()["total"]
        self.assertEqual(count, 1)

        row = self.conn.execute(
            "SELECT actividad_1, proyecto FROM grade_records WHERE estudiante_id = ? AND asignacion_id = ? AND trimestre_num = ?",
            ("E1", "AS1", 1),
        ).fetchone()
        self.assertEqual(row["actividad_1"], 10)
        self.assertEqual(row["proyecto"], 9)

    def test_recalcular_promedios_correctamente(self) -> None:
        fila = self.service.recalcular_fila(
            {
                "estudiante_id": "E1",
                "actividad_1": 9,
                "mejora_1": 10,
                "actividad_2": 8,
                "mejora_2": None,
                "actividad_3": 7,
                "mejora_3": 8,
                "proyecto": 9,
                "evaluacion": 8,
                "refuerzo": 7,
                "mejora_sumativa": 10,
            }
        )
        self.assertEqual(fila["promedio_formativo"], 8.33)
        self.assertEqual(fila["promedio_sumativo"], 8.16)
        self.assertEqual(fila["nota_trimestral"], 8.27)

    def test_contexto_sin_estudiantes_retorna_vacio(self) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO asignaciones_docente (id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) VALUES (?, ?, ?, ?, ?, ?)",
                ("AS2", "D1", "A1", "C1", "P1", "2025-2026"),
            )
            self.conn.execute("DELETE FROM matriculas")

        rows = self.service.cargar_registro("AS2", 1)
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
