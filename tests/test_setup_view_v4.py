"""Pruebas de la configuración inicial sin autenticación en V4."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QDialog, QLabel, QMessageBox

from src.application.services.institution_service import InstitutionService
from src.application.services.setup_service import SetupService
from src.infrastructure.persistence.db import initialize_database
from src.presentation.views.setup_view import SetupView


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_setup_view_only_requests_institution(qt_app) -> None:
    connection = initialize_database(":memory:")
    view = SetupView(SetupService(connection), InstitutionService(connection))
    visible_text = " ".join(label.text().lower() for label in view.findChildren(QLabel))

    assert not hasattr(view, "password_input")
    assert not hasattr(view, "password_confirm_input")
    assert not hasattr(view, "email_input")
    assert "clave maestra" not in visible_text
    assert "correo" not in visible_text
    connection.close()


def test_new_installation_completes_without_password_or_email(qt_app, monkeypatch) -> None:
    connection = initialize_database(":memory:")
    setup_service = SetupService(connection)
    institution_service = InstitutionService(connection)
    view = SetupView(setup_service, institution_service)
    monkeypatch.setattr(QMessageBox, "information", lambda *_args, **_kwargs: None)
    view.institution_input.setText("INSTITUCIÓN SINTÉTICA V4")

    view._on_save()

    configuration = connection.execute(
        "SELECT clave_inicial_hash, clave_inicial_salt, correo_recuperacion, "
        "primer_uso_completado FROM configuracion_sistema WHERE id = 1"
    ).fetchone()
    institution = institution_service.obtener_actual()
    assert view.result() == QDialog.Accepted
    assert tuple(configuration) == (None, None, None, 1)
    assert institution["nombre"] == "INSTITUCIÓN SINTÉTICA V4"
    connection.close()
