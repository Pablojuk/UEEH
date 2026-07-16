"""Semillas iniciales para base de datos de BLOQUE 2."""

from __future__ import annotations

import sqlite3

from .repositories import ConfiguracionSistemaRepository


CATALOG_COURSES: tuple[dict[str, str], ...] = (
    {"id_curso": "CUR-000", "nombre": "2do de EGB", "nivel": "EGB"},
    {"id_curso": "CUR-00A", "nombre": "3ro de EGB", "nivel": "EGB"},
    {"id_curso": "CUR-00B", "nombre": "4to de EGB", "nivel": "EGB"},
    {"id_curso": "CUR-001", "nombre": "5to EGB", "nivel": "EGB"},
    {"id_curso": "CUR-002", "nombre": "6to EGB", "nivel": "EGB"},
    {"id_curso": "CUR-003", "nombre": "7mo EGB", "nivel": "EGB"},
    {"id_curso": "CUR-004", "nombre": "8vo EGB", "nivel": "EGB"},
    {"id_curso": "CUR-005", "nombre": "9no EGB", "nivel": "EGB"},
    {"id_curso": "CUR-006", "nombre": "10mo EGB", "nivel": "EGB"},
    {"id_curso": "CUR-007", "nombre": "1ro BGU", "nivel": "BGU"},
    {"id_curso": "CUR-008", "nombre": "2do BGU", "nivel": "BGU"},
    {"id_curso": "CUR-009", "nombre": "3ro BGU", "nivel": "BGU"},
)

CATALOG_PARALLELS: tuple[dict[str, str], ...] = (
    {"id_paralelo": "PAR-001", "nombre": "A"},
    {"id_paralelo": "PAR-002", "nombre": "B"},
    {"id_paralelo": "PAR-003", "nombre": "C"},
    {"id_paralelo": "PAR-004", "nombre": "D"},
    {"id_paralelo": "PAR-005", "nombre": "E"},
    {"id_paralelo": "PAR-006", "nombre": "F"},
    {"id_paralelo": "PAR-007", "nombre": "G"},
    {"id_paralelo": "PAR-008", "nombre": "H"},
)

CATALOG_SUBJECTS: tuple[dict[str, str], ...] = (
    {"id_asignatura": "ASIG-000", "nombre": "Orientación vocacional y profesional", "codigo": "OVP"},
    {"id_asignatura": "ASIG-00A", "nombre": "Acompañamiento integral en el aula", "codigo": "AIA"},
    {"id_asignatura": "ASIG-00C", "nombre": "Comportamiento", "codigo": "COM"},
    {"id_asignatura": "ASIG-00B", "nombre": "Animación a la Lectura", "codigo": "AL"},
    {"id_asignatura": "ASIG-001", "nombre": "Matemática", "codigo": "MAT"},
    {"id_asignatura": "ASIG-002", "nombre": "Lengua y Literatura", "codigo": "LYL"},
    {"id_asignatura": "ASIG-003", "nombre": "Ciencias Naturales", "codigo": "CN"},
    {"id_asignatura": "ASIG-004", "nombre": "Estudios Sociales", "codigo": "ES"},
    {"id_asignatura": "ASIG-005", "nombre": "Inglés", "codigo": "ING"},
    {"id_asignatura": "ASIG-006", "nombre": "Educación Cultural y Artística", "codigo": "ECA"},
    {"id_asignatura": "ASIG-007", "nombre": "Educación Física", "codigo": "EF"},
    {"id_asignatura": "ASIG-008", "nombre": "Emprendimiento y Gestión", "codigo": "EYG"},
    {"id_asignatura": "ASIG-009", "nombre": "Filosofía", "codigo": "FIL"},
    {"id_asignatura": "ASIG-010", "nombre": "Historia", "codigo": "HIS"},
    {"id_asignatura": "ASIG-011", "nombre": "Biología", "codigo": "BIO"},
    {"id_asignatura": "ASIG-012", "nombre": "Física", "codigo": "FIS"},
    {"id_asignatura": "ASIG-013", "nombre": "Química", "codigo": "QUI"},
)


