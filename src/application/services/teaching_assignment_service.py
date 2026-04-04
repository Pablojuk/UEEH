"""Servicio de asignaciones académicas."""

from __future__ import annotations

import sqlite3
import uuid

from src.infrastructure.persistence.repositories import AsignacionesDocenteRepository


class TeachingAssignmentService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.repo = AsignacionesDocenteRepository(connection)

    def crear_asignacion(self, data: dict) -> tuple[bool, str]:
        required = ["docente_id", "asignatura_id", "curso_id", "paralelo_id", "periodo_id"]
        if not all(str(data.get(field, "")).strip() for field in required):
            return False, "Docente, asignatura, curso, paralelo y período son obligatorios"

        if self._es_duplicada(data):
            return False, "Asignación duplicada para la misma combinación académica"

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

        self.repo.actualizar(assignment_id, merged)
        return True, "Asignación actualizada"

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
