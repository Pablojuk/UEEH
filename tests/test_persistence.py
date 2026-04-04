"""Pruebas de persistencia SQLite para BLOQUE 2."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from src.infrastructure.persistence.db import create_connection, initialize_database
from src.infrastructure.persistence.repositories import (
    CursosRepository,
    EstudiantesRepository,
    MatriculasRepository,
    PeriodosLectivosRepository,
)
from src.infrastructure.persistence.seed import run_safe_seeds


class TestPersistenceSQLite(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp.name
        tmp.close()
        self.connection = initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.connection.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_creacion_tablas_principales(self) -> None:
        tablas_esperadas = {
            "configuracion_sistema",
            "institucion",
            "docentes",
            "cursos",
            "paralelos",
            "asignaturas",
            "periodos_lectivos",
            "estudiantes",
            "matriculas",
            "asignaciones_docente",
            "trimestres",
            "grade_records",
            "final_supplementary",
        }
        cursor = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tablas = {row["name"] for row in cursor.fetchall()}
        self.assertTrue(tablas_esperadas.issubset(tablas))

    def test_insercion_y_lectura_basica(self) -> None:
        repo = CursosRepository(self.connection)
        repo.crear({"id_curso": "C1", "nombre": "Primero", "nivel": "Básica"})

        obtenido = repo.obtener_por_id("C1")
        self.assertIsNotNone(obtenido)
        self.assertEqual(obtenido["nombre"], "Primero")

        repo.actualizar("C1", {"nombre": "Primero A"})
        actualizado = repo.obtener_por_id("C1")
        self.assertEqual(actualizado["nombre"], "Primero A")

    def test_foreign_keys_activas(self) -> None:
        repo_matriculas = MatriculasRepository(self.connection)
        with self.assertRaises(sqlite3.IntegrityError):
            repo_matriculas.crear(
                {
                    "id_matricula": "M1",
                    "estudiante_id": "NO_EXISTE",
                    "curso_id": "NO_EXISTE",
                    "paralelo_id": "NO_EXISTE",
                    "periodo_id": "NO_EXISTE",
                    "numero_lista": 1,
                }
            )

    def test_seeds_basicas_idempotentes(self) -> None:
        periodos_repo = PeriodosLectivosRepository(self.connection)
        periodos_repo.crear(
            {
                "id_periodo": "2025-2026",
                "anio_inicio": 2025,
                "anio_fin": 2026,
                "fecha_inicio": None,
                "fecha_fin": None,
            }
        )

        run_safe_seeds(
            self.connection,
            clave_inicial_hash="hash_demo",
            clave_inicial_salt="salt_demo",
            periodo_id="2025-2026",
        )
        run_safe_seeds(
            self.connection,
            clave_inicial_hash="hash_demo",
            clave_inicial_salt="salt_demo",
            periodo_id="2025-2026",
        )

        conf_count = self.connection.execute(
            "SELECT COUNT(*) AS c FROM configuracion_sistema"
        ).fetchone()["c"]
        trim_count = self.connection.execute(
            "SELECT COUNT(*) AS c FROM trimestres WHERE periodo_id = ?",
            ("2025-2026",),
        ).fetchone()["c"]

        self.assertEqual(conf_count, 1)
        self.assertEqual(trim_count, 3)

    def test_registro_basico_con_relaciones_validas(self) -> None:
        self.connection.execute(
            "INSERT INTO paralelos (id_paralelo, nombre) VALUES ('P1', 'A')"
        )
        PeriodosLectivosRepository(self.connection).crear(
            {
                "id_periodo": "PER1",
                "anio_inicio": 2025,
                "anio_fin": 2026,
                "fecha_inicio": None,
                "fecha_fin": None,
            }
        )
        CursosRepository(self.connection).crear(
            {"id_curso": "CUR1", "nombre": "Primero", "nivel": "Básica"}
        )
        EstudiantesRepository(self.connection).crear(
            {
                "id_estudiante": "EST1",
                "codigo": "001",
                "apellidos": "Pérez",
                "nombres": "Ana",
                "identificacion": None,
            }
        )

        MatriculasRepository(self.connection).crear(
            {
                "id_matricula": "MAT1",
                "estudiante_id": "EST1",
                "curso_id": "CUR1",
                "paralelo_id": "P1",
                "periodo_id": "PER1",
                "numero_lista": 5,
            }
        )
        row = MatriculasRepository(self.connection).obtener_por_id("MAT1")
        self.assertEqual(row["estudiante_id"], "EST1")

    def test_migracion_compatibilidad_agrega_columnas_nuevas(self) -> None:
        legacy_connection = create_connection(self.db_path)
        with legacy_connection:
            legacy_connection.execute("DROP TABLE IF EXISTS configuracion_sistema")
            legacy_connection.execute("DROP TABLE IF EXISTS docentes")
            legacy_connection.execute(
                """
                CREATE TABLE configuracion_sistema (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    clave_inicial_hash TEXT NOT NULL,
                    primer_uso_completado INTEGER NOT NULL DEFAULT 0,
                    escala_maxima REAL NOT NULL DEFAULT 10.0,
                    escala_minima REAL NOT NULL DEFAULT 0.0
                );
                """
            )
            legacy_connection.execute(
                """
                CREATE TABLE docentes (
                    id_docente TEXT PRIMARY KEY,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    identificacion TEXT NOT NULL UNIQUE
                );
                """
            )
        legacy_connection.close()

        migrated_connection = initialize_database(self.db_path)
        conf_cols = {
            row["name"]
            for row in migrated_connection.execute("PRAGMA table_info(configuracion_sistema)").fetchall()
        }
        doc_cols = {
            row["name"]
            for row in migrated_connection.execute("PRAGMA table_info(docentes)").fetchall()
        }
        self.assertIn("clave_inicial_salt", conf_cols)
        self.assertIn("activo", doc_cols)
        migrated_connection.close()


if __name__ == "__main__":
    unittest.main()
