# BLOQUE 8 - Registro de notas por trimestre

## Que resuelve esta parte

Este bloque completa el flujo operativo para registrar notas trimestrales en la aplicacion:

- Servicio de negocio para cargar contexto academico, estudiantes matriculados y notas guardadas.
- Recalculo de promedios y nota trimestral reutilizando funciones del dominio.
- Vista PySide6 para seleccionar asignacion + trimestre, editar notas y guardar cambios.
- Integracion en ventana principal para abrir el modulo desde "Notas".
- Pruebas unitarias del servicio y pruebas minimas de la vista.

## Como ejecutar la app

Desde la raiz del proyecto:

```bash
python -m src.app
```

## Prueba manual de registro de notas

1. Crear catalogos base (curso, paralelo, asignatura, periodo).
2. Crear docentes, estudiantes, matriculas y asignaciones academicas.
3. Abrir menu **Notas**.
4. Seleccionar asignacion y trimestre.
5. Cargar estudiantes.
6. Ingresar columnas de actividades y sumativas.
7. Pulsar **Recalcular** y revisar promedio formativo, promedio sumativo y nota trimestral.
8. Pulsar **Guardar** y volver a cargar para verificar persistencia.

## Como correr pruebas

```bash
PYTHONPATH=. pytest -q tests/test_grade_registration_service.py tests/test_grades_view.py tests/test_ui_smoke.py
```

> Nota: Las pruebas de UI se omiten automaticamente si PySide6 no esta instalado.

## Pendiente para BLOQUE 9

- Consolidado trimestral completo por curso y asignatura.
- Promedio final anual y cualitativo final.
- Flujo completo de supletorio.
- Exportacion avanzada de reportes.
