"""Pruebas del arranque directo de UEEH V4 sin autenticación."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog

from src.application.services.catalog_service import CatalogService
from src.application.services.setup_service import SetupService
from src.infrastructure.persistence.db import initialize_database
from src.shared.security import generar_salt, hash_clave


EXPECTED_MAIN_WINDOW_SERVICES = {
    "institution_service",
    "teacher_service",
    "catalog_service",
    "student_service",
    "student_import_service",
    "enrollment_service",
    "teaching_assignment_service",
    "grade_registration_service",
    "academic_summary_service",
    "report_export_service",
    "backup_service",
    "classroom_accompaniment_service",
    "attendance_service",
    "setup_service",
}


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class _Signal:
    def connect(self, callback) -> None:
        self.callback = callback


class _FakeUpdateWorker:
    def __init__(self, _version: str) -> None:
        self.update_available = _Signal()

    def start(self) -> None:
        return None


def _patch_runtime(monkeypatch, db_path: Path, created_windows: list):
    from src import app as app_module
    from src.presentation.views import login_view as legacy_login_module
    from src.presentation.workers import email_worker as legacy_email_module
    from src.presentation.workers import update_worker as update_worker_module

    original_initialize = initialize_database

    class FakeMainWindow:
        def __init__(self, **services) -> None:
            self.services = services
            self.shown = False
            created_windows.append(self)

        def show(self) -> None:
            self.shown = True

    class ForbiddenLogin:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("V4 no debe crear LoginView")

    class ForbiddenEmailWorker:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("V4 no debe iniciar recuperación SMTP")

    def forbidden_authentication(*_args, **_kwargs):
        raise AssertionError("V4 no debe verificar ni recuperar una clave al iniciar")

    monkeypatch.setattr(
        app_module,
        "initialize_database",
        lambda _path=None: original_initialize(str(db_path)),
    )
    monkeypatch.setattr(app_module, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(app_module, "MainWindow", FakeMainWindow)
    monkeypatch.setattr(app_module, "install_global_interaction_support", lambda _app: None)
    monkeypatch.setattr(update_worker_module, "UpdateCheckWorker", _FakeUpdateWorker)
    monkeypatch.setattr(legacy_login_module, "LoginView", ForbiddenLogin)
    monkeypatch.setattr(legacy_email_module, "EmailSendWorker", ForbiddenEmailWorker)
    monkeypatch.setattr(SetupService, "validar_clave_maestra", forbidden_authentication)
    monkeypatch.setattr(SetupService, "get_recovery_email", forbidden_authentication)
    monkeypatch.setattr(SetupService, "save_recovery_email", forbidden_authentication)
    monkeypatch.setattr(SetupService, "recover_master_key", forbidden_authentication)
    for name in (
        "UEEH_SMTP_USER",
        "UEEH_SMTP_PASSWORD",
        "UEEH_SMTP_SERVER",
        "UEEH_SMTP_PORT",
        "UEEH_SMTP_SECURITY",
    ):
        monkeypatch.delenv(name, raising=False)

    assert not hasattr(app_module, "LoginView")
    return app_module


def _run_and_exit(app_module, qt_app) -> int:
    QTimer.singleShot(0, qt_app.quit)
    return app_module.run_application()


def test_existing_database_opens_directly_and_preserves_legacy_data(
    tmp_path,
    qt_app,
    monkeypatch,
) -> None:
    db_path = tmp_path / "existing-v4.db"
    connection = initialize_database(str(db_path))
    CatalogService(connection)
    salt = generar_salt()
    legacy_hash = hash_clave("Clave-Legada-Sintética", salt)
    with connection:
        connection.execute(
            """
            INSERT INTO configuracion_sistema (
                id, clave_inicial_hash, clave_inicial_salt,
                primer_uso_completado, escala_maxima, escala_minima,
                correo_recuperacion, licencia_activada, fecha_primer_inicio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (1, legacy_hash, salt, 1, 10.0, 0.0, "sintetico@example.test", 1, None),
        )
        connection.execute(
            """
            CREATE TABLE codigos_recuperacion (
                id INTEGER PRIMARY KEY,
                codigo_hash TEXT NOT NULL,
                codigo_salt TEXT NOT NULL,
                expira_en TEXT NOT NULL,
                intentos_restantes INTEGER NOT NULL,
                usado_en TEXT,
                creado_en TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO codigos_recuperacion VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (1, "hash-codigo-sintetico", "salt-codigo-sintetico", "2099-01-01T00:00:00+00:00", 5, None, "2026-01-01T00:00:00+00:00"),
        )
        connection.execute(
            """
            INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres, identificacion)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("EST-V4", "SINT-001", "Apellido Sintético", "Nombre Sintético", None),
        )
    connection.close()

    created_windows: list = []
    app_module = _patch_runtime(monkeypatch, db_path, created_windows)

    class ForbiddenSetup:
        Accepted = QDialog.Accepted

        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("Una base configurada no debe repetir el asistente")

    monkeypatch.setattr(app_module, "SetupView", ForbiddenSetup)
    application_before = QApplication.instance()

    assert _run_and_exit(app_module, qt_app) == 0
    assert _run_and_exit(app_module, qt_app) == 0

    verification = initialize_database(str(db_path))
    configuration = verification.execute(
        "SELECT clave_inicial_hash, clave_inicial_salt, correo_recuperacion "
        "FROM configuracion_sistema WHERE id = 1"
    ).fetchone()
    pending_code = verification.execute(
        "SELECT codigo_hash, codigo_salt, intentos_restantes, usado_en "
        "FROM codigos_recuperacion WHERE id = 1"
    ).fetchone()
    student = verification.execute(
        "SELECT codigo, apellidos, nombres FROM estudiantes WHERE id_estudiante = ?",
        ("EST-V4",),
    ).fetchone()
    verification.close()

    assert QApplication.instance() is application_before
    assert len(created_windows) == 2
    assert all(window.shown for window in created_windows)
    assert all(set(window.services) == EXPECTED_MAIN_WINDOW_SERVICES for window in created_windows)
    assert tuple(configuration) == (legacy_hash, salt, "sintetico@example.test")
    assert tuple(pending_code) == (
        "hash-codigo-sintetico",
        "salt-codigo-sintetico",
        5,
        None,
    )
    assert tuple(student) == ("SINT-001", "Apellido Sintético", "Nombre Sintético")


