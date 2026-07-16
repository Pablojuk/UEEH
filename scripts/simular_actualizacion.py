"""Script de prueba para simular visualmente el flujo de actualización de la app.

Este script parchea (monkeypatch) el servicio UpdateChecker para simular
la disponibilidad de una nueva versión (v2.0.0) y ejecuta la aplicación completa.

USO:
    python scripts/simular_actualizacion.py
"""

import sys
from pathlib import Path

# Añadir la raíz del repositorio al PYTHONPATH
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Realizar monkeypatch ANTES de importar o iniciar la aplicación
from src.infrastructure.update_checker import UpdateChecker, ReleaseInfo

# 1. Simulación de la respuesta de la API de GitHub
def mock_check_latest(self) -> ReleaseInfo | None:
    print("[MOCK] Simulando consulta de última versión en GitHub...")
    return ReleaseInfo(
        tag_name="v2.0.0",
        release_notes=(
            "- Se corrigieron errores en los reportes trimestrales.\n"
            "- Mejoras de rendimiento en el motor de base de datos.\n"
            "- Solución a la superposición en la sección de firmas.\n"
            "- Nueva interfaz de actualización OTA en segundo plano."
        ),
        # Usamos el archivo README.md del propio repositorio como archivo de prueba para descargar
        download_url="https://raw.githubusercontent.com/Pablojuk/UEEH/main/README.md",
        html_url="https://github.com/Pablojuk/UEEH"
    )

# 2. Simulación de la lógica de comparación de versiones (forzar actualización disponible)
def mock_is_update_available(self, current_version: str, latest_version: str) -> bool:
    print(f"[MOCK] Comparando versiones: Local ({current_version}) vs Remota ({latest_version}) -> FORZANDO DISPONIBILIDAD")
    return True

# Aplicamos los métodos simulados a la clase real
UpdateChecker.check_latest = mock_check_latest
UpdateChecker.is_update_available = mock_is_update_available

# Ahora importamos y arrancamos la aplicación normalmente
from src.app import run_application

if __name__ == "__main__":
    print("=" * 70)
    # Explicación del funcionamiento de la descarga
    print("  SIMULADOR VISUAL DE ACTUALIZACIONES OTA")
    print("=" * 70)
    print("  * Se simulará que la versión local (1.0.0) es antigua.")
    print("  * Se simulará que la versión v2.0.0 está disponible.")
    print("  * Al descargar, se bajará un archivo 'README.md' de prueba.")
    print("  * El archivo se guardará en su carpeta de 'Descargas' (Downloads).")
    print("=" * 70)
    print("\nIniciando la aplicación académica UEEH (inicie sesión para ver la ventana)...")
    
    sys.exit(run_application())
