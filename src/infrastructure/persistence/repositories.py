"""Repositorios SQLite base para BLOQUE 2."""

from __future__ import annotations

import sqlite3
from typing import Any


class SQLiteRepository:
    """Repositorio base con operaciones CRUD mínimas."""

    table_name: str
    id_field: str
    fields: tuple[str, ...]

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def crear(self, data: dict[str, Any]) -> None:
        columnas = ", ".join(self.fields)
        placeholders = ", ".join(["?"] * len(self.fields))
        valores = [data[campo] for campo in self.fields]
        query = f"INSERT INTO {self.table_name} ({columnas}) VALUES ({placeholders})"
        with self.connection:
            self.connection.execute(query, valores)

    def obtener_por_id(self, id_value: Any) -> dict[str, Any] | None:
        query = f"SELECT * FROM {self.table_name} WHERE {self.id_field} = ?"
        cursor = self.connection.execute(query, (id_value,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def listar(self) -> list[dict[str, Any]]:
        query = f"SELECT * FROM {self.table_name} ORDER BY {self.id_field}"
        cursor = self.connection.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def actualizar(self, id_value: Any, data: dict[str, Any]) -> None:
        campos_actualizables = [campo for campo in self.fields if campo != self.id_field and campo in data]
        if not campos_actualizables:
            return

        set_clause = ", ".join([f"{campo} = ?" for campo in campos_actualizables])
        valores = [data[campo] for campo in campos_actualizables]
        valores.append(id_value)

        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.id_field} = ?"
        with self.connection:
            self.connection.execute(query, valores)

    def eliminar(self, id_value: Any) -> None:
        query = f"DELETE FROM {self.table_name} WHERE {self.id_field} = ?"
        with self.connection:
            self.connection.execute(query, (id_value,))


class ConfiguracionSistemaRepository(SQLiteRepository):
    table_name = "configuracion_sistema"
    id_field = "id"
    fields = (
        "id",
        "clave_inicial_hash",
        "clave_inicial_salt",
        "primer_uso_completado",
        "escala_maxima",
        "escala_minima",
    )


class InstitucionRepository(SQLiteRepository):
    table_name = "institucion"
    id_field = "id_institucion"
    fields = (
        "id_institucion",
        "nombre",
        "jornada",
        "provincia",
        "ciudad",
        "parroquia",
        "direccion",
        "codigo_amie",
        "rector",
        "vicerrector",
        "inspector",
        "logo_ministerio_path",
        "logo_path",
    )


class DocentesRepository(SQLiteRepository):
    table_name = "docentes"
    id_field = "id_docente"
    fields = ("id_docente", "nombres", "apellidos", "identificacion", "titulo", "activo")


class CursosRepository(SQLiteRepository):
    table_name = "cursos"
    id_field = "id_curso"
    fields = ("id_curso", "nombre", "nivel")


class ParalelosRepository(SQLiteRepository):
    table_name = "paralelos"
    id_field = "id_paralelo"
    fields = ("id_paralelo", "nombre")


class AsignaturasRepository(SQLiteRepository):
    table_name = "asignaturas"
    id_field = "id_asignatura"
    fields = ("id_asignatura", "nombre", "codigo")


class PeriodosLectivosRepository(SQLiteRepository):
    table_name = "periodos_lectivos"
    id_field = "id_periodo"
    fields = ("id_periodo", "anio_inicio", "anio_fin", "fecha_inicio", "fecha_fin")


class EstudiantesRepository(SQLiteRepository):
    table_name = "estudiantes"
    id_field = "id_estudiante"
    fields = ("id_estudiante", "codigo", "apellidos", "nombres", "identificacion")


class MatriculasRepository(SQLiteRepository):
    table_name = "matriculas"
    id_field = "id_matricula"
    fields = (
        "id_matricula",
        "estudiante_id",
        "curso_id",
        "paralelo_id",
        "periodo_id",
        "numero_lista",
    )


class AsignacionesDocenteRepository(SQLiteRepository):
    table_name = "asignaciones_docente"
    id_field = "id_asignacion"
    fields = (
        "id_asignacion",
        "docente_id",
        "asignatura_id",
        "curso_id",
        "paralelo_id",
        "periodo_id",
    )


class TrimestresRepository(SQLiteRepository):
    table_name = "trimestres"
    id_field = "id_trimestre"
    fields = ("id_trimestre", "numero", "nombre", "periodo_id")


class GradeRecordsRepository(SQLiteRepository):
    table_name = "grade_records"
    id_field = "id_registro"
    fields = (
        "id_registro",
        "estudiante_id",
        "asignacion_id",
        "trimestre_num",
        "actividad_1",
        "mejora_1",
        "actividad_2",
        "mejora_2",
        "actividad_3",
        "mejora_3",
        "proyecto",
        "evaluacion",
        "refuerzo",
        "mejora_sumativa",
        "promedio_formativo",
        "promedio_sumativo",
        "nota_trimestral",
        "actividades_json",
        "mejoras_json",
    )


class GradeActivityConfigRepository(SQLiteRepository):
    table_name = "grade_activity_config"
    id_field = "id_config"
    fields = ("id_config", "asignacion_id", "trimestre_num", "numero_actividades", "metadata_json")


class FinalSupplementaryRepository(SQLiteRepository):
    table_name = "final_supplementary"
    id_field = "id_supletorio"
    fields = (
        "id_supletorio",
        "estudiante_id",
        "asignacion_id",
        "nota_supletorio",
    )


class ClassroomAccompanimentRepository(SQLiteRepository):
    table_name = "acompanamiento_evaluaciones"
    id_field = "id_evaluacion"
    fields = (
        "id_evaluacion",
        "asignacion_id",
        "trimestre_num",
        "estudiante_id",
        "habilidad_clave",
        "valor",
    )


class ClassroomAccompanimentSkillConfigRepository(SQLiteRepository):
    table_name = "acompanamiento_habilidades_config"
    id_field = "id_config"
    fields = (
        "id_config",
        "asignacion_id",
        "trimestre_num",
        "habilidad_clave",
        "visible",
    )


class AnimationReadingEvaluationRepository(SQLiteRepository):
    table_name = "animacion_lectura_evaluaciones"
    id_field = "id_evaluacion"
    fields = (
        "id_evaluacion",
        "asignacion_id",
        "trimestre_num",
        "nivel",
        "estudiante_id",
        "notas_indicadores_json",
        "valor_promedio",
        "cualitativo",
        "cualitativo_1",
    )


class VocationalOrientationEvaluationRepository(SQLiteRepository):
    table_name = "orientacion_vocacional_evaluaciones"
    id_field = "id_evaluacion"
    fields = (
        "id_evaluacion",
        "asignacion_id",
        "trimestre_num",
        "curso_clave",
        "estudiante_id",
        "respuestas_json",
        "puntaje_total",
        "calificacion",
    )
