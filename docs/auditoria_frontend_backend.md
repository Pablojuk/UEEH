# Auditoría frontend/backend UEEH V2

## 1. Resumen ejecutivo
La app **sí parece lista para prueba manual guiada**, con una arquitectura por capas clara y un flujo de arranque completo (setup inicial → login → ventana principal). Sin embargo, antes de pruebas funcionales profundas conviene validar dependencias en un equipo con internet y ejecutar la suite automática completa para reducir riesgo de regresiones en UI/reportes.

## 2. Arquitectura general
El proyecto está organizado en capas coherentes:
- **presentation**: ventanas, vistas y navegación PySide6.
- **application**: servicios/casos de uso por módulo académico.
- **domain**: reglas de cálculo y modelos de negocio puros.
- **infrastructure**: persistencia SQLite, importadores, exportadores y templates.
- **shared**: utilidades transversales (seguridad).
- **tests**: pruebas unitarias/integración ligera de servicios, dominio y UI.

Conclusión: la separación de responsabilidades es buena para mantenimiento incremental.

## 3. Revisión de frontend PySide6
### Hallazgos
- `MainWindow` centraliza navegación con `Sidebar` + `QStackedWidget` y conecta vistas por sección.
- Existe un conjunto amplio de vistas críticas: institución, docentes, catálogos, estudiantes, matrículas, asignaciones, notas, reportes, asistencia y acompañamiento.
- La hoja de estilo global (`styles.py`) mantiene consistencia visual base.

### Riesgos visuales/UX
- `refresh_data` se invoca de forma amplia en cambios globales; en datasets grandes puede impactar fluidez.
- Gran cantidad de módulos en una sola ventana principal puede requerir pruebas de usabilidad por secuencia real docente.

### Pantallas críticas para prueba manual
- Setup/Login.
- Estudiantes (alta/importación).
- Matrículas + Asignaciones.
- Registro de notas.
- Reportes (HTML/PDF/Excel).
- Asistencia y acompañamiento.

## 4. Revisión de backend/servicios
### Hallazgos
- Servicios bien particionados por dominio funcional (`*_service.py`).
- `src/app.py` compone explícitamente dependencias y las inyecta a la UI.
- Buen desacople entre cálculo (domain), persistencia (infrastructure) y orquestación (application).

### Riesgos de acoplamiento
- El entrypoint arma muchos servicios en bloque: útil y explícito, pero aumenta sensibilidad a cambios de constructor.
- Algunos flujos dependen de múltiples servicios coordinados (reportes/notas/asignaciones), donde errores de consistencia de datos pueden aparecer tarde.

### Validaciones/manejo de errores
- Se observan validaciones funcionales en servicios y cobertura de pruebas por módulos clave.
- Recomendable prueba manual negativa (datos incompletos, catálogos vacíos, asignaciones inexistentes).

## 5. Revisión de base de datos SQLite
### Hallazgos
- Inicialización robusta con `initialize_database()` y `PRAGMA foreign_keys = ON`.
- Esquema amplio para operación académica (configuración, institución, docentes, estudiantes, matrículas, asignaciones, notas, asistencia, acompañamiento, etc.).
- Hay migraciones de compatibilidad mínimas (`ALTER TABLE` condicional).

### Riesgos
- Sin framework formal de migraciones versionadas; la estrategia actual es pragmática y puede crecer en complejidad con más cambios.
- Riesgo de pérdida de datos si no se hacen respaldos antes de pruebas destructivas.
- Correcto que `data/*.db` esté ignorado por Git para evitar mezclar estado local con código.

## 6. Revisión de reportes/exportadores
### Hallazgos
- Exportadores presentes para Excel/PDF y render HTML por plantillas Jinja2.
- Templates específicos por tipo de reporte (trimestral/anual/cualitativo/asistencia/orientación).

### Riesgos
- Dependencias externas (`openpyxl`; potencialmente librería PDF) deben validarse en entorno real.
- Riesgo de divergencia entre datos esperados en template y estructura real de registros si cambia un servicio.

## 7. Revisión de importación de estudiantes
### Hallazgos
- Importador dedicado en infraestructura (`excel_students_importer.py`) consumido por `student_import_service`.
- Diseño correcto: parsing en infraestructura, coordinación en capa de aplicación.

### Riesgos
- Errores de formato de archivo (columnas, tipos, encabezados) deben cubrirse con pruebas manuales de plantillas reales.
- Validar manejo de duplicados/códigos existentes en escenario de uso docente.

## 8. Revisión de seguridad
### Hallazgos
- Seguridad local basada en PBKDF2-HMAC SHA-256 con salt aleatorio por clave.
- Verificación en tiempo constante con `hmac.compare_digest`.

### Riesgos
- Modelo de seguridad local depende de custodia del equipo/DB del docente.
- Conviene documentar política de cambio/recuperación de clave maestra para operación real.

## 9. Revisión de pruebas
- Archivos de prueba detectados: **31**.
- Archivos de prueba vacíos (sin `test_`): **0**.
- Marcadores/condiciones de skip detectados: **16** aprox.
- Cobertura clara en dominio/cálculos, persistencia, servicios clave, reportes y vistas.
- Módulos con cobertura menos evidente por nombre de test: `teacher_service`, `institution_service`, `attendance_service`, `catalog_service` (revisar cobertura funcional indirecta).
- Debe ejecutarse en PC local con internet: `python -m pip install -r requirements-dev.txt` + `python -m pytest`.

## 10. Riesgos técnicos antes de prueba manual
### Alto
- Dependencias de entorno no instalables en entornos restringidos de red.
- Pruebas UI/reportes pueden omitirse si faltan paquetes, ocultando regresiones.

### Medio
- Migraciones de compatibilidad sin versionado formal de esquema.
- Flujos de datos cruzados entre módulos (asignaciones/notas/reportes).

### Bajo
- Estilo visual global simple (riesgo bajo de inconsistencia severa).
- Estructura por capas clara para localizar fallos.

## 11. Checklist de prueba manual en Cursor/Windows
1. Abrir app (`python -m src.app`).
2. Configurar primer uso.
3. Login con clave maestra.
4. Registrar/editar institución.
5. Registrar docentes.
6. Configurar catálogos (curso/paralelo/asignatura/período).
7. Crear/importar estudiantes.
8. Registrar matrículas.
9. Crear asignaciones docentes.
10. Registrar notas trimestrales y validar cálculos.
11. Generar reportes (HTML/PDF/Excel).
12. Probar asistencia.
13. Probar acompañamiento integral.
14. Ejecutar respaldo/restauración.
15. Cerrar y reabrir app.
16. Verificar persistencia SQLite y consistencia de datos.

## 12. Recomendación final
Recomendación: **pasar a prueba manual controlada**, pero primero validar dependencias e idealmente correr suite automática completa en una PC local con internet. No se requiere corrección inmediata de arquitectura antes de esa fase; sí conviene registrar hallazgos de prueba manual por módulo para priorizar ajustes funcionales posteriores.
