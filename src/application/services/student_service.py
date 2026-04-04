"""Servicio de gestión de estudiantes."""

from __future__ import annotations

import sqlite3
import uuid

from src.infrastructure.persistence.repositories import EstudiantesRepository


class StudentService:
    """Casos de uso básicos para estudiantes."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.repo = EstudiantesRepository(connection)

    def crear_estudiante(self, data: dict) -> tuple[bool, str]:
        normalized = self._normalize_payload(data)
        duplicate_reason = self.validar_duplicado(normalized)
        if duplicate_reason:
            return False, duplicate_reason

        self.repo.crear(normalized)
        return True, "Estudiante creado"

    def obtener_estudiante_por_id(self, student_id: str) -> dict | None:
        return self.repo.obtener_por_id(student_id)

    def listar_estudiantes(self) -> list[dict]:
        return self.repo.listar()

    def buscar_estudiantes(self, query: str) -> list[dict]:
        query_norm = query.strip().lower()
        if not query_norm:
            return self.listar_estudiantes()

        return [
            row
            for row in self.listar_estudiantes()
            if query_norm in row.get("nombres", "").lower()
            or query_norm in row.get("apellidos", "").lower()
            or query_norm in (row.get("identificacion") or "").lower()
            or query_norm in (row.get("codigo") or "").lower()
        ]

    def actualizar_estudiante(self, student_id: str, data: dict) -> tuple[bool, str]:
        existing = self.obtener_estudiante_por_id(student_id)
        if not existing:
            return False, "Estudiante no encontrado"

        merged = {
            **existing,
            **{k: v for k, v in data.items() if v is not None},
        }
        normalized = self._normalize_payload(merged, force_id=student_id)

        duplicate_reason = self.validar_duplicado(normalized, exclude_id=student_id)
        if duplicate_reason:
            return False, duplicate_reason

        self.repo.actualizar(student_id, normalized)
        return True, "Estudiante actualizado"

    def validar_duplicado(self, data: dict, exclude_id: str | None = None) -> str | None:
        rows = self.listar_estudiantes()

        for row in rows:
            if exclude_id and row.get("id_estudiante") == exclude_id:
                continue

            if data.get("identificacion") and row.get("identificacion"):
                if data["identificacion"].strip().lower() == row["identificacion"].strip().lower():
                    return "Duplicado por identificación"

            same_name = data.get("nombres", "").strip().lower() == row.get("nombres", "").strip().lower()
            same_lastname = data.get("apellidos", "").strip().lower() == row.get("apellidos", "").strip().lower()
            if same_name and same_lastname:
                return "Duplicado por nombres y apellidos"

        return None

    @staticmethod
    def _normalize_payload(data: dict, force_id: str | None = None) -> dict:
        student_id = force_id or data.get("id_estudiante") or str(uuid.uuid4())
        names = str(data.get("nombres", "")).strip()
        lastnames = str(data.get("apellidos", "")).strip()
        identification = str(data.get("identificacion", "")).strip() or None

        if not names or not lastnames:
            raise ValueError("Nombres y apellidos son obligatorios")

        # El código es opcional. Si no viene, se genera uno técnico interno.
        code = str(data.get("codigo", "")).strip() or f"AUTO-{student_id[:8]}"

        return {
            "id_estudiante": student_id,
            "codigo": code,
            "apellidos": lastnames,
            "nombres": names,
            "identificacion": identification,
        }
