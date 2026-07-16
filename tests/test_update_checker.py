"""Pruebas unitarias para el servicio de actualizaciones OTA."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

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
        "body": "Novedades de la versión:\n- Bug fixes\n- Nueva UI",
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
    """Prueba la descarga simulada de un asset y la invocación del callback de progreso."""
    # Datos simulados de descarga (100 bytes)
    dummy_data = b"x" * 100

    mock_response = MagicMock()
    mock_response.headers = {"content-length": "100"}
    
    # Simular lectura parcial
    # Retorna 50 bytes primero, luego otros 50, luego nada
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
        progress_callback=progress_callback
    )

    # Verificar que el archivo se guardó
    assert dest_file.exists()
    assert dest_file.read_bytes() == dummy_data

    # Verificar que se reportó el progreso y terminó en 100
    assert len(progress_ticks) > 0
    assert progress_ticks[-1] == 100
