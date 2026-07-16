# README BLOQUE 5 - Gestión visual de institución, docentes y catálogos

## Qué resuelve este bloque
Este bloque convierte en funcionales las vistas de:
- Institución
- Docentes
- Catálogos

Se incorporan formularios, tablas y operaciones básicas conectadas a servicios de aplicación existentes.

## Cómo ejecutar la app
Desde consola:

```bash
python -m src.app
```

En Spyder:
1. Abrir el proyecto.
2. Verificar entorno con PySide6.
3. Ejecutar `src/app.py`.

## Prueba manual de módulos
### Institución
1. Ir a módulo "Institución".
2. Completar nombre y jornada.
3. Guardar y verificar mensaje de éxito.
4. Cambiar valor y guardar nuevamente para validar actualización.

### Docentes
1. Ir a módulo "Docentes".
2. Registrar un docente nuevo.
3. Verificar que aparezca en tabla.
4. Seleccionar fila y editar datos, guardar.
5. Usar activar/inactivar y confirmar cambio de estado en tabla.
6. Probar búsqueda por nombre o identificación.

### Catálogos
1. Ir a módulo "Catálogos".
2. En cada pestaña (Cursos, Paralelos, Asignaturas, Períodos) registrar un elemento.
3. Verificar recarga de la tabla después de guardar.

## Cómo correr las pruebas
```bash
python -m unittest tests.test_ui_smoke -v
python -m unittest tests.test_ui_management_views -v
```

## Qué queda pendiente para BLOQUE 6
1. Módulo visual de estudiantes con matrícula.
2. Base visual de registro de notas.
3. Integración progresiva de cálculos en vistas de notas.
4. Flujo inicial para reportes (sin exportación final completa).
