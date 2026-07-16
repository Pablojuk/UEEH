"""Servicio de negocio para datos institucionales."""

from __future__ import annotations

import sqlite3

from src.infrastructure.persistence.repositories import InstitucionRepository


class InstitutionService:
    """Gestiona una sola institución activa en el sistema."""

    INSTITUCION_ACTIVA_ID = "INST_ACTIVA"

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.repo = InstitucionRepository(connection)

    def crear_o_actualizar(self, nombre: str, jornada: str, logo_path: str | None = None, **extra_fields: str | None) -> None:
        existente = self.repo.obtener_por_id(self.INSTITUCION_ACTIVA_ID)
        data = {
            "id_institucion": self.INSTITUCION_ACTIVA_ID,
            "nombre": nombre,
            "jornada": jornada,
            "provincia": extra_fields.get("provincia") if extra_fields.get("provincia") is not None else (existente or {}).get("provincia"),
            "ciudad": extra_fields.get("ciudad") if extra_fields.get("ciudad") is not None else (existente or {}).get("ciudad"),
            "parroquia": extra_fields.get("parroquia") if extra_fields.get("parroquia") is not None else (existente or {}).get("parroquia"),
            "direccion": extra_fields.get("direccion") if extra_fields.get("direccion") is not None else (existente or {}).get("direccion"),
            "codigo_amie": extra_fields.get("codigo_amie") if extra_fields.get("codigo_amie") is not None else (existente or {}).get("codigo_amie"),
            "rector": extra_fields.get("rector") if extra_fields.get("rector") is not None else (existente or {}).get("rector"),
            "vicerrector": extra_fields.get("vicerrector") if extra_fields.get("vicerrector") is not None else (existente or {}).get("vicerrector"),
            "inspector": extra_fields.get("inspector") if extra_fields.get("inspector") is not None else (existente or {}).get("inspector"),
            "logo_ministerio_path": extra_fields.get("logo_ministerio_path")
            if extra_fields.get("logo_ministerio_path") is not None
            else (existente or {}).get("logo_ministerio_path"),
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

    def actualizar_logos(self, logo_ministerio_path: str | None, logo_institucional_path: str | None) -> None:
        existente = self.repo.obtener_por_id(self.INSTITUCION_ACTIVA_ID)
        if not existente:
            self.repo.crear(
                {
                    "id_institucion": self.INSTITUCION_ACTIVA_ID,
                    "nombre": "Institución no configurada",
                    "jornada": "Por definir",
                    "provincia": None,
                    "ciudad": None,
                    "parroquia": None,
                    "direccion": None,
                    "codigo_amie": None,
                    "rector": None,
                    "vicerrector": None,
                    "inspector": None,
                    "logo_ministerio_path": logo_ministerio_path,
                    "logo_path": logo_institucional_path,
                }
            )
            return
        self.repo.actualizar(
            self.INSTITUCION_ACTIVA_ID,
            {"logo_ministerio_path": logo_ministerio_path, "logo_path": logo_institucional_path},
        )
