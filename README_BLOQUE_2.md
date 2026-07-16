# README BLOQUE 2 - Persistencia SQLite e infraestructura base

Este bloque implementa la capa de persistencia con `sqlite3` estándar, sin ORM y sin interfaz gráfica.

## 1. Qué incluye
- Conexión SQLite configurable (`db.py`).
- Inicialización de esquema normalizado (`schema.py`).
- Repositorios base con operaciones: crear, obtener por id, listar, actualizar (`repositories.py`).
- Semillas idempotentes para configuración base y trimestres (`seed.py`).
- Pruebas unitarias de persistencia sobre base temporal (`tests/test_persistence.py`).

## 2. Cómo inicializar la base
Desde la raíz del proyecto:

```bash
python -c "from src.infrastructure.persistence.db import initialize_database; conn = initialize_database(); conn.close()"
```

Esto creará por defecto el archivo SQLite en `data/sistema_notas.db`.

Si necesitas otra ruta:

```python
from src.infrastructure.persistence.db import initialize_database

conn = initialize_database(r"C:\ruta\personalizada\mi_base.db")
conn.close()
```

## 3. Cómo correr pruebas
Ejecutar todas las pruebas:

```bash
python -m unittest -v
```

Ejecutar solo persistencia:

```bash
python -m unittest tests.test_persistence -v
```

## 4. Uso desde Spyder
1. Abre Spyder y luego **File > Open Project...**.
2. Selecciona la carpeta raíz del proyecto.
3. Verifica el intérprete Python 3.
4. Para inicializar BD desde consola IPython:
   ```python
   from src.infrastructure.persistence.db import initialize_database
   conn = initialize_database()
   conn.close()
   ```
5. Para ejecutar pruebas en Spyder:
   ```python
   !python -m unittest tests.test_persistence -v
   ```

## 5. Pendiente para BLOQUE 3
1. Definir contrato y validaciones para importación de estudiantes desde Excel.
2. Implementar adaptador de lectura Excel desacoplado del dominio.
3. Incorporar bitácora de errores de importación por fila.
4. Agregar pruebas de importación con archivos de ejemplo.
5. Mantener consistencia con las reglas de dominio del BLOQUE 1.

## 6. Restricciones respetadas en este bloque
- Sin UI ni PySide6.
- Sin ventanas de escritorio.
- Sin importación real desde Excel.
- Sin exportación a PDF/Excel.
- Sin implementación de reportes.
