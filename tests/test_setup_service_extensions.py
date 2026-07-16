"""Pruebas unitarias para las extensiones de seguridad de SetupService (Licencias y Recuperación)."""

from __future__ import annotations

import sqlite3
import pytest

from src.infrastructure.persistence.db import initialize_database
from src.application.services.setup_service import SetupService


@pytest.fixture
def db_conn():
    """Inicializa una base de datos SQLite en memoria para cada prueba."""
    conn = initialize_database(":memory:")
    yield conn
    conn.close()


def test_license_activation(db_conn):
    """Prueba que el sistema reconozca la clave de licencia correcta e ignore las inválidas."""
    setup_service = SetupService(db_conn)
    setup_service.configurar_sistema_inicial("clave123")

    # Inicia sin licencia activa
    assert setup_service.is_licensed() is False

    # Clave de licencia errónea
    assert setup_service.activate_license("clave-erronea-123") is False
    assert setup_service.is_licensed() is False

    # Clave de licencia correcta (Base64 provista por el prompt)
    valid_key = "eyJjbGllbnQiOiJVRUVIIiwiZXhwaXJlcyI6Im5ldmVyIiwic2lnbmF0dXJlIjoiNzE4Y2E2MDc2MDA4ZTA0Mzc0YTE1M2YyMzdiNzJhYjgwMjcyYTIzMWRlYTQ0YTYwNDA2MDhhNTk3Y2M1OTU2NCJ9"
    assert setup_service.activate_license(valid_key) is True
    assert setup_service.is_licensed() is True


def test_trial_period_counting(db_conn):
    """Prueba el registro y conteo de días en el período de prueba de 30 días."""
    setup_service = SetupService(db_conn)
    setup_service.configurar_sistema_inicial("clave123")

    # El primer conteo debe inicializar el período a 30 días
    assert setup_service.get_trial_days_remaining() == 30

    # Simular que transcurrieron 10 días forzando el registro en la DB
    from datetime import datetime, timedelta
    fecha_hace_10_dias = (datetime.now().date() - timedelta(days=10)).isoformat()
    setup_service.repo.actualizar(1, {"fecha_primer_inicio": fecha_hace_10_dias})

    # Deben restar 20 días
    assert setup_service.get_trial_days_remaining() == 20

    # Simular expiración de prueba (transcurridos 35 días)
    fecha_hace_35_dias = (datetime.now().date() - timedelta(days=35)).isoformat()
    setup_service.repo.actualizar(1, {"fecha_primer_inicio": fecha_hace_35_dias})

    # Restan 0 días (no negativos) y expira
    assert setup_service.get_trial_days_remaining() == 0


def test_recovery_email_registration(db_conn):
    """Prueba el registro, guardado y recuperación de correos electrónicos."""
    setup_service = SetupService(db_conn)
    setup_service.configurar_sistema_inicial("clave123")

    # Inicialmente está vacío
    assert setup_service.get_recovery_email() is None

    # Guardar correo
    test_email = "docente-soporte@ueeh.edu.ec"
    setup_service.save_recovery_email(test_email)
    assert setup_service.get_recovery_email() == test_email


def test_master_key_recovery_reset(db_conn):
    """Prueba que el reseteo genere una clave temporal y cambie la validez de la clave anterior."""
    setup_service = SetupService(db_conn)
    setup_service.configurar_sistema_inicial("claveOriginal")

    # Guardamos correo
    setup_service.save_recovery_email("docente@ueeh.edu.ec")

    # Validamos que la clave vieja funciona antes del reseteo
    assert setup_service.validar_clave_maestra("claveOriginal") is True

    # Realizar recuperación
    ok, nueva_clave = setup_service.recover_master_key()
    assert ok is True
    assert len(nueva_clave) == 8
    assert nueva_clave != "claveOriginal"

    # La clave original ya no debe ser válida
    assert setup_service.validar_clave_maestra("claveOriginal") is False

    # La nueva clave temporal debe ser perfectamente válida
    assert setup_service.validar_clave_maestra(nueva_clave) is True
