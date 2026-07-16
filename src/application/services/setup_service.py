"""Servicio de configuración inicial y clave maestra."""

from __future__ import annotations

import sqlite3
import secrets
import string
from datetime import datetime
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

    def configurar_sistema_inicial(self) -> dict[str, Any]:
        """Marca la configuración inicial como completa sin crear credenciales."""
        existente = self.repo.obtener_por_id(1)
        if existente and int(existente["primer_uso_completado"]) == 1:
            return {"creado": False, "mensaje": "El sistema ya fue configurado"}

        if existente:
            self.repo.actualizar(
                1,
                {
                    "primer_uso_completado": 1,
                },
            )
        else:
            self.repo.crear(
                {
                    "id": 1,
                    "clave_inicial_hash": None,
                    "clave_inicial_salt": None,
                    "primer_uso_completado": 1,
                    "escala_maxima": 10.0,
                    "escala_minima": 0.0,
                    "correo_recuperacion": None,
                    "licencia_activada": 0,
                    "fecha_primer_inicio": None,
                }
            )

        return {"creado": True, "mensaje": "Configuración inicial completada"}

    def validar_clave_maestra(self, clave_maestra: str) -> bool:
        """Compatibilidad heredada; V4 no invoca este método para acceder."""
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

    def is_licensed(self) -> bool:
        """Indica si el sistema está activado permanentemente."""
        configuracion = self.repo.obtener_por_id(1)
        if not configuracion:
            return False
        return bool(configuracion.get("licencia_activada", 0))

    def activate_license(self, license_key: str) -> bool:
        """Compara la clave ingresada y activa permanentemente la licencia si es correcta."""
        clean_key = license_key.strip()
        expected = "eyJjbGllbnQiOiJVRUVIIiwiZXhwaXJlcyI6Im5ldmVyIiwic2lnbmF0dXJlIjoiNzE4Y2E2MDc2MDA4ZTA0Mzc0YTE1M2YyMzdiNzJhYjgwMjcyYTIzMWRlYTQ0YTYwNDA2MDhhNTk3Y2M159u64"
        # Permitir tanto la cadena corta truncada por el prompt o la firma exacta para evitar problemas si se recorta
        expected_full = "eyJjbGllbnQiOiJVRUVIIiwiZXhwaXJlcyI6Im5ldmVyIiwic2lnbmF0dXJlIjoiNzE4Y2E2MDc2MDA4ZTA0Mzc0YTE1M2YyMzdiNzJhYjgwMjcyYTIzMWRlYTQ0YTYwNDA2MDhhNTk3Y2M1OTU2NCJ9"
        if clean_key == expected_full or clean_key == expected:
            self.repo.actualizar(1, {"licencia_activada": 1})
            return True
        return False

    def get_trial_days_remaining(self) -> int:
        """Calcula y retorna los días restantes del período de prueba.

        Si no se ha registrado la fecha de primer inicio, la registra hoy.
        """
        configuracion = self.repo.obtener_por_id(1)
        if not configuracion:
            return 0

        primer_inicio_str = configuracion.get("fecha_primer_inicio")
        hoy = datetime.now().date()

        if not primer_inicio_str:
            primer_inicio_str = hoy.isoformat()
            self.repo.actualizar(1, {"fecha_primer_inicio": primer_inicio_str})
            return 30

        try:
            fecha_inicio = datetime.fromisoformat(primer_inicio_str).date()
            dias_transcurridos = (hoy - fecha_inicio).days
            return max(0, 30 - dias_transcurridos)
        except Exception:
            # En caso de error de parseo, reiniciar la fecha de inicio por seguridad
            self.repo.actualizar(1, {"fecha_primer_inicio": hoy.isoformat()})
            return 30

    def get_recovery_email(self) -> str | None:
        """Compatibilidad heredada con configuraciones anteriores a V4."""
        configuracion = self.repo.obtener_por_id(1)
        if not configuracion:
            return None
        return configuracion.get("correo_recuperacion")

    def save_recovery_email(self, email: str) -> None:
        """Compatibilidad heredada; no se expone en la interfaz de V4."""
        self.repo.actualizar(1, {"correo_recuperacion": email.strip()})

    def recover_master_key(self) -> tuple[bool, str]:
        """Compatibilidad heredada; V4 no invoca recuperación para acceder.

        Retorna (True, nueva_clave_plana) en caso de éxito.
        """
        configuracion = self.repo.obtener_por_id(1)
        if not configuracion:
            return False, "Sistema no configurado"

        caracteres = string.ascii_letters + string.digits
        nueva_clave = "".join(secrets.choice(caracteres) for _ in range(8))

        salt = generar_salt()
        clave_hash = hash_clave(nueva_clave, salt)

        self.repo.actualizar(
            1,
            {
                "clave_inicial_hash": clave_hash,
                "clave_inicial_salt": salt
            }
        )
        return True, nueva_clave
