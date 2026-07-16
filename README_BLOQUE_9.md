# BLOQUE 9 - Resumen anual y supletorio

## Que resuelve este bloque

Este bloque incorpora el resumen academico final por asignacion:

- Consolidado de notas trimestrales (T1, T2, T3) por estudiante.
- Calculo de promedio final anual.
- Calculo de cualitativo y observacion final.
- Registro de supletorio y recalculo de nota definitiva.
- Vista visual para cargar, recalcular y guardar supletorios.

## Como ejecutar la app

```bash
python -m src.app
```

## Como probar manualmente el resumen academico

1. Tener estudiantes matriculados y notas trimestrales registradas.
2. Abrir modulo **Reportes**.
3. Seleccionar una asignacion academica.
4. Pulsar **Cargar resumen**.
5. Revisar columnas de trimestres, promedio, cualitativo y observacion.
6. Ingresar supletorio en los estudiantes necesarios.
7. Pulsar **Recalcular** y luego **Guardar supletorio**.
8. Volver a cargar para verificar persistencia de supletorio.

## Como correr pruebas

```bash
PYTHONPATH=. pytest -q tests/test_academic_summary_service.py tests/test_academic_summary_view.py tests/test_persistence.py tests/test_ui_smoke.py
```

> Las pruebas de UI se omiten automaticamente si PySide6 no esta instalado.

## Pendiente para BLOQUE 10

- Exportacion PDF de reportes finales.
- Exportacion Excel de consolidado.
- Formato de impresion institucional.
- Ajustes de filtros avanzados de reporteria.
