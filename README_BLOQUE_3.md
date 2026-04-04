# README BLOQUE 3 - Capa de aplicación y servicios base

## Qué resuelve este bloque
Este bloque implementa la capa de aplicación sobre la persistencia SQLite existente, enfocada en:

1. configuración inicial del sistema,
2. clave maestra de primer uso con hash y salt,
3. validación posterior de clave maestra,
4. servicios de negocio para institución,
5. servicios para docentes y catálogos (cursos, paralelos, asignaturas, períodos lectivos).

No incluye UI, PySide6, importación Excel ni reportes.

## Cómo correr las pruebas
Desde la raíz del proyecto:

```bash
python -m unittest tests.test_setup_service -v
python -m unittest tests.test_application_services -v
python -m unittest tests.test_calculations -v
python -m unittest tests.test_persistence -v
```

## Uso desde Spyder
1. Abre Spyder y carga la carpeta del proyecto.
2. Verifica que el intérprete sea Python 3.
3. Desde la consola IPython, puedes ejecutar:

```python
!python -m unittest tests.test_setup_service -v
!python -m unittest tests.test_application_services -v
```

## Qué queda pendiente para el BLOQUE 4
1. Casos de uso de registro de notas trimestrales.
2. Integración de cálculo de notas con persistencia de registros académicos.
3. Consolidación trimestral/final persistida.
4. Reglas operativas para supletorio en flujo real de aplicación.
5. Preparación de contratos para futura UI (sin implementarla).
