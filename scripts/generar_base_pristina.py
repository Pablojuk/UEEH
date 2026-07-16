"""Script para generar una base de datos de distribución limpia (prístina).

Crea una base de datos SQLite en data/sistema_notas.db con la estructura completa
y los catálogos académicos iniciales sembrados, pero sin ningún dato operativo
(docentes, estudiantes, asistencias, configuración de clave, etc.).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Añadir la raíz del repositorio al PYTHONPATH
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.infrastructure.persistence.db import initialize_database
from src.application.services.catalog_service import CatalogService


def main() -> None:
    db_dest = _REPO_ROOT / "data" / "sistema_notas.db"
    
    # 1. Asegurar que el directorio data exista
    db_dest.parent.mkdir(parents=True, exist_ok=True)
    
    # 2. Eliminar base existente si hay una para empezar desde cero
    if db_dest.exists():
        print(f"Eliminando base de datos anterior en: {db_dest}")
        db_dest.unlink()
        
    print("Inicializando base de datos prístina...")
    # 3. Inicializar esquema
    conn = initialize_database(str(db_dest))
    
    # 4. Sembrar catálogos académicos obligatorios a través de CatalogService
    print("Sembrando catálogos base del Ministerio de Educación...")
    CatalogService(conn)
    
    conn.close()
    
    size_kb = db_dest.stat().st_size / 1024
    print("=" * 60)
    print("  BASE DE DATOS MAESTRA GENERADA EXITOSAMENTE")
    print("=" * 60)
    print(f"  Ubicación : {db_dest}")
    print(f"  Tamaño    : {size_kb:,.1f} KB")
    print("  Contenido : Esquema + Catálogos académicos base.")
    print("  Excluidos : Docentes, Estudiantes, Calificaciones, Clave Maestra.")
    print("=" * 60)


if __name__ == "__main__":
    main()
