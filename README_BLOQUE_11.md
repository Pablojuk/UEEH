# BLOQUE 11 - Validación final y utilidades del sistema

## Que resuelve este bloque

Este bloque fortalece la robustez antes del empaquetado final:

- Servicio de respaldo y restauración de base SQLite.
- Vista de utilidades del sistema para operaciones de seguridad.
- Integración visual en menú principal para acceso rápido.
- Mensajes claros de éxito/error y confirmación de restauración.

## Como crear respaldo

1. Abrir **Utilidades** en la aplicación.
2. Pulsar **Crear respaldo**.
3. Elegir ruta y nombre de archivo `.db`.
4. Confirmar mensaje de éxito.

## Como restaurar respaldo

1. Abrir **Utilidades**.
2. Pulsar **Restaurar respaldo**.
3. Elegir archivo `.db` existente.
4. Confirmar advertencia.
5. Reiniciar la aplicación si el mensaje lo indica.

## Como ejecutar la app

```bash
python -m src.app
```

## Como correr las pruebas

```bash
PYTHONPATH=. pytest -q tests/test_backup_service.py tests/test_settings_view.py tests/test_ui_smoke.py tests/test_reports_view.py tests/test_academic_summary_view.py tests/test_grades_view.py
```

## Pendiente para un bloque futuro

- Auditoría de operaciones sensibles.
- Mejoras de permisos/roles por perfil de usuario.
- Endurecimiento adicional de seguridad de credenciales.
- Estrategia de distribución final (fuera del alcance actual).
