# Gestión Académica

Estructura reorganizada con **src layout** para mantener el proyecto escalable y limpio.

## Estructura

```text
.
├── data/                        # Archivos SQLite y recursos persistentes
├── main.py                      # Punto de entrada local (desarrollo)
├── pyproject.toml               # Configuración de paquete Python
└── src/
    └── gestion_academica/
        ├── __init__.py
        ├── app.py               # Entrypoint de aplicación
        ├── config/
        │   ├── __init__.py
        │   └── estilos.py
        ├── data/
        │   ├── __init__.py
        │   └── datos_demo.py
        └── views/
            ├── __init__.py
            ├── tabla_calificaciones.py
            └── ventana_principal.py
```

## Ejecución

```bash
python main.py
```

> La carpeta `data/` queda lista para ubicar la base SQLite (ej. `data/academico.db`).
