# Gestión Académica

Aplicación de escritorio en **PySide6** para visualizar un informe de notas (estilo Excel) directamente en la interfaz, con opciones de guardado a **PDF** y **Excel (.xlsx)**.

## Estructura

```text
.
├── data/                        # Datos persistentes (SQLite u otros)
├── main.py                      # Punto de entrada para desarrollo/Spyder
├── pyproject.toml               # Configuración del paquete
├── reports/                     # Salidas recomendadas (PDF/XLSX)
└── src/
    └── gestion_academica/
        ├── __init__.py
        ├── app.py               # Arranque de la app Qt
        ├── config/
        │   ├── __init__.py
        │   └── estilos.py
        ├── data/
        │   ├── __init__.py
        │   └── datos_demo.py
        ├── resources/
        │   └── logos/
        │       ├── institucion.png
        │       └── mineduc.png
        ├── services/
        │   ├── __init__.py
        │   └── exportadores.py
        └── views/
            ├── __init__.py
            ├── tabla_calificaciones.py
            └── ventana_principal.py
```

> Si los logos no existen, la app usa un fallback visual y sigue funcionando.

## Ejecución

### Desde terminal

```bash
python main.py
```

### Desde Spyder

1. Abrir la carpeta del proyecto (`/workspace/UEEH`) como *Working Directory*.
2. Abrir `main.py`.
3. Ejecutar (Run file/F5).

## Funcionalidades de salida

- **Imprimir**: abre diálogo de impresión del sistema.
- **Guardar PDF**: renderiza el reporte completo paginado a un archivo PDF.
- **Guardar Excel**: genera un `.xlsx` con metadatos, tabla y resumen.
