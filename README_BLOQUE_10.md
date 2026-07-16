# BLOQUE 10 - Exportación de reportes PDF y Excel

## Que resuelve este bloque

Este bloque agrega la exportación de reportes académicos por asignación:

- Exportación de resumen final por estudiante (T1, T2, T3, promedio, cualitativo, observación, supletorio, nota definitiva).
- Generación de PDF para impresión.
- Generación de Excel `.xlsx` para revisión y entrega.
- Integración visual con botones de exportación desde el módulo de reportes.

## Dependencias necesarias para PDF y Excel

Instalar en el entorno de trabajo:

```bash
pip install reportlab openpyxl
```

## Como ejecutar la app

```bash
python -m src.app
```

## Como probar manualmente la exportación

1. Abrir módulo **Reportes**.
2. Seleccionar asignación académica.
3. Cargar resumen.
4. Usar **Exportar PDF** y elegir ruta de guardado.
5. Usar **Exportar Excel** y elegir ruta de guardado.
6. Verificar archivos creados y contenido.
7. Probar escenario sin datos para validar mensaje de advertencia.

## Como correr las pruebas

```bash
PYTHONPATH=. pytest -q tests/test_report_export_service.py tests/test_pdf_report_exporter.py tests/test_excel_report_exporter.py tests/test_reports_view.py tests/test_ui_smoke.py
```

> Las pruebas de exportadores se omiten automáticamente si `reportlab` u `openpyxl` no están instalados.

## Pendiente para BLOQUE 11

- Parametrización avanzada de plantillas institucionales.
- Exportación masiva por múltiples asignaciones.
- Firma digital o validación documental.
- Preparación para empaquetado final e instalador.