def seed_configuracion_base(
    connection: sqlite3.Connection,
    clave_inicial_hash: str,
    clave_inicial_salt: str,
) -> None:
    """Crea configuración base única (id=1) si aún no existe."""
    repo = ConfiguracionSistemaRepository(connection)
    if repo.obtener_por_id(1) is None:
        repo.crear(
            {
                "id": 1,
                "clave_inicial_hash": clave_inicial_hash,
                "clave_inicial_salt": clave_inicial_salt,
                "primer_uso_completado": 0,
                "escala_maxima": 10.0,
                "escala_minima": 0.0,
                "correo_recuperacion": None,
                "licencia_activada": 0,
                "fecha_primer_inicio": None,
            }
        )


def seed_trimestres(connection: sqlite3.Connection, periodo_id: str) -> None:
    """Inserta trimestres 1-3 para un periodo, evitando duplicados."""
    seeds = [
        {"id_trimestre": f"{periodo_id}-T1", "numero": 1, "nombre": "Trimestre 1", "periodo_id": periodo_id},
        {"id_trimestre": f"{periodo_id}-T2", "numero": 2, "nombre": "Trimestre 2", "periodo_id": periodo_id},
        {"id_trimestre": f"{periodo_id}-T3", "numero": 3, "nombre": "Trimestre 3", "periodo_id": periodo_id},
    ]

    with connection:
        for seed in seeds:
            connection.execute(
                """
                INSERT OR IGNORE INTO trimestres (id_trimestre, numero, nombre, periodo_id)
                VALUES (:id_trimestre, :numero, :nombre, :periodo_id)
                """,
                seed,
            )


def seed_catalogos_academicos(connection: sqlite3.Connection) -> None:
    """Inserta catálogos base de cursos, paralelos y asignaturas sin duplicar."""
    with connection:
        for course in CATALOG_COURSES:
            exists = connection.execute(
                "SELECT 1 FROM cursos WHERE id_curso = ? OR nombre = ? LIMIT 1",
                (course["id_curso"], course["nombre"]),
            ).fetchone()
            if exists is None:
                connection.execute(
                    """
                    INSERT INTO cursos (id_curso, nombre, nivel)
                    VALUES (:id_curso, :nombre, :nivel)
                    """,
                    course,
                )

        for parallel in CATALOG_PARALLELS:
            exists = connection.execute(
                "SELECT 1 FROM paralelos WHERE id_paralelo = ? OR nombre = ? LIMIT 1",
                (parallel["id_paralelo"], parallel["nombre"]),
            ).fetchone()
            if exists is None:
                connection.execute(
                    """
                    INSERT INTO paralelos (id_paralelo, nombre)
                    VALUES (:id_paralelo, :nombre)
                    """,
                    parallel,
                )

        for subject in CATALOG_SUBJECTS:
            exists = connection.execute(
                "SELECT 1 FROM asignaturas WHERE id_asignatura = ? OR nombre = ? LIMIT 1",
                (subject["id_asignatura"], subject["nombre"]),
            ).fetchone()
            if exists is None:
                connection.execute(
                    """
                    INSERT INTO asignaturas (id_asignatura, nombre, codigo)
                    VALUES (:id_asignatura, :nombre, :codigo)
                    """,
                    subject,
                )


def run_safe_seeds(
    connection: sqlite3.Connection,
    clave_inicial_hash: str,
    clave_inicial_salt: str,
    periodo_id: str,
) -> None:
    """Ejecuta semillas base de forma idempotente."""
    seed_configuracion_base(
        connection,
        clave_inicial_hash=clave_inicial_hash,
        clave_inicial_salt=clave_inicial_salt,
    )
    seed_trimestres(connection, periodo_id=periodo_id)
