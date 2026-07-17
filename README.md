# Sistema Académico UEEH V2

## Descripción general
Sistema académico de escritorio para gestión institucional y pedagógica en entorno local.

## Objetivo de la aplicación
Centralizar procesos clave de gestión académica para docentes e institución: configuración, registro, seguimiento, reportes y respaldo de información.

## Tipo de aplicación
Aplicación de escritorio local para docentes.

## Tecnologías usadas
- Python
- PySide6
- SQLite
- openpyxl
- Jinja2
- pytest

## Módulos principales
- Configuración inicial
- Institución
- Docentes
- Catálogos
- Estudiantes
- Importación de estudiantes
- Matrículas
- Asignaciones docentes
- Registro de calificaciones
- Reportes
- Asistencia
- Acompañamiento integral
- Respaldo/restauración

## Requisitos previos
- Python 3.10 o superior
- pip
- Entorno virtual recomendado

## Instalación
- Crear entorno virtual:
```bash
python -m venv .venv
```

- Activación del entorno virtual en Windows:
```bash
.venv\Scripts\activate
```

- Instalación de dependencias:
```bash
python -m pip install -r requirements-dev.txt
```

## Ejecución de la app
```bash
python -m src.app
```

## Ejecución de pruebas
```bash
python -m pytest
```

## Nota sobre el entorno de Codex
En el entorno de Codex, la instalación de dependencias puede fallar por restricción de red (error 403). La validación completa debe ejecutarse en una PC con acceso a internet.

## Base de datos
La aplicación utiliza SQLite local. Los archivos `data/*.db` no deben versionarse en Git.

## Respaldos
Cada docente debe realizar respaldos periódicos de su base local para evitar pérdida de información.

## Estructura del proyecto
- `src/application`: capa de servicios y casos de uso.
- `src/domain`: reglas y modelos de dominio.
- `src/infrastructure`: persistencia, importadores y exportadores.
- `src/presentation`: interfaz gráfica y vistas.
- `src/shared`: utilidades compartidas.
- `tests`: pruebas automáticas.

## Buenas prácticas
- Trabajar por ramas pequeñas.
- No subir `__pycache__` ni `*.pyc`.
- No subir archivos `.db` locales.
- No modificar lógica sin pruebas.

## Estado actual
- Base limpia de trabajo consolidada en `codex/V2` (referencia de proceso).
- Dependencias documentadas en `requirements.txt` y `requirements-dev.txt`.
- Validación funcional completa pendiente en entorno con internet.

## Próximos pasos
1. Validar instalación en PC local con internet.
2. Ejecutar pruebas automáticas.
3. Revisar flujos y salida de reportes.
4. Preparar instalador para Windows.
