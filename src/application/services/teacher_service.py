"""Servicio de negocio para gestión de docentes."""

from __future__ import annotations

import sqlite3

from src.infrastructure.persistence.repositories import DocentesRepository


class TeacherService:
    """Gestiona operaciones de docentes."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.repo = DocentesRepository(connection)

    def crear_docente(self, data: dict) -> None:
        payload = {
            "id_docente": data["id_docente"],
            "nombres": data["nombres"],
            "apellidos": data["apellidos"],
            "identificacion": data["identificacion"],
            "activo": data.get("activo", 1),
        }
        self.repo.crear(payload)

    def obtener_docente(self, id_docente: str) -> dict | None:
        return self.repo.obtener_por_id(id_docente)

    def listar_docentes(self) -> list[dict]:
        return self.repo.listar()

    def actualizar_docente(self, id_docente: str, data: dict) -> None:
        self.repo.actualizar(id_docente, data)

    def activar_docente(self, id_docente: str) -> None:
        self.repo.actualizar(id_docente, {"activo": 1})

    def inactivar_docente(self, id_docente: str) -> None:
        self.repo.actualizar(id_docente, {"activo": 0})
