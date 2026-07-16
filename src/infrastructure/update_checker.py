"""Servicio para comprobar y descargar actualizaciones desde GitHub Releases."""

from __future__ import annotations

import json
import re
import hashlib
import os
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# ==============================================================================
# CONFIGURACIÓN DEL REPOSITORIO
# Modifique estas variables para apuntar a su repositorio de GitHub:
# ==============================================================================
GITHUB_REPO_OWNER = "Pablojuk"
GITHUB_REPO_NAME = "UEEH"
# ==============================================================================


class SecurityError(ValueError):
    """Excepción para errores de seguridad crítica en el actualizador."""
    pass


@dataclass
class ReleaseInfo:
    tag_name: str
    release_notes: str
    download_url: str | None
    html_url: str
    expected_hash: str | None = None


class UpdateChecker:
    """Clase encargada de consultar la API de GitHub y gestionar las descargas."""

    def __init__(self, owner: str = GITHUB_REPO_OWNER, repo: str = GITHUB_REPO_NAME) -> None:
        self.owner = owner
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    def check_latest(self) -> ReleaseInfo | None:
        """Consulta la API de GitHub para obtener la última release publicada.

        Retorna ReleaseInfo si tiene éxito, o None si ocurre un error de red o no hay releases.
        """
        req = urllib.request.Request(
            self.api_url,
            headers={
                "User-Agent": "UEEH-OTA-Updater",
                "Accept": "application/vnd.github+json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

                tag_name = data.get("tag_name", "")
                body = data.get("body", "")
                html_url = data.get("html_url", "")

                # Extraer el hash SHA-256 esperado del cuerpo (ej. SHA256: HASH)
                hash_match = re.search(r"(?i)sha256:\s*([a-fA-F0-9]{64})", body)
                expected_hash = hash_match.group(1).lower() if hash_match else None

                # Buscar el asset que corresponde a un ejecutable (.exe)
                download_url = None
                assets = data.get("assets", [])
                for asset in assets:
                    name = asset.get("name", "")
                    if name.lower().endswith(".exe"):
                        download_url = asset.get("browser_download_url")
                        break

                return ReleaseInfo(
                    tag_name=tag_name,
                    release_notes=body,
                    download_url=download_url,
                    html_url=html_url,
                    expected_hash=expected_hash
                )

        except urllib.error.URLError:
            # Error de red (sin internet o servidor inaccesible)
            return None
        except (json.JSONDecodeError, KeyError, ValueError):
            # Error al procesar respuesta
            return None
        except Exception:
            # Cualquier otra excepción inesperada
            return None

    @staticmethod
    def parse_version(version_str: str) -> list[int]:
        """Normaliza y convierte una cadena de versión a una lista de enteros.

        Ejemplos: "v1.2.0" -> [1, 2, 0], "2.3.4-beta" -> [2, 3, 4]
        """
        # Eliminar prefijo 'v' si existe
        clean_str = version_str.strip().lower()
        if clean_str.startswith("v"):
            clean_str = clean_str[1:]

        # Dividir por caracteres no numéricos o simplemente limpiar sufijos comunes
        # Para mantenerlo simple y libre de dependencias complejas, separamos por puntos
        # y filtramos la parte numérica de cada bloque
        parts = clean_str.split("-")[0].split(".")
        result = []
        for p in parts:
            # Extraer solo dígitos de cada sección
            digits = "".join(char for char in p if char.isdigit())
            if digits:
                result.append(int(digits))
            else:
                result.append(0)

        # Rellenar con ceros si tiene menos de 3 componentes
        while len(result) < 3:
            result.append(0)

        return result[:3]

    def is_update_available(self, current_version: str, latest_version: str) -> bool:
        """Compara la versión local con la versión remota.

        Retorna True si la versión remota es estrictamente superior a la local.
        """
        try:
            curr_parts = self.parse_version(current_version)
            late_parts = self.parse_version(latest_version)
            return late_parts > curr_parts
        except Exception:
            return False

    def download_asset(
        self,
        url: str,
        dest_path: Path,
        expected_hash: str | None = None,
        progress_callback: Callable[[int], None] | None = None
    ) -> Path:
        """Descarga el asset desde la URL especificada hacia el destino local.

        Informa del progreso (0 a 100) llamando a progress_callback.
        Valida que el SHA-256 del archivo coincida con el hash esperado.
        """
        # Forzar HTTPS y validación estricta de SSL
        if not url.lower().startswith("https://"):
            raise SecurityError("Error de seguridad: solo se permiten descargas a través de conexiones seguras (HTTPS).")

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "UEEH-OTA-Updater"}
        )

        with urllib.request.urlopen(req) as response:
            total_size = int(response.headers.get("content-length", 0))
            chunk_size = 1024 * 64  # 64 KB
            bytes_downloaded = 0

            # Crear directorios padres si no existen
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_downloaded += len(chunk)

                    if total_size > 0 and progress_callback:
                        pct = int((bytes_downloaded / total_size) * 100)
                        progress_callback(min(100, pct))

            # Asegurar progreso final al 100%
            if progress_callback:
                progress_callback(100)

        # Validación criptográfica SHA-256 obligatoria (DevSecOps Hardening)
        if not expected_hash:
            if dest_path.exists():
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
            raise ValueError(
                "Error de seguridad crítico: No se encontró la firma hash SHA-256 en las notas del release.\n"
                "Se aborta la instalación para prevenir posibles ataques a la cadena de suministro."
            )

        # Calcular hash del archivo descargado
        sha256_hash = hashlib.sha256()
        with open(dest_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        calculated_hash = sha256_hash.hexdigest().lower()

        if calculated_hash != expected_hash.strip().lower():
            if dest_path.exists():
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
            raise ValueError(
                "¡Alerta crítica de seguridad! El hash SHA-256 del archivo descargado no coincide con el publicado.\n"
                "La descarga ha sido eliminada por sospecha de alteración o malware (Man-in-the-Middle)."
            )

        return dest_path
