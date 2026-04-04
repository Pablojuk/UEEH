# README BLOQUE 4 - Interfaz base PySide6

## Qué resuelve este bloque
BLOQUE 4 agrega la base visual en PySide6:
- punto de entrada `src/app.py`,
- ventana principal con navegación lateral,
- vistas de primer uso y acceso por clave maestra,
- placeholders de módulos futuros,
- conexión con servicios de BLOQUE 3.

## Instalar PySide6
Desde consola:

```bash
pip install PySide6
```

## Ejecutar la app desde consola
Desde la raíz del proyecto:

```bash
python -m src.app
```

## Ejecutar la app desde Spyder
1. Abrir el proyecto en Spyder.
2. Verificar intérprete Python del entorno con PySide6 instalado.
3. Ejecutar el archivo `src/app.py`.

## Correr pruebas smoke

```bash
python -m unittest tests.test_ui_smoke -v
```

> Si PySide6 no está instalado, las pruebas smoke de UI se omiten automáticamente.

## Pendiente para BLOQUE 5
1. Conectar vistas con CRUD real de institución, docentes y catálogos.
2. Integrar módulo de estudiantes con importación desde Excel.
3. Implementar flujo inicial de registro de notas.
4. Mejorar validaciones visuales y experiencia de usuario.
5. Preparar base para módulo de reportes.
