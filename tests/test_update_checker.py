"""Pruebas unitarias para el servicio de actualizaciones OTA."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error
import hashlib

import pytest

from src.infrastructure.update_checker import ReleaseInfo, UpdateChecker


def test_parse_version():
    """Prueba la conversión de cadenas de versión a listas numéricas."""
    assert UpdateChecker.parse_version("1.0.0") == [1, 0, 0]
    assert UpdateChecker.parse_version("v1.2.3") == [1, 2, 3]
    assert UpdateChecker.parse_version("v2.1") == [2, 1, 0]
    assert UpdateChecker.parse_version("3") == [3, 0, 0]
    assert UpdateChecker.parse_version("1.0.0-beta") == [1, 0, 0]
    assert UpdateChecker.parse_version("  v2.5.6-rc1  ") == [2, 5, 6]
    assert UpdateChecker.parse_version("invalida") == [0, 0, 0]


def test_is_update_available():
    """Prueba la lógica de comparación para identificar actualizaciones disponibles."""
    checker = UpdateChecker()

    # Remota mayor que local
    assert checker.is_update_available("1.0.0", "1.1.0") is True
    assert checker.is_update_available("1.0.0", "v2.0.0") is True
    assert checker.is_update_available("v1.2.3", "1.2.4") is True
    assert checker.is_update_available("0.9.0", "1.0.0-beta") is True

    # Remota igual a local
    assert checker.is_update_available("1.0.0", "1.0.0") is False
    assert checker.is_update_available("v1.2.3", "1.2.3") is False

    # Remota menor que local
    assert checker.is_update_available("1.1.0", "1.0.0") is False
    assert checker.is_update_available("2.0.0", "v1.5.0") is False


@patch("urllib.request.urlopen")
def test_check_latest_success(mock_urlopen):
    """Prueba la obtención exitosa de los datos de la última versión usando mocks."""
    mock_response_data = {
        "tag_name": "v1.1.0",
        "body": "Novedades de la versión:\n- Bug fixes\n- Nueva UI\n\nSHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "html_url": "https://github.com/Pablojuk/UEEH/releases/tag/v1.1.0",
        "assets": [
            {
                "name": "UEEH_Installer.exe",
                "browser_download_url": "https://github.com/Pablojuk/UEEH/releases/download/v1.1.0/UEEH_Installer.exe"
            },
            {
                "name": "source.zip",
                "browser_download_url": "https://github.com/Pablojuk/UEEH/archive/refs/tags/v1.1.0.zip"
            }
        ]
    }

    # Configurar el mock para que devuelva un objeto similar a una respuesta HTTP
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    checker = UpdateChecker(owner="mock_owner", repo="mock_repo")
    info = checker.check_latest()

    assert info is not None
    assert info.tag_name == "v1.1.0"
    assert "Bug fixes" in info.release_notes
    assert info.download_url == "https://github.com/Pablojuk/UEEH/releases/download/v1.1.0/UEEH_Installer.exe"
    assert info.html_url == "https://github.com/Pablojuk/UEEH/releases/tag/v1.1.0"
    assert info.expected_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@patch("urllib.request.urlopen")
def test_check_latest_no_exe_asset(mock_urlopen):
    """Prueba qué pasa si la release no contiene ningún archivo ejecutable .exe."""
    mock_response_data = {
        "tag_name": "v1.1.0",
        "body": "Release sin ejecutable",
        "html_url": "https://github.com/Pablojuk/UEEH/releases/tag/v1.1.0",
        "assets": [
            {
                "name": "source.zip",
                "browser_download_url": "https://github.com/Pablojuk/UEEH/archive/refs/tags/v1.1.0.zip"
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    checker = UpdateChecker()
    info = checker.check_latest()

    assert info is not None
    assert info.tag_name == "v1.1.0"
    assert info.download_url is None  # No hay asset .exe
    assert info.html_url == "https://github.com/Pablojuk/UEEH/releases/tag/v1.1.0"


@patch("urllib.request.urlopen")
def test_check_latest_network_error(mock_urlopen):
    """Prueba el comportamiento del actualizador ante un error de red."""
    # Hacer que urlopen lance una excepción de red
    mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

    checker = UpdateChecker()
    info = checker.check_latest()

    assert info is None  # Debe manejar la excepción internamente y retornar None


@patch("urllib.request.urlopen")
def test_download_asset(mock_urlopen, tmp_path):
    """Prueba la descarga simulada de un asset con verificación exitosa de hash."""
    dummy_data = b"x" * 100
    expected_hash = hashlib.sha256(dummy_data).hexdigest()

    mock_response = MagicMock()
    mock_response.headers = {"content-length": "100"}
    mock_response.read.side_effect = [dummy_data[:50], dummy_data[50:], b""]
    mock_urlopen.return_value.__enter__.return_value = mock_response

    checker = UpdateChecker()
    dest_file = tmp_path / "descarga_test.exe"

    progress_ticks = []
    def progress_callback(pct: int):
        progress_ticks.append(pct)

    checker.download_asset(
        url="https://github.com/dummy/installer.exe",
        dest_path=dest_file,
        expected_hash=expected_hash,
        progress_callback=progress_callback
    )

    assert dest_file.exists()
    assert dest_file.read_bytes() == dummy_data
    assert len(progress_ticks) > 0
    assert progress_ticks[-1] == 100


@patch("urllib.request.urlopen")
def test_download_asset_invalid_hash(mock_urlopen, tmp_path):
    """Prueba que el actualizador rechaza descargas con hash incorrecto y elimina el archivo."""
    dummy_data = b"incorrect_payload"
    bad_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    mock_response = MagicMock()
    mock_response.headers = {"content-length": "17"}
    mock_response.read.side_effect = [dummy_data, b""]
    mock_urlopen.return_value.__enter__.return_value = mock_response

    checker = UpdateChecker()
    dest_file = tmp_path / "unsafe_installer.exe"

    with pytest.raises(ValueError) as excinfo:
        checker.download_asset(
            url="https://github.com/dummy/unsafe.exe",
            dest_path=dest_file,
            expected_hash=bad_hash
        )

    assert "no coincide con el publicado" in str(excinfo.value)
    # El archivo descargado debe haber sido eliminado inmediatamente por seguridad
    assert not dest_file.exists()


@patch("urllib.request.urlopen")
def test_download_asset_missing_hash(mock_urlopen, tmp_path):
    """Prueba que el actualizador rechaza la instalación si no se declaró un hash en el release."""
    dummy_data = b"some_data"

    mock_response = MagicMock()
    mock_response.headers = {"content-length": "9"}
    mock_response.read.side_effect = [dummy_data, b""]
    mock_urlopen.return_value.__enter__.return_value = mock_response

    checker = UpdateChecker()
    dest_file = tmp_path / "unverified_installer.exe"

    with pytest.raises(ValueError) as excinfo:
        checker.download_asset(
            url="https://github.com/dummy/unverified.exe",
            dest_path=dest_file,
            expected_hash=None
        )

    assert "No se encontró la firma hash SHA-256" in str(excinfo.value)
    assert not dest_file.exists()


def test_download_asset_non_https(tmp_path):
    """Prueba que el actualizador bloquea de forma inmediata descargas que no usen HTTPS."""
    from src.infrastructure.update_checker import SecurityError
    
    checker = UpdateChecker()
    dest_file = tmp_path / "insecure.exe"

    with pytest.raises(SecurityError) as excinfo:
        checker.download_asset(
            url="http://insecure-connection.com/malicious.exe",
            dest_path=dest_file,
            expected_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    assert "solo se permiten descargas a través de conexiones seguras (HTTPS)" in str(excinfo.value)
    assert not dest_file.exists()
