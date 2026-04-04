"""Servicio de matrículas."""

from __future__ import annotations

import sqlite3
import uuid

from src.infrastructure.persistence.repositories import MatriculasRepository


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
