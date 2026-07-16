# BLOQUE 1 - Dominio, reglas de negocio y especificación técnica inicial

Este bloque establece la base funcional y técnica del sistema de notas, sin incluir interfaz, base de datos ni importación/exportación real.

## 1. Requisitos previos
- Python 3.10+ (recomendado).
- Entorno virtual opcional pero sugerido.

## 2. Estructura del bloque

```text
UEEH/
├── docs/
│   ├── reglas_negocio.md
│   └── arquitectura_inicial.md
├── src/
│   └── domain/
│       ├── models.py
│       └── calculations.py
├── tests/
│   └── test_calculations.py
└── README_BLOQUE_1.md
```

## 3. Cómo ejecutar este bloque
Este bloque no inicia una aplicación todavía. Solo contiene documentación + dominio + pruebas.

Puedes validar que los módulos cargan correctamente ejecutando:

```bash
python -m unittest tests.test_calculations -v
```

## 4. Cómo correr pruebas
Desde la raíz del proyecto:

```bash
python -m unittest -v
```

o de forma específica:

```bash
python -m unittest tests.test_calculations -v
```

## 5. Cómo abrirlo desde Spyder
1. Abrir Spyder.
2. Ir a **File > Open Project...**.
3. Seleccionar la carpeta raíz `UEEH`.
4. Establecer el intérprete Python del entorno deseado.
5. Abrir y revisar:
   - `docs/reglas_negocio.md`
   - `docs/arquitectura_inicial.md`
   - `src/domain/models.py`
   - `src/domain/calculations.py`
   - `tests/test_calculations.py`
6. Ejecutar pruebas desde consola IPython en Spyder:
   ```python
   !python -m unittest tests.test_calculations -v
   ```

## 6. Pendientes para BLOQUE 2
1. Diseñar esquema SQLite inicial (tablas y relaciones).
2. Crear repositorios de persistencia para entidades principales.
3. Implementar casos de uso de configuración inicial (clave única).
4. Definir validaciones de rango de notas y consistencia de datos.
5. Preparar servicios de aplicación para matrícula, asignación docente y carga de notas.
6. Mantener las reglas de `domain/calculations.py` como núcleo reutilizable.

## 7. Restricciones respetadas en este bloque
- Sin interfaz gráfica.
- Sin ventanas ni PySide6 en código.
- Sin base de datos implementada.
- Sin CRUD.
- Sin importación/exportación real.
- Sin reportes.
