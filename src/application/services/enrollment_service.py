"""Servicio de matrículas."""

from __future__ import annotations

import sqlite3
import unicodedata
import uuid
from dataclasses import dataclass
from typing import Any

from src.infrastructure.persistence.repositories import MatriculasRepository


@dataclass(frozen=True)
class AssignmentEnrollmentMatch:
    """Contexto y matrículas que coinciden exactamente con una asignación."""

    context: dict[str, Any] | None
    students: list[dict[str, Any]]

    @property
    def validation_message(self) -> str:
        if self.context is None or self.students:
            return ""
        course = self.context.get("curso_nombre") or self.context.get("curso_id") or "curso desconocido"
        parallel = self.context.get("paralelo_nombre") or self.context.get("paralelo_id") or "desconocido"
        period = self.context.get("periodo_id") or "desconocido"
        return (
            f"No se encontraron estudiantes matriculados para {course}, "
            f"paralelo {parallel}, período {period}."
        )


def load_students_for_assignment(
    connection: sqlite3.Connection,
    assignment_id: str,
    *,
    alphabetical: bool = False,
) -> AssignmentEnrollmentMatch:
    """Obtiene estudiantes por los tres IDs exactos de la asignación."""

    context_row = connection.execute(
        """
        SELECT
            a.id_asignacion,
            a.curso_id,
            a.paralelo_id,
            a.periodo_id,
            c.nombre AS curso_nombre,
            p.nombre AS paralelo_nombre
        FROM asignaciones_docente a
        LEFT JOIN cursos c ON c.id_curso = a.curso_id
        LEFT JOIN paralelos p ON p.id_paralelo = a.paralelo_id
        WHERE a.id_asignacion = ?
        """,
        (assignment_id,),
    ).fetchone()
    if context_row is None:
        return AssignmentEnrollmentMatch(context=None, students=[])

    context = dict(context_row)
    students = [
        dict(row)
        for row in connection.execute(
            """
            SELECT
                e.id_estudiante,
                e.codigo,
                e.apellidos,
                e.nombres,
                m.numero_lista
            FROM matriculas m
            JOIN estudiantes e ON e.id_estudiante = m.estudiante_id
            WHERE m.curso_id = ? AND m.paralelo_id = ? AND m.periodo_id = ?
            ORDER BY
                CASE WHEN m.numero_lista IS NULL THEN 1 ELSE 0 END,
                m.numero_lista,
                e.apellidos,
                e.nombres
            """,
            (context["curso_id"], context["paralelo_id"], context["periodo_id"]),
        ).fetchall()
    ]
    if alphabetical:
        students.sort(key=student_alphabetical_key)
    return AssignmentEnrollmentMatch(context=context, students=students)


def student_alphabetical_key(student: dict[str, Any]) -> tuple[str, str, str, str]:
    """Genera una clave estable que ignora mayúsculas, minúsculas y tildes."""

    def normalize(value: Any) -> str:
        decomposed = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()

    return (
        normalize(student.get("apellidos")),
        normalize(student.get("nombres")),
        normalize(student.get("codigo")),
        normalize(student.get("id_estudiante") or student.get("estudiante_id")),
    )


class EnrollmentService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.repo = MatriculasRepository(connection)

    def crear_matricula(self, data: dict) -> tuple[bool, str]:
        required = ["estudiante_id", "curso_id", "paralelo_id", "periodo_id"]
        if not all(str(data.get(field, "")).strip() for field in required):
            return False, "Estudiante, curso, paralelo y período son obligatorios"

        if self._es_duplicada(data):
            return False, "Matrícula duplicada para estudiante en mismo curso/paralelo/período"

        payload = {
            "id_matricula": data.get("id_matricula") or str(uuid.uuid4()),
            "estudiante_id": data["estudiante_id"],
            "curso_id": data["curso_id"],
            "paralelo_id": data["paralelo_id"],
            "periodo_id": data["periodo_id"],
            "numero_lista": data.get("numero_lista"),
        }
        self.repo.crear(payload)
        return True, "Matrícula creada"

    def crear_matriculas_masivas(self, student_ids: list[str], context: dict) -> tuple[bool, str]:
        if not student_ids:
            return False, "No se recibieron estudiantes para matrícula masiva"
        required = ["curso_id", "paralelo_id", "periodo_id"]
        if not all(str(context.get(field, "")).strip() for field in required):
            return False, "Curso, paralelo y período son obligatorios"

        creadas = 0
        duplicadas = 0
        for student_id in student_ids:
            payload = {
                "estudiante_id": student_id,
                "curso_id": context["curso_id"],
                "paralelo_id": context["paralelo_id"],
                "periodo_id": context["periodo_id"],
            }
            ok, _ = self.crear_matricula(payload)
            if ok:
                creadas += 1
            else:
                duplicadas += 1
        if creadas == 0:
            return False, "No se crearon matrículas nuevas; los estudiantes ya estaban registrados en ese contexto"
        return True, f"Matrículas creadas: {creadas}. Omitidas por duplicado: {duplicadas}."

    def obtener_matricula_por_id(self, enrollment_id: str) -> dict | None:
        return self.repo.obtener_por_id(enrollment_id)

    def listar_matriculas(self) -> list[dict]:
        return self.repo.listar()

    def buscar_matriculas(self, query: str) -> list[dict]:
        q = query.strip().lower()
        if not q:
            return self.listar_matriculas()
        return [
            row
            for row in self.listar_matriculas()
            if q in row.get("estudiante_id", "").lower()
            or q in row.get("curso_id", "").lower()
            or q in row.get("paralelo_id", "").lower()
            or q in row.get("periodo_id", "").lower()
        ]

    def listar_por_grupo(self, curso_id: str, paralelo_id: str, periodo_id: str) -> list[dict]:
        return [
            row
            for row in self.listar_matriculas()
            if row.get("curso_id") == curso_id
            and row.get("paralelo_id") == paralelo_id
            and row.get("periodo_id") == periodo_id
        ]

    def actualizar_matricula(self, enrollment_id: str, data: dict) -> tuple[bool, str]:
        existing = self.repo.obtener_por_id(enrollment_id)
        if not existing:
            return False, "Matrícula no encontrada"

        merged = {**existing, **data}
        if self._es_duplicada(merged, exclude_id=enrollment_id):
            return False, "Matrícula duplicada para estudiante en mismo curso/paralelo/período"

        self.repo.actualizar(enrollment_id, merged)
        return True, "Matrícula actualizada"

    def eliminar_matricula(self, enrollment_id: str) -> tuple[bool, str]:
        existing = self.repo.obtener_por_id(enrollment_id)
        if not existing:
            return False, "Matrícula no encontrada"
        self.repo.eliminar(enrollment_id)
        return True, "Matrícula eliminada"

    def _es_duplicada(self, data: dict, exclude_id: str | None = None) -> bool:
        for row in self.listar_matriculas():
            if exclude_id and row.get("id_matricula") == exclude_id:
                continue
            if (
                row.get("estudiante_id") == data.get("estudiante_id")
                and row.get("curso_id") == data.get("curso_id")
                and row.get("paralelo_id") == data.get("paralelo_id")
                and row.get("periodo_id") == data.get("periodo_id")
            ):
                return True
        return False
