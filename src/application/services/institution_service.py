"""Servicio de negocio para datos institucionales."""

from __future__ import annotations

import sqlite3

from src.infrastructure.persistence.repositories import InstitucionRepository


class InstitutionService:
    """Gestiona una sola institución activa en el sistema."""

    INSTITUCION_ACTIVA_ID = "INST_ACTIVA"

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.repo = InstitucionRepository(connection)

    def crear_o_actualizar(self, nombre: str, jornada: str) -> None:
        data = {
            "id_institucion": self.INSTITUCION_ACTIVA_ID,
            "nombre": nombre,
            "jornada": jornada,
        }
        existente = self.repo.obtener_por_id(self.INSTITUCION_ACTIVA_ID)
        if existente:
            self.repo.actualizar(self.INSTITUCION_ACTIVA_ID, data)
        else:
            self.repo.crear(data)

    def obtener_actual(self) -> dict | None:
        return self.repo.obtener_por_id(self.INSTITUCION_ACTIVA_ID)
