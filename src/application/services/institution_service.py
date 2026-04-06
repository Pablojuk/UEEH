"""Servicio de negocio para datos institucionales."""

from __future__ import annotations

import sqlite3

from src.infrastructure.persistence.repositories import InstitucionRepository


class InstitutionService:
    """Gestiona una sola institución activa en el sistema."""

    INSTITUCION_ACTIVA_ID = "INST_ACTIVA"

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.repo = InstitucionRepository(connection)

    def crear_o_actualizar(self, nombre: str, jornada: str, logo_path: str | None = None) -> None:
        existente = self.repo.obtener_por_id(self.INSTITUCION_ACTIVA_ID)
        data = {
            "id_institucion": self.INSTITUCION_ACTIVA_ID,
            "nombre": nombre,
            "jornada": jornada,
            "logo_path": logo_path if logo_path is not None else (existente.get("logo_path") if existente else None),
        }
        if existente:
            self.repo.actualizar(self.INSTITUCION_ACTIVA_ID, data)
        else:
            self.repo.crear(data)

    def obtener_actual(self) -> dict | None:
        return self.repo.obtener_por_id(self.INSTITUCION_ACTIVA_ID)

    def actualizar_logo(self, logo_path: str | None) -> None:
        existente = self.repo.obtener_por_id(self.INSTITUCION_ACTIVA_ID)
        if not existente:
            data = {
                "id_institucion": self.INSTITUCION_ACTIVA_ID,
                "nombre": "Institución no configurada",
                "jornada": "Por definir",
                "logo_path": logo_path,
            }
            self.repo.crear(data)
            return
        self.repo.actualizar(self.INSTITUCION_ACTIVA_ID, {"logo_path": logo_path})
