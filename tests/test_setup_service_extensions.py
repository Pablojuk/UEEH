"""Pruebas de licencia y ausencia de recuperación activa en V4."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.application.services.setup_service import SetupService
from src.infrastructure.persistence.db import initialize_database


@pytest.fixture
def db_conn():
    connection = initialize_database(":memory:")
    yield connection
    connection.close()


def test_license_activation(db_conn) -> None:
    setup_service = SetupService(db_conn)
    setup_service.configurar_sistema_inicial()

    assert setup_service.is_licensed() is False
    assert setup_service.activate_license("clave-licencia-incorrecta-sintetica") is False
    assert setup_service.is_licensed() is False

    valid_key = "eyJjbGllbnQiOiJVRUVIIiwiZXhwaXJlcyI6Im5ldmVyIiwic2lnbmF0dXJlIjoiNzE4Y2E2MDc2MDA4ZTA0Mzc0YTE1M2YyMzdiNzJhYjgwMjcyYTIzMWRlYTQ0YTYwNDA2MDhhNTk3Y2M1OTU2NCJ9"
    assert setup_service.activate_license(valid_key) is True
    assert setup_service.is_licensed() is True


def test_trial_period_counting(db_conn) -> None:
    setup_service = SetupService(db_conn)
    setup_service.configurar_sistema_inicial()

    assert setup_service.get_trial_days_remaining() == 30

    ten_days_ago = (datetime.now().date() - timedelta(days=10)).isoformat()
    setup_service.repo.actualizar(1, {"fecha_primer_inicio": ten_days_ago})
    assert setup_service.get_trial_days_remaining() == 20

    thirty_five_days_ago = (datetime.now().date() - timedelta(days=35)).isoformat()
    setup_service.repo.actualizar(1, {"fecha_primer_inicio": thirty_five_days_ago})
    assert setup_service.get_trial_days_remaining() == 0


def test_initial_configuration_does_not_invoke_recovery(monkeypatch, db_conn) -> None:
    setup_service = SetupService(db_conn)

    def unexpected_call(*_args, **_kwargs):
        raise AssertionError("La configuración V4 no debe invocar recuperación")

    monkeypatch.setattr(setup_service, "recover_master_key", unexpected_call)
    monkeypatch.setattr(setup_service, "save_recovery_email", unexpected_call)

    result = setup_service.configurar_sistema_inicial()

    assert result["creado"] is True
    assert setup_service.get_recovery_email() is None


def test_legacy_recovery_email_is_not_modified_by_v4_configuration(db_conn) -> None:
    with db_conn:
        db_conn.execute(
            """
            INSERT INTO configuracion_sistema (
                id, clave_inicial_hash, clave_inicial_salt,
                primer_uso_completado, escala_maxima, escala_minima,
                correo_recuperacion, licencia_activada, fecha_primer_inicio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (1, "hash-legado", "salt-legado", 0, 10.0, 0.0, "sintetico@example.test", 0, None),
        )
    setup_service = SetupService(db_conn)

    setup_service.configurar_sistema_inicial()

    row = db_conn.execute(
        "SELECT clave_inicial_hash, clave_inicial_salt, correo_recuperacion "
        "FROM configuracion_sistema WHERE id = 1"
    ).fetchone()
    assert tuple(row) == ("hash-legado", "salt-legado", "sintetico@example.test")
