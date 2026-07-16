"""
Script de desarrollo/pruebas — Limpia todas las tablas operativas de la base
de datos SQLite del sistema UEEH, dejando la estructura (tablas, índices,
triggers) intacta.

USO:
    python scripts/limpiar_base_pruebas.py

La base de datos por defecto está en  data/sistema_notas.db  (relativa a la
raíz del repositorio).  El script pide confirmación antes de ejecutar el
borrado.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

# ------------------------------------------------------------------
# Ruta a la base de datos
# ------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DB_DEFAULT = _REPO_ROOT / "data" / "sistema_notas.db"


def _db_path() -> Path:
    """Determina la ruta a la base de datos (argumento o valor por defecto)."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    return _DB_DEFAULT


# ------------------------------------------------------------------
# Orden de borrado: tablas hijas primero, tablas padre al final.
# Se desactivan las FK temporalmente para evitar problemas de orden
# en caso de que SQLite las valide durante el DELETE.
# ------------------------------------------------------------------
TABLAS_EN_ORDEN: tuple[str, ...] = (
    # — Registros dependientes de asignaciones + estudiantes —
    "orientacion_vocacional_evaluaciones",
    "animacion_lectura_evaluaciones",
    "acompanamiento_evaluaciones",
    "acompanamiento_habilidades_config",
    "grade_activity_config",
    "final_supplementary",
    "grade_records",
    "attendance_justifications",
    "attendance_records",
    # — Relaciones intermedias —
    "asignaciones_docente",
    "matriculas",
    "trimestres",
    # — Catálogos —
    "estudiantes",
    "docentes",
    "asignaturas",
    "cursos",
    "paralelos",
    "periodos_lectivos",
    # — Institución y configuración —
    "institucion",
    "configuracion_sistema",
)


def limpiar(db: Path) -> None:
    """Vacía todas las tablas operativas de la base indicada."""

    conn = sqlite3.connect(str(db))
    try:
        # Desactivar FK durante el borrado
        conn.execute("PRAGMA foreign_keys = OFF;")

        with conn:
            for tabla in TABLAS_EN_ORDEN:
                conn.execute(f"DELETE FROM {tabla};")
                print(f"  ✓ {tabla}")

        # Reactivar FK
        conn.execute("PRAGMA foreign_keys = ON;")

        # VACUUM para recuperar espacio en disco
        conn.execute("VACUUM;")
        print("\n  ✓ VACUUM ejecutado — espacio en disco recuperado.")
    finally:
        conn.close()


# ------------------------------------------------------------------
# Punto de entrada
# ------------------------------------------------------------------
def main() -> None:
    db = _db_path()

    if not db.exists():
        print(f"ERROR: No se encontró la base de datos en:\n  {db}")
        sys.exit(1)

    size_kb = db.stat().st_size / 1024
    print("=" * 60)
    print("  LIMPIEZA DE BASE DE DATOS — Solo para pruebas")
    print("=" * 60)
    print(f"\n  Base de datos : {db}")
    print(f"  Tamaño actual : {size_kb:,.1f} KB\n")
    print("  ADVERTENCIA: Se eliminarán TODOS los datos de TODAS")
    print("  las tablas operativas.  La estructura se conserva.\n")
    print("  Asegúrate de haber creado un respaldo antes de continuar.\n")

    respuesta = input("  Escribe SI (en mayúsculas) para continuar: ").strip()

    if respuesta != "SI":
        print("\n  Operación cancelada. No se modificó la base de datos.")
        sys.exit(0)

    print()
    limpiar(db)
    print("\n" + "=" * 60)
    print("  Base de datos vaciada exitosamente.")
    print("  Puedes restaurar tu respaldo desde el módulo de Utilidades.")
    print("=" * 60)


if __name__ == "__main__":
    main()
