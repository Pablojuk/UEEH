"""Conexión e inicialización de base de datos SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .schema import get_schema_statements

DEFAULT_DB_DIR = Path(__file__).resolve().parents[3] / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "sistema_notas.db"


SQLITE_MEMORY_PATHS = {":memory:"}


def create_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Crea una conexión SQLite y activa foreign keys.

    Acepta rutas de archivo y también el valor especial ":memory:".
    """
    if db_path in SQLITE_MEMORY_PATHS:
        connection = sqlite3.connect(db_path)
    else:
        resolved_path = Path(db_path).expanduser().resolve() if db_path else DEFAULT_DB_PATH
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(resolved_path)

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def _column_exists(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    columns = {row["name"] for row in cursor.fetchall()}
    return column_name in columns


def _run_compatibility_migrations(connection: sqlite3.Connection) -> None:
    """Aplica migraciones mínimas para esquemas existentes de bloques previos."""
    with connection:
        if _column_exists(connection, "configuracion_sistema", "id"):
            if not _column_exists(connection, "configuracion_sistema", "clave_inicial_salt"):
                connection.execute(
                    "ALTER TABLE configuracion_sistema ADD COLUMN clave_inicial_salt TEXT NOT NULL DEFAULT ''"
                )

        if _column_exists(connection, "docentes", "id_docente"):
            if not _column_exists(connection, "docentes", "activo"):
                connection.execute(
                    "ALTER TABLE docentes ADD COLUMN activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))"
                )
            if not _column_exists(connection, "docentes", "titulo"):
                connection.execute("ALTER TABLE docentes ADD COLUMN titulo TEXT")

        if _column_exists(connection, "institucion", "id_institucion"):
            if not _column_exists(connection, "institucion", "logo_path"):
                connection.execute("ALTER TABLE institucion ADD COLUMN logo_path TEXT")
            for column_name in (
                "provincia",
                "ciudad",
                "parroquia",
                "direccion",
                "codigo_amie",
                "rector",
                "vicerrector",
                "inspector",
                "logo_ministerio_path",
            ):
                if not _column_exists(connection, "institucion", column_name):
                    connection.execute(f"ALTER TABLE institucion ADD COLUMN {column_name} TEXT")

        if _column_exists(connection, "grade_records", "id_registro"):
            if not _column_exists(connection, "grade_records", "actividades_json"):
                connection.execute("ALTER TABLE grade_records ADD COLUMN actividades_json TEXT")
            if not _column_exists(connection, "grade_records", "mejoras_json"):
                connection.execute("ALTER TABLE grade_records ADD COLUMN mejoras_json TEXT")

        if _column_exists(connection, "grade_activity_config", "id_config"):
            if not _column_exists(connection, "grade_activity_config", "metadata_json"):
                connection.execute("ALTER TABLE grade_activity_config ADD COLUMN metadata_json TEXT")


def initialize_database(db_path: str | None = None) -> sqlite3.Connection:
    """Inicializa el esquema completo y retorna la conexión activa."""
    connection = create_connection(db_path=db_path)
    statements = get_schema_statements()
    table_statements = [stmt for stmt in statements if "CREATE TABLE" in stmt.upper()]
    index_statements = [stmt for stmt in statements if "CREATE INDEX" in stmt.upper()]

    with connection:
        for statement in table_statements:
            connection.execute(statement)

    _run_compatibility_migrations(connection)

    with connection:
        for statement in index_statements:
            connection.execute(statement)

    return connection
