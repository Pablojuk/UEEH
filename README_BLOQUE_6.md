# README BLOQUE 6 - Módulo de estudiantes e importación desde Excel

## Qué resuelve este bloque
- Vista funcional de estudiantes con registro manual y búsqueda.
- Importación de estudiantes desde `.xlsx`, `.xlsm` y `.csv`.
- Vista previa simple de importación y resumen final.
- Validaciones básicas y control de duplicados.

## Dependencias necesarias para leer Excel
- `openpyxl` (para `.xlsx` y `.xlsm`).

Instalación:

```bash
pip install openpyxl
```

## Cómo ejecutar la app
```bash
python -m src.app
```

## Cómo probar manualmente la importación
1. Abrir módulo **Estudiantes**.
2. Probar registro manual de un estudiante.
3. Usar botón **Importar Excel/CSV**.
4. Elegir archivo con columnas de nombres/apellidos (identificación opcional).
5. Confirmar importación en vista previa.
6. Revisar resumen final (importados, omitidos, duplicados, errores).

## Cómo correr las pruebas
```bash
python -m unittest tests.test_student_service -v
python -m unittest tests.test_student_import_service -v
python -m unittest tests.test_students_view -v
python -m unittest tests.test_ui_smoke -v
```

## Qué queda pendiente para BLOQUE 7
1. Módulo visual de matrículas.
2. Asignaciones académicas (docente-asignatura-curso-paralelo).
3. Integración entre estudiantes y matrículas en UI.
4. Endurecer validaciones de importación y bitácora detallada.
