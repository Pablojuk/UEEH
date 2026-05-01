"""Servicio de asignaciones académicas."""

from __future__ import annotations

import sqlite3
import uuid
import unicodedata

from src.infrastructure.persistence.repositories import AsignacionesDocenteRepository


class TeachingAssignmentService:
    ORIENTATION_SUBJECT_NAME = "orientacion vocacional y profesional"
    ORIENTATION_ALLOWED_COURSE_KEYS = {"8", "9", "10"}
    ORIENTATION_VALIDATION_MESSAGE = (
        "La asignatura Orientación Vocacional y Profesional solo corresponde a 8vo, 9no y 10mo de Educación General Básica Superior."
    )

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.repo = AsignacionesDocenteRepository(connection)

    def crear_asignacion(self, data: dict) -> tuple[bool, str]:
        required = ["docente_id", "asignatura_id", "curso_id", "paralelo_id", "periodo_id"]
        if not all(str(data.get(field, "")).strip() for field in required):
            return False, "Docente, asignatura, curso, paralelo y período son obligatorios"

        if self._es_duplicada(data):
            return False, "Asignación duplicada para la misma combinación académica"
        valid, validation_message = self._validar_orientacion_vocacional_por_curso(data)
        if not valid:
            return False, validation_message

        payload = {
            "id_asignacion": data.get("id_asignacion") or str(uuid.uuid4()),
            "docente_id": data["docente_id"],
            "asignatura_id": data["asignatura_id"],
            "curso_id": data["curso_id"],
            "paralelo_id": data["paralelo_id"],
            "periodo_id": data["periodo_id"],
        }
        self.repo.crear(payload)
        return True, "Asignación creada"

    def obtener_asignacion_por_id(self, assignment_id: str) -> dict | None:
        return self.repo.obtener_por_id(assignment_id)

    def listar_asignaciones(self) -> list[dict]:
        return self.repo.listar()

    def buscar_asignaciones(self, query: str) -> list[dict]:
        q = query.strip().lower()
        if not q:
            return self.listar_asignaciones()

        return [
            row
            for row in self.listar_asignaciones()
            if q in row.get("docente_id", "").lower()
            or q in row.get("asignatura_id", "").lower()
            or q in row.get("curso_id", "").lower()
            or q in row.get("paralelo_id", "").lower()
            or q in row.get("periodo_id", "").lower()
        ]

    def listar_por_docente(self, docente_id: str) -> list[dict]:
        return [row for row in self.listar_asignaciones() if row.get("docente_id") == docente_id]

    def listar_por_grupo(self, curso_id: str, paralelo_id: str, periodo_id: str) -> list[dict]:
        return [
            row
            for row in self.listar_asignaciones()
            if row.get("curso_id") == curso_id
            and row.get("paralelo_id") == paralelo_id
            and row.get("periodo_id") == periodo_id
        ]

    def actualizar_asignacion(self, assignment_id: str, data: dict) -> tuple[bool, str]:
        existing = self.repo.obtener_por_id(assignment_id)
        if not existing:
            return False, "Asignación no encontrada"

        merged = {**existing, **data}
        if self._es_duplicada(merged, exclude_id=assignment_id):
            return False, "Asignación duplicada para la misma combinación académica"
        valid, validation_message = self._validar_orientacion_vocacional_por_curso(merged)
        if not valid:
            return False, validation_message

        self.repo.actualizar(assignment_id, merged)
        return True, "Asignación actualizada"

    def eliminar_asignacion(self, assignment_id: str) -> tuple[bool, str]:
        existing = self.repo.obtener_por_id(assignment_id)
        if not existing:
            return False, "Asignación no encontrada"
        self.repo.eliminar(assignment_id)
        return True, "Asignación eliminada"

    def _es_duplicada(self, data: dict, exclude_id: str | None = None) -> bool:
        for row in self.listar_asignaciones():
            if exclude_id and row.get("id_asignacion") == exclude_id:
                continue
            if (
                row.get("docente_id") == data.get("docente_id")
                and row.get("asignatura_id") == data.get("asignatura_id")
                and row.get("curso_id") == data.get("curso_id")
                and row.get("paralelo_id") == data.get("paralelo_id")
                and row.get("periodo_id") == data.get("periodo_id")
            ):
                return True
        return False

    def _validar_orientacion_vocacional_por_curso(self, data: dict) -> tuple[bool, str]:
        subject_id = str(data.get("asignatura_id") or "").strip()
        course_id = str(data.get("curso_id") or "").strip()
        if not subject_id or not course_id:
            return True, ""

        subject_row = self.connection.execute(
            "SELECT nombre FROM asignaturas WHERE id_asignatura = ?",
            (subject_id,),
        ).fetchone()
        course_row = self.connection.execute(
            "SELECT nombre FROM cursos WHERE id_curso = ?",
            (course_id,),
        ).fetchone()
        if not subject_row or not course_row:
            return True, ""

        subject_name = self._normalize_text(str(subject_row["nombre"] or ""))
        if subject_name != self.ORIENTATION_SUBJECT_NAME:
            return True, ""

        course_key = self._detect_orientation_course_key(str(course_row["nombre"] or ""))
        if course_key not in self.ORIENTATION_ALLOWED_COURSE_KEYS:
            return False, self.ORIENTATION_VALIDATION_MESSAGE
        return True, ""

    @classmethod
    def _detect_orientation_course_key(cls, course_name: str) -> str | None:
        normalized = cls._normalize_text(course_name)
        tokens = set(normalized.split())
        if any(token in tokens for token in {"8", "8vo", "octavo"}):
            return "8"
        if any(token in tokens for token in {"9", "9no", "noveno"}):
            return "9"
        if any(token in tokens for token in {"10", "10mo", "decimo"}):
            return "10"
        return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFD", str(value or "").strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())
