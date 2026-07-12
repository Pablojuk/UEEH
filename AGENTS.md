# Guía permanente para agentes — UEEH

## Alcance y propósito

Este archivo rige todo el repositorio UEEH. El proyecto es una aplicación académica de escritorio y uso local para la gestión institucional y pedagógica en el contexto educativo ecuatoriano. Todo agente debe actuar como especialista del dominio, preservar la trazabilidad de la información y priorizar la exactitud de calificaciones, matrículas, asistencia, reportes y respaldos.

Antes de modificar cualquier archivo:

1. Ejecutar `git branch --show-current` y `git status --short`.
2. Confirmar que la rama activa sea exactamente la autorizada por el usuario. Para el trabajo de V3, debe ser `codex/V3`.
3. Si la rama no coincide, detenerse e informar; nunca cambiar de rama automáticamente.
4. Revisar el estado existente y no sobrescribir cambios ajenos o no relacionados.
5. Limitar cada cambio al alcance solicitado.

Está prohibido modificar otras ramas. No realizar `merge`, `rebase`, `git push`, abrir pull requests ni publicar cambios sin autorización expresa del usuario. No crear commits salvo que el usuario lo solicite explícitamente.

## Entorno tecnológico

- Usar Python 3.10 o superior y mantener compatibilidad con esa versión mínima.
- La interfaz gráfica usa PySide6; respetar el ciclo de vida de `QApplication`, las señales, los diálogos, las vistas y el hilo de interfaz.
- La persistencia es SQLite local mediante `sqlite3`, con `sqlite3.Row` y claves foráneas activadas.
- La importación y exportación de libros Excel usa OpenPyXL.
- Los reportes HTML usan Jinja2 y las plantillas de `src/infrastructure/templates`.
- Las pruebas se ejecutan con pytest, aunque parte de la suite conserva clases y aserciones de `unittest`.
- La aplicación debe seguir funcionando en Windows, incluidas rutas con `pathlib`, separadores, permisos, nombres de archivo, codificación UTF-8 y comportamiento de PySide6.
- No agregar ni actualizar dependencias sin autorización. Las dependencias de ejecución viven en `requirements.txt` y las de desarrollo en `requirements-dev.txt`.

Comandos canónicos:

```powershell
python -m pip install -r requirements-dev.txt
python -m src.app
python -m pytest
```

## Arquitectura real del proyecto

Mantener la arquitectura por capas y ubicar cada responsabilidad donde corresponde:

- `src/domain`: modelos de dominio y funciones puras de cálculo académico. `models.py` contiene entidades mediante `dataclass`; `calculations.py` concentra fórmulas, redondeo, truncamiento y escalas. Esta capa no debe depender de PySide6, SQLite, OpenPyXL ni Jinja2.
- `src/application`: servicios y casos de uso para configuración, institución, docentes, catálogos, estudiantes, importación, matrículas, asignaciones, calificaciones, asistencia, acompañamiento, resúmenes, reportes y respaldos. Coordina validación y persistencia, pero no debe contener widgets ni decisiones visuales.
- `src/infrastructure`: detalles técnicos. `persistence` contiene conexión, esquema, migraciones compatibles y repositorios SQLite; `importers` lee Excel/CSV; `exporters` genera Excel, HTML y PDF; `templates` contiene las plantillas Jinja2.
- `src/presentation`: interfaz PySide6. `main_window.py`, `views` y `widgets` deben encargarse de interacción y presentación, delegando reglas y persistencia a servicios.
- `src/shared`: utilidades transversales pequeñas y reutilizables. La seguridad de la clave maestra usa PBKDF2-HMAC, salt aleatorio y comparación en tiempo constante; nunca degradar estas garantías.
- `tests`: pruebas de cálculos, servicios, persistencia, importadores/exportadores, respaldos, reportes y vistas. Mantener las pruebas aisladas de la base real y usar bases temporales o `:memory:`.
- `src/app.py`: punto de entrada y raíz de composición para `python -m src.app`. Inicializa `QApplication`, base de datos y servicios, ejecuta configuración inicial y login, construye `MainWindow`, y cierra la conexión al salir. No duplicar esta composición en las vistas.