def test_new_installation_reaches_main_window_without_credentials(
    tmp_path,
    qt_app,
    monkeypatch,
) -> None:
    db_path = tmp_path / "new-v4.db"
    created_windows: list = []
    app_module = _patch_runtime(monkeypatch, db_path, created_windows)

    class CompletingSetup:
        Accepted = QDialog.Accepted

        def __init__(self, setup_service, institution_service) -> None:
            self.setup_service = setup_service
            self.institution_service = institution_service

        def exec(self) -> int:
            self.setup_service.configurar_sistema_inicial()
            self.institution_service.crear_o_actualizar(
                nombre="INSTITUCIÓN SINTÉTICA V4",
                jornada="Por definir",
            )
            return self.Accepted

    monkeypatch.setattr(app_module, "SetupView", CompletingSetup)
    monkeypatch.setattr(SetupService, "is_licensed", lambda _self: True)
    application_before = QApplication.instance()

    assert _run_and_exit(app_module, qt_app) == 0
    assert _run_and_exit(app_module, qt_app) == 0

    verification = initialize_database(str(db_path))
    configuration = verification.execute(
        "SELECT clave_inicial_hash, clave_inicial_salt, correo_recuperacion, "
        "primer_uso_completado FROM configuracion_sistema WHERE id = 1"
    ).fetchone()
    institution = verification.execute(
        "SELECT nombre FROM institucion WHERE id_institucion = ?",
        ("INST_ACTIVA",),
    ).fetchone()
    verification.close()

    assert QApplication.instance() is application_before
    assert len(created_windows) == 2
    assert all(window.shown for window in created_windows)
    assert all(set(window.services) == EXPECTED_MAIN_WINDOW_SERVICES for window in created_windows)
    assert tuple(configuration) == (None, None, None, 1)
    assert institution["nombre"] == "INSTITUCIÓN SINTÉTICA V4"
