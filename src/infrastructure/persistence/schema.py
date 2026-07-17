"""Definición de esquema SQLite para BLOQUE 2."""

from __future__ import annotations

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS configuracion_sistema (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        clave_inicial_hash TEXT,
        clave_inicial_salt TEXT,
        primer_uso_completado INTEGER NOT NULL DEFAULT 0 CHECK (primer_uso_completado IN (0, 1)),
        escala_maxima REAL NOT NULL DEFAULT 10.0,
        escala_minima REAL NOT NULL DEFAULT 0.0,
        correo_recuperacion TEXT,
        licencia_activada INTEGER NOT NULL DEFAULT 0 CHECK (licencia_activada IN (0, 1)),
        fecha_primer_inicio TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS institucion (
        id_institucion TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        jornada TEXT NOT NULL,
        provincia TEXT,
        ciudad TEXT,
        parroquia TEXT,
        direccion TEXT,
        codigo_amie TEXT,
        rector TEXT,
        vicerrector TEXT,
        inspector TEXT,
        logo_ministerio_path TEXT,
        logo_path TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS docentes (
        id_docente TEXT PRIMARY KEY,
        nombres TEXT NOT NULL,
        apellidos TEXT NOT NULL,
        identificacion TEXT NOT NULL UNIQUE,
        titulo TEXT,
        activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS cursos (
        id_curso TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        nivel TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS paralelos (
        id_paralelo TEXT PRIMARY KEY,
        nombre TEXT NOT NULL UNIQUE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS asignaturas (
        id_asignatura TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        codigo TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS periodos_lectivos (
        id_periodo TEXT PRIMARY KEY,
        anio_inicio INTEGER NOT NULL,
        anio_fin INTEGER NOT NULL,
        fecha_inicio TEXT,
        fecha_fin TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS estudiantes (
        id_estudiante TEXT PRIMARY KEY,
        codigo TEXT NOT NULL UNIQUE,
        apellidos TEXT NOT NULL,
        nombres TEXT NOT NULL,
        identificacion TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS matriculas (
        id_matricula TEXT PRIMARY KEY,
        estudiante_id TEXT NOT NULL,
        curso_id TEXT NOT NULL,
        paralelo_id TEXT NOT NULL,
        periodo_id TEXT NOT NULL,
        numero_lista INTEGER,
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id_estudiante),
        FOREIGN KEY (curso_id) REFERENCES cursos(id_curso),
        FOREIGN KEY (paralelo_id) REFERENCES paralelos(id_paralelo),
        FOREIGN KEY (periodo_id) REFERENCES periodos_lectivos(id_periodo)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS asignaciones_docente (
        id_asignacion TEXT PRIMARY KEY,
        docente_id TEXT NOT NULL,
        asignatura_id TEXT NOT NULL,
        curso_id TEXT NOT NULL,
        paralelo_id TEXT NOT NULL,
        periodo_id TEXT NOT NULL,
        FOREIGN KEY (docente_id) REFERENCES docentes(id_docente),
        FOREIGN KEY (asignatura_id) REFERENCES asignaturas(id_asignatura),
        FOREIGN KEY (curso_id) REFERENCES cursos(id_curso),
        FOREIGN KEY (paralelo_id) REFERENCES paralelos(id_paralelo),
        FOREIGN KEY (periodo_id) REFERENCES periodos_lectivos(id_periodo)
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS grade_records (
        id_registro TEXT PRIMARY KEY,
        estudiante_id TEXT NOT NULL,
        asignacion_id TEXT NOT NULL,
        trimestre_num INTEGER NOT NULL CHECK (trimestre_num IN (1,2,3)),
        actividad_1 REAL,
        mejora_1 REAL,
        actividad_2 REAL,
        mejora_2 REAL,
        actividad_3 REAL,
        mejora_3 REAL,
        proyecto REAL,
        evaluacion REAL,
        refuerzo REAL,
        mejora_sumativa REAL,
        promedio_formativo REAL,
        promedio_sumativo REAL,
        nota_trimestral REAL,
        actividades_json TEXT,
        mejoras_json TEXT,
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id_estudiante),
        FOREIGN KEY (asignacion_id) REFERENCES asignaciones_docente(id_asignacion),
        UNIQUE (estudiante_id, asignacion_id, trimestre_num)
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS final_supplementary (
        id_supletorio TEXT PRIMARY KEY,
        estudiante_id TEXT NOT NULL,
        asignacion_id TEXT NOT NULL,
        nota_supletorio REAL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id_estudiante),
        FOREIGN KEY (asignacion_id) REFERENCES asignaciones_docente(id_asignacion),
        UNIQUE (estudiante_id, asignacion_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS trimestres (
        id_trimestre TEXT PRIMARY KEY,
        numero INTEGER NOT NULL CHECK (numero IN (1, 2, 3)),
        nombre TEXT NOT NULL,
        periodo_id TEXT NOT NULL,
        UNIQUE (periodo_id, numero),
        FOREIGN KEY (periodo_id) REFERENCES periodos_lectivos(id_periodo)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS grade_activity_config (
        id_config TEXT PRIMARY KEY,
        asignacion_id TEXT NOT NULL,
        trimestre_num INTEGER NOT NULL CHECK (trimestre_num IN (1,2,3)),
        numero_actividades INTEGER NOT NULL CHECK (numero_actividades >= 1 AND numero_actividades <= 20),
        metadata_json TEXT,
        UNIQUE (asignacion_id, trimestre_num),
        FOREIGN KEY (asignacion_id) REFERENCES asignaciones_docente(id_asignacion)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS acompanamiento_evaluaciones (
        id_evaluacion TEXT PRIMARY KEY,
        asignacion_id TEXT NOT NULL,
        trimestre_num INTEGER NOT NULL CHECK (trimestre_num IN (1,2,3)),
        estudiante_id TEXT NOT NULL,
        habilidad_clave TEXT NOT NULL,
        valor TEXT NOT NULL CHECK (valor IN ('Siempre', 'Frecuentemente', 'Ocasionalmente', 'Nunca')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (asignacion_id, trimestre_num, estudiante_id, habilidad_clave),
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id_estudiante),
        FOREIGN KEY (asignacion_id) REFERENCES asignaciones_docente(id_asignacion)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS acompanamiento_habilidades_config (
        id_config TEXT PRIMARY KEY,
        asignacion_id TEXT NOT NULL,
        trimestre_num INTEGER NOT NULL CHECK (trimestre_num IN (1,2,3)),
        habilidad_clave TEXT NOT NULL,
        visible INTEGER NOT NULL DEFAULT 1 CHECK (visible IN (0, 1)),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (asignacion_id, trimestre_num, habilidad_clave),
        FOREIGN KEY (asignacion_id) REFERENCES asignaciones_docente(id_asignacion)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS animacion_lectura_evaluaciones (
        id_evaluacion TEXT PRIMARY KEY,
        asignacion_id TEXT NOT NULL,
        trimestre_num INTEGER NOT NULL CHECK (trimestre_num IN (1,2,3)),
        nivel TEXT NOT NULL,
        estudiante_id TEXT NOT NULL,
        notas_indicadores_json TEXT,
        valor_promedio REAL,
        cualitativo TEXT,
        cualitativo_1 TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (asignacion_id, trimestre_num, estudiante_id),
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id_estudiante),
        FOREIGN KEY (asignacion_id) REFERENCES asignaciones_docente(id_asignacion)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS orientacion_vocacional_evaluaciones (
        id_evaluacion TEXT PRIMARY KEY,
        asignacion_id TEXT NOT NULL,
        trimestre_num INTEGER NOT NULL CHECK (trimestre_num IN (1,2,3)),
        curso_clave TEXT NOT NULL CHECK (curso_clave IN ('8', '9', '10')),
        estudiante_id TEXT NOT NULL,
        respuestas_json TEXT NOT NULL,
        puntaje_total INTEGER,
        calificacion TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (asignacion_id, trimestre_num, estudiante_id),
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id_estudiante),
        FOREIGN KEY (asignacion_id) REFERENCES asignaciones_docente(id_asignacion)
    );
    """,
)

INDEX_STATEMENTS: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_estudiantes_codigo ON estudiantes(codigo);",
    "CREATE INDEX IF NOT EXISTS idx_docentes_activo ON docentes(activo);",
    "CREATE INDEX IF NOT EXISTS idx_matriculas_estudiante ON matriculas(estudiante_id);",
    "CREATE INDEX IF NOT EXISTS idx_matriculas_periodo ON matriculas(periodo_id);",
    "CREATE INDEX IF NOT EXISTS idx_asignaciones_docente_docente ON asignaciones_docente(docente_id);",
    "CREATE INDEX IF NOT EXISTS idx_asignaciones_docente_periodo ON asignaciones_docente(periodo_id);",
    "CREATE INDEX IF NOT EXISTS idx_trimestres_periodo ON trimestres(periodo_id);",
    "CREATE INDEX IF NOT EXISTS idx_grade_records_assignment_trimestre ON grade_records(asignacion_id, trimestre_num);",
    "CREATE INDEX IF NOT EXISTS idx_final_supp_assignment ON final_supplementary(asignacion_id);",
    "CREATE INDEX IF NOT EXISTS idx_grade_activity_config_assignment ON grade_activity_config(asignacion_id, trimestre_num);",
    "CREATE INDEX IF NOT EXISTS idx_acompanamiento_eval_asig_trim ON acompanamiento_evaluaciones(asignacion_id, trimestre_num);",
    "CREATE INDEX IF NOT EXISTS idx_acompanamiento_eval_estudiante ON acompanamiento_evaluaciones(estudiante_id);",
    "CREATE INDEX IF NOT EXISTS idx_acompanamiento_cfg_asig_trim ON acompanamiento_habilidades_config(asignacion_id, trimestre_num);",
    "CREATE INDEX IF NOT EXISTS idx_animacion_eval_asig_trim ON animacion_lectura_evaluaciones(asignacion_id, trimestre_num);",
    "CREATE INDEX IF NOT EXISTS idx_orientacion_eval_asig_trim ON orientacion_vocacional_evaluaciones(asignacion_id, trimestre_num);",
    "CREATE INDEX IF NOT EXISTS idx_matriculas_contexto_lista ON matriculas(curso_id, paralelo_id, periodo_id, numero_lista);",
    "CREATE INDEX IF NOT EXISTS idx_attendance_assignment_date_student ON attendance_records(assignment_id, date, student_id);",
    "CREATE INDEX IF NOT EXISTS idx_attendance_assignment_student_status_date ON attendance_records(assignment_id, student_id, status, date);",
    "CREATE INDEX IF NOT EXISTS idx_attendance_justifications_assignment_student_date ON attendance_justifications(assignment_id, student_id, date);",
)


def get_schema_statements() -> tuple[str, ...]:
    """Retorna las sentencias SQL para crear tablas e índices."""
    return SCHEMA_STATEMENTS + INDEX_STATEMENTS
