"""Semillas iniciales para base de datos de BLOQUE 2."""

from __future__ import annotations

import sqlite3

from .repositories import ConfiguracionSistemaRepository


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
