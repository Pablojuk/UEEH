# Reglas de Negocio y Definición de Dominio

## 1. Propósito del sistema
Construir una aplicación de escritorio en Python para reemplazar el libro Excel con macros usado para registro y consolidación de notas, manteniendo la lógica académica actual (fórmulas y reglas) y mejorando mantenibilidad, trazabilidad y escalabilidad para múltiples docentes.

## 2. Alcance funcional (BLOQUE 1)
Este bloque **define** el dominio y la especificación funcional/técnica inicial. Incluye:

- Definición de entidades del dominio académico.
- Reglas de cálculo de notas (trimestres, cualitativo, observación, supletorio).
- Mapa de equivalencia entre hojas Excel y módulos de aplicación.
- Riesgos técnicos y supuestos explícitos.

No incluye en este bloque:

- Interfaz gráfica.
- Persistencia SQLite implementada.
- CRUD.
- Importación/exportación implementada.
- Reportes finales implementados.

## 3. Actores del sistema
1. **Docente**
   - Registra calificaciones por estudiante.
   - Revisa resúmenes trimestrales/finales.
   - Solicita exportación de reportes.

2. **Responsable de configuración inicial**
   - Define clave única inicial del sistema.
   - Configura datos institucionales y catálogos base.

3. **Coordinación académica (actor de negocio, no técnico)**
   - Define lineamientos de evaluación y validez de reportes.

## 4. Entidades del dominio
- **ConfiguracionSistema**: parámetros globales (clave inicial, escala, banderas de primer uso).
- **Institucion**: datos institucionales.
- **Docente**: información de profesor.
- **Curso**: nivel/curso académico.
- **Paralelo**: división del curso (A, B, etc.).
- **Asignatura**: materia.
- **PeriodoLectivo**: año lectivo y fechas relevantes.
- **Estudiante**: identidad del estudiante.
- **Matricula**: relación estudiante-curso-paralelo-periodo.
- **AsignacionDocente**: relación docente-asignatura-curso-paralelo-periodo.
- **Trimestre**: unidad temporal de evaluación (1, 2, 3).
- **RegistroActividad**: actividad formativa con base/mejora.
- **RegistroSumativo**: evaluación sumativa con base/mejora.
- **ResumenTrimestral**: consolidado de un trimestre por estudiante.
- **ResumenFinal**: consolidado anual (promedio, cualitativo, observación, estado).
- **Supletorio**: evaluación suplementaria y efecto sobre nota final.

## 5. Reglas del negocio

### 5.1 Estructura académica
1. El periodo tiene **3 trimestres**.
2. Cada trimestre contiene componente **formativo** y **sumativo**.

### 5.2 Ponderación trimestral
3. Nota trimestral = (formativo × 0.70) + (sumativo × 0.30).

### 5.3 Regla de mejora
4. Cada actividad puede tener **nota base** y **nota de mejora**.
5. Si mejora > base: nota resuelta = `TRUNC((base + mejora) / 2, 2)`.
6. Si mejora <= base: nota resuelta = base.
7. Si no existe mejora: nota resuelta = base.

### 5.4 Promedios por componente
8. Formativo = promedio aritmético de actividades formativas resueltas.
9. Sumativo = promedio aritmético de evaluaciones sumativas resueltas.
10. Si no hay registros válidos en un componente, se usa 0.0 como criterio técnico inicial (supuesto de BLOQUE 1).

### 5.5 Cierre trimestral y anual
11. Nota final trimestral se redondea/trunca según función definida en dominio (truncado a 2 decimales para coherencia con Excel).
12. Promedio anual final = promedio de 3 trimestres, redondeado a 2 decimales.

### 5.6 Escala cualitativa
13. Conversión nota→cualitativo:
    - >= 9.5: A+
    - >= 8.5: A-
    - >= 7.5: B+
    - >= 6.5: B-
    - >= 5.5: C+
    - >= 4.5: C-
    - >= 3.5: D+
    - >= 2.5: D-
    - >= 1.5: E+
    - >= 0.5: E-
14. Si nota < 0.5, el sistema devolverá `SIN_ESCALA` como valor técnico de resguardo (supuesto explícito).

### 5.7 Observación final
15. Si promedio final >= 7: `APB`.
16. Si promedio final > 4 y < 7: `SPL`.
17. Si promedio final >= 1 y <= 4: `REP`.
18. Si promedio final < 1: `REP` como criterio de seguridad académica (supuesto explícito para evitar valores vacíos).

### 5.8 Supletorio
19. Si nota final >= 7: se conserva.
20. Si nota final < 7 y supletorio >= 7: nota definitiva = 7.
21. Si nota final < 7 y supletorio < 7: mantiene nota final (no aprueba).

## 6. Mapa de equivalencia (Excel → App)

| Excel actual | Rol en Excel | Módulo objetivo en app |
|---|---|---|
| `DS` | Datos institucionales, jornada, docente, año, parámetros | Configuración del sistema + catálogos base (`domain` + futuro `application/config`) |
| `TABLAS` | Catálogos de soporte | Catálogos normalizados (`domain` + futuro `infrastructure/repositories`) |
| `M1-M13` | Captura principal de notas por estudiante | Módulo de registro de calificaciones (`application/grades`) |
| `I1-I13` | Resumen trimestral/final/cualitativo/observación/supletorio | Motor de cálculo académico (`domain/calculations`) + casos de uso de consolidación |
| `R1-R13` | Reportes imprimibles | Módulo de reportes/exportación (`application/reports` + `infrastructure/exporters`) |

## 7. Riesgos técnicos detectados
1. **Diferencias de precisión** entre Excel y Python (TRUNC vs ROUND) pueden alterar décimas.
2. **Inconsistencia de plantillas Excel** de entrada (columnas cambiadas por usuarios).
3. **Datos históricos incompletos** (mejoras vacías, celdas con texto, filas fusionadas).
4. **Acoplamiento implícito a estructura M1..M13** que no escalaría si cambia la malla.
5. **Concurrencia local** (varios docentes en PCs distintos) sin sincronización central en v1.
6. **Ausencia de login** requiere política clara de clave inicial y resguardo local.

## 8. Supuestos explícitos
1. Escala numérica esperada: 0.00 a 10.00.
2. Las notas inválidas (fuera de rango) serán validadas en capas superiores en siguientes bloques.
3. El BLOQUE 1 solo define reglas y modelos; no persiste datos.
4. Se prioriza compatibilidad con la lógica de fórmulas de Excel por encima del diseño visual previo.
5. La clave única inicial se almacenará de forma segura en próximos bloques (hash + configuración local).
6. Para componentes sin registros, promedio = 0.0 (hasta definir política institucional alternativa).