Regla de dependencias: presentación llama a aplicación; aplicación aplica casos de uso y reglas de dominio y accede a infraestructura mediante las colaboraciones ya establecidas; infraestructura implementa persistencia, importación y salida; dominio permanece independiente. Evitar dependencias circulares y acceso SQL directo desde vistas.

## Dominio académico ecuatoriano

- Tratar las reglas académicas como lógica sensible. No inventar normativa, escalas, equivalencias, períodos o requisitos del Ministerio de Educación; verificar primero la especificación del proyecto y solicitar aclaración si falta una regla.
- Conservar las reglas existentes hasta que exista un requisito explícito: calificaciones normalizadas en el rango 0 a 10, trimestres 1 a 3, cálculo trimestral 70 % formativo y 30 % sumativo, y funciones explícitas de redondeo o truncamiento a dos decimales.
- No sustituir `Decimal`, `ROUND_DOWN` o `ROUND_HALF_UP` por redondeos binarios implícitos cuando ello cambie resultados.
- Validar en la capa de aplicación tanto entradas manuales como datos importados. La interfaz puede ayudar al usuario, pero nunca debe ser la única barrera de validación.
- Toda modificación de fórmulas, refuerzo, mejora, supletorio, escala cualitativa, aprobación o promoción debe incluir casos de frontera y pruebas de regresión con resultados exactos.
- Respetar claves únicas, relaciones de matrícula/asignación, integridad referencial y restricciones de trimestre definidas por SQLite.
- Mantener en español los conceptos visibles del dominio y mensajes destinados a usuarios, con ortografía y tildes correctas.

## Privacidad y seguridad de datos

- Los datos de estudiantes y docentes son confidenciales. Aplicar minimización: leer, mostrar, registrar y exportar solamente lo necesario para el caso de uso.
- Nunca incluir en código, pruebas, documentación, capturas, logs, commits o mensajes datos reales de estudiantes, docentes, representantes o credenciales. Usar datos sintéticos inequívocos.
- No exponer identificaciones, nombres, calificaciones, asistencia, direcciones, teléfonos, rutas privadas o secretos en mensajes de error o registros diagnósticos.
- No enviar datos académicos a servicios externos ni añadir telemetría, sincronización o red sin autorización expresa y una revisión de privacidad.
- No almacenar claves en texto plano. Preservar el hash PBKDF2-HMAC, el salt y la comparación segura existentes.
- Al generar archivos, evitar fórmulas o contenido activo procedente de entradas no confiables y controlar rutas, extensiones y sobrescrituras.

## SQLite, respaldos y restauración

- La base predeterminada es local: `data/sistema_notas.db`. Está prohibido versionar `data/*.db`, `*.sqlite` o cualquier copia que contenga datos reales.
- No quitar `PRAGMA foreign_keys = ON`, restricciones `CHECK`, claves únicas ni transacciones sin una justificación y pruebas específicas.
- Los cambios de esquema deben ser compatibles con bases existentes, idempotentes y probados tanto en una base nueva como en una base anterior representativa. No destruir ni reinterpretar datos silenciosamente.
- Usar parámetros SQL para valores; nunca interpolar entradas del usuario en consultas.
- Para respaldar y restaurar, usar la API de backup de SQLite y cerrar explícitamente todas las conexiones, como hace `BackupService`.
- Antes de restaurar, validar existencia, extensión y legibilidad del respaldo. No reemplazar la base activa con un archivo no validado; conservar mensajes claros y exigir reinicio cuando corresponda.
- Las pruebas nunca deben escribir sobre la base local real. Usar directorios temporales, rutas temporales o `:memory:`.

## Importación y exportación de Excel

- La importación admite actualmente `.xlsx`, `.xlsm` y `.csv`; OpenPyXL debe abrir libros con `data_only=True` y `read_only=True`, sin ejecutar macros.
- Cerrar siempre los libros, incluso ante errores. Validar extensión, existencia, encabezados, hoja seleccionada, filas vacías, tipos, identificaciones, duplicados y campos obligatorios antes de persistir.
- Presentar una previsualización o resultado validado y errores accionables por fila cuando el flujo lo permita. Una importación parcial debe ser explícita y no dejar datos inconsistentes.
- Neutralizar valores de texto que puedan convertirse en fórmulas al abrir archivos exportados. No copiar macros, vínculos externos ni contenido activo.
- En exportaciones, conservar formato numérico, dos decimales, títulos, contexto institucional y estructura esperada. Probar el archivo resultante volviéndolo a abrir con OpenPyXL y verificando celdas relevantes.
- Mantener la lógica académica fuera del exportador: este recibe datos ya calculados y se responsabiliza de representarlos fielmente.

