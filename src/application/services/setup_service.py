"""Servicio de configuración inicial y clave maestra."""

from __future__ import annotations

import sqlite3
from typing import Any

from src.infrastructure.persistence.repositories import ConfiguracionSistemaRepository
from src.shared.security import generar_salt, hash_clave, verificar_clave


class SetupService:
    """Orquesta la configuración inicial del sistema."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.repo = ConfiguracionSistemaRepository(connection)

    def obtener_estado_sistema(self) -> dict[str, Any]:
        """Retorna estado general de configuración."""
        configuracion = self.repo.obtener_por_id(1)
        if not configuracion:
            return {
                "primer_uso": True,
                "configurado": False,
                "tiene_clave_maestra": False,
            }

        return {
            "primer_uso": not bool(configuracion["primer_uso_completado"]),
            "configurado": bool(configuracion["primer_uso_completado"]),
            "tiene_clave_maestra": bool(configuracion.get("clave_inicial_hash") and configuracion.get("clave_inicial_salt")),
        }

    def es_primer_uso(self) -> bool:
        """Indica si el sistema aún no completó configuración inicial."""
        return self.obtener_estado_sistema()["primer_uso"]

    def configurar_sistema_inicial(self, clave_maestra: str) -> dict[str, Any]:
        """Configura por primera vez el sistema con clave maestra hasheada."""
        if not clave_maestra:
            raise ValueError("La clave maestra es obligatoria")

        existente = self.repo.obtener_por_id(1)
        if existente and int(existente["primer_uso_completado"]) == 1:
            return {"creado": False, "mensaje": "El sistema ya fue configurado"}

        salt = generar_salt()
        clave_hash = hash_clave(clave_maestra, salt)

        if existente:
            self.repo.actualizar(
                1,
                {
                    "clave_inicial_hash": clave_hash,
                    "clave_inicial_salt": salt,
                    "primer_uso_completado": 1,
                },
            )
        else:
            self.repo.crear(
                {
                    "id": 1,
                    "clave_inicial_hash": clave_hash,
                    "clave_inicial_salt": salt,
                    "primer_uso_completado": 1,
                    "escala_maxima": 10.0,
                    "escala_minima": 0.0,
                }
            )

        return {"creado": True, "mensaje": "Configuración inicial completada"}

    def validar_clave_maestra(self, clave_maestra: str) -> bool:
        """Valida clave maestra contra configuración persistida."""
        configuracion = self.repo.obtener_por_id(1)
        if not configuracion:
            return False

        if not configuracion.get("clave_inicial_hash") or not configuracion.get("clave_inicial_salt"):
            return False

        return verificar_clave(
            clave_plana=clave_maestra,
            salt_hex=configuracion.get("clave_inicial_salt", ""),
            hash_esperado=configuracion.get("clave_inicial_hash", ""),
        )
