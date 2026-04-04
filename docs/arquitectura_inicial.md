# Arquitectura Inicial (BLOQUE 1)

## 1. Propuesta de arquitectura en capas
Se propone una arquitectura limpia por capas para separar reglas académicas de infraestructura y UI:

1. **Domain (núcleo)**
   - Entidades y objetos de valor.
   - Reglas puras de cálculo de notas.
   - Sin dependencias de UI, base de datos o librerías externas de infraestructura.

2. **Application (casos de uso)**
   - Orquestación de operaciones: registrar notas, consolidar trimestre, cerrar año, preparar reporte.
   - Invoca domain + puertos (interfaces).

3. **Infrastructure**
   - Adaptadores concretos: SQLite, importación Excel, exportación Excel/PDF.
   - Implementa repositorios y servicios externos.

4. **Presentation (Desktop UI)**
   - Ventanas, formularios, navegación.
   - Llama casos de uso de `application`.

### Beneficios
- Menor acoplamiento y mayor testabilidad.
- Reglas de negocio estables y reutilizables.
- Posibilidad de cambiar UI o BD sin reescribir cálculos académicos.

## 2. ¿Por qué Python + PySide6 + SQLite?

## Python
- Sintaxis clara y productiva para equipos pequeños.
- Excelente ecosistema para manejo de Excel, PDF y testing.
- Facilita iteración incremental por bloques.

## PySide6 (para bloques siguientes)
- Framework Qt moderno para escritorio nativo multiplataforma.
- Permite construir UI profesional/minimalista.
- Buen soporte para tablas, modelos de datos y formularios complejos.

## SQLite (v1 local)
- Base embebida, sin servidor.
- Fácil despliegue en PCs de docentes.
- Suficiente para primera versión offline.

## 3. Módulos principales propuestos
1. `domain.models`
   - Dataclasses del dominio académico.
2. `domain.calculations`
   - Funciones puras de notas.
3. `application.use_cases` (siguiente bloque)
   - Flujos de negocio.
4. `infrastructure.persistence` (siguiente bloque)
   - Repositorios SQLite.
5. `infrastructure.importers` (siguiente bloque)
   - Importación de estudiantes desde Excel.
6. `infrastructure.exporters` (siguiente bloque)
   - Exportación a Excel/PDF.
7. `presentation.desktop` (bloques posteriores)
   - UI PySide6.

## 4. Estrategia de importación desde Excel (diseño inicial)
1. Definir plantilla mínima esperada para estudiantes (columnas obligatorias).
2. Crear adaptador de lectura por columnas nominales, no por posiciones rígidas.
3. Estandarizar limpieza:
   - recorte de espacios,
   - normalización de mayúsculas,
   - validación de duplicados.
4. Generar reporte de errores por fila para corrección del usuario.
5. Confirmar importación antes de persistir.

> Nota: en este bloque se documenta estrategia; no se implementa código de importación real.

## 5. Estrategia de exportación a PDF y Excel (diseño inicial)
1. Construir un DTO de reporte desacoplado del dominio.
2. Exportador Excel:
   - plantilla institucional,
   - escritura por filas/columnas,
   - formato básico (encabezados, anchos, notas finales).
3. Exportador PDF:
   - diseño tipo acta/boletín,
   - encabezado institucional,
   - tabla de resultados y observación.
4. Versionar plantillas para evitar ruptura por cambios de formato.

> Nota: en este bloque se documenta estrategia; no se implementa código de exportación real.

## 6. Estructura de carpetas recomendada

```text
UEEH/
├── docs/
│   ├── reglas_negocio.md
│   └── arquitectura_inicial.md
├── src/
│   └── domain/
│       ├── models.py
│       └── calculations.py
├── tests/
│   └── test_calculations.py
└── README_BLOQUE_1.md
```

## 7. Orden sugerido de implementación por bloques

### BLOQUE 1 (actual)
- Dominio, reglas y cálculos puros.
- Pruebas unitarias de reglas críticas.

### BLOQUE 2
- Diseño e implementación de persistencia SQLite (schema + repositorios).
- Casos de uso base (configuración inicial, catálogos, estudiantes, matrículas).

### BLOQUE 3
- Importación de estudiantes desde Excel (validaciones y bitácora de errores).

### BLOQUE 4
- Registro de notas trimestrales y consolidación automática.

### BLOQUE 5
- Exportación de reportes finales a Excel/PDF.

### BLOQUE 6
- Interfaz de escritorio PySide6 (minimalista y profesional).

### BLOQUE 7
- Endurecimiento: empaquetado, respaldo, auditoría básica y pruebas de aceptación.
