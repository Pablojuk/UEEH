# README BLOQUE 7 - Matrículas y asignaciones académicas

## Qué resuelve este bloque
- Módulo funcional de matrículas.
- Módulo funcional de asignaciones académicas.
- Integración visual en menú lateral y ventana principal.

## Cómo ejecutar la app
```bash
python -m src.app
```

## Cómo probar manualmente matrículas
1. Abrir módulo **Matrículas**.
2. Seleccionar estudiante, curso, paralelo y período.
3. Guardar y verificar fila en tabla.
4. Intentar duplicar la misma matrícula y verificar advertencia.

## Cómo probar manualmente asignaciones académicas
1. Abrir módulo **Asignaciones**.
2. Seleccionar docente, asignatura, curso, paralelo y período.
3. Guardar y verificar fila en tabla.
4. Intentar duplicar la misma combinación y verificar advertencia.

## Cómo correr las pruebas
```bash
python -m unittest tests.test_enrollment_service -v
python -m unittest tests.test_teaching_assignment_service -v
python -m unittest tests.test_enrollments_view -v
python -m unittest tests.test_teaching_assignments_view -v
python -m unittest tests.test_ui_smoke -v
```

## Qué queda pendiente para BLOQUE 8
1. Módulo real de registro de notas.
2. Consolidación trimestral y anual.
3. Integración de asignaciones con captura de notas.
4. Preparación de reportes académicos.