## Reportes

- Los reportes PDF, Excel y HTML deben representar los mismos datos y reglas. Evitar recalcular notas de manera diferente en cada formato.
- Escapar contenido variable en plantillas Jinja2 y no insertar HTML no confiable como seguro.
- Preservar las plantillas y variantes existentes para reportes trimestrales, anuales, simplificados, asistencia, animación a la lectura, orientación vocacional y acompañamiento.
- Comprobar títulos, institución, período, asignatura, curso, paralelo, docente, trimestre, orden de estudiantes, observaciones, promedios y filas vacías según el tipo de reporte.
- No incluir datos adicionales por conveniencia. Cada reporte debe limitarse a la información autorizada y necesaria.
- Si cambia una plantilla o exportador, añadir pruebas del contenido y, cuando afecte diseño, verificar visualmente una salida generada sin usar datos reales.

## PySide6 y experiencia en Windows

- Las vistas no deben abrir conexiones SQLite ni contener SQL. Inyectar servicios desde `src.app.py` o desde la composición correspondiente.
- No bloquear el hilo de interfaz con importaciones, exportaciones o tareas largas; conservar estados ocupados y mensajes de error comprensibles.
- Mantener señales y conexiones con ciclos de vida claros. Evitar crear múltiples instancias de `QApplication`.
- Probar diálogos, selección de archivos, portapapeles, rutas Unicode, escalado y cierre de recursos en Windows.
- Para pruebas de UI, reutilizar `QApplication.instance()` y mantener la posibilidad de omitirlas con una razón explícita si PySide6 no está instalado; un salto no equivale a una validación exitosa del comportamiento afectado.

## Calidad y pruebas obligatorias

Todo cambio funcional debe comenzar o terminar con pruebas que cubran el comportamiento modificado. Antes de dar una tarea por finalizada:

1. Ejecutar las pruebas específicas del área afectada.
2. Ejecutar la suite completa con `python -m pytest`.
3. Revisar `git diff --check`, `git diff --stat` y `git status --short`.
4. Confirmar que no se generaron bases, reportes, credenciales, cachés ni artefactos que puedan contener datos.
5. Informar los comandos ejecutados, pruebas aprobadas, omitidas o fallidas y cualquier limitación del entorno.

No declarar éxito si una prueba relevante falla. No corregir una prueba relajando una regla válida ni eliminar cobertura para hacer pasar la suite. Si el entorno carece de una dependencia o impide ejecutar una validación, documentar la limitación y proporcionar el comando exacto pendiente; no ocultar el fallo.

Las pruebas mínimas según el cambio incluyen:

- Dominio/calificaciones: valores límite, `None`, mejoras, decimales, tres trimestres, ponderaciones, cualitativos y supletorio.
- Persistencia: esquema nuevo, migración, claves foráneas, unicidad, rollback y reapertura.
- Excel: archivo válido, extensión inválida, encabezados faltantes, filas vacías, duplicados, fórmulas inseguras y reapertura de exportación.
- Reportes: igualdad de datos entre formatos, contexto, filas y plantillas especiales.
- Respaldos: creación, archivo inválido, restauración y verificación de datos en una ruta temporal.
- UI: construcción, señales, validación, flujo feliz, error y no bloqueo del hilo visual.

## Disciplina de cambios y entrega

- Preferir cambios pequeños, legibles y tipados; conservar `from __future__ import annotations` donde ya se usa.
- No alterar código no relacionado, no reformatear masivamente y no renombrar conceptos del dominio sin necesidad.
- Mantener compatibilidad hacia atrás en bases, archivos importados, reportes y flujos de usuario, salvo requisito explícito en contrario.
- Actualizar pruebas y documentación cuando cambie un contrato observable.
- Antes de finalizar, enumerar la rama activa, archivos modificados, resumen del cambio, pruebas y estado Git.
- Nunca versionar bases locales ni datos personales. Nunca actuar sobre otra rama, fusionar o publicar sin autorización expresa.
