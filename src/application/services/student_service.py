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

    def eliminar_estudiantes(self, student_ids: list[str]) -> tuple[int, list[str]]:
        eliminados = 0
        bloqueos: list[str] = []
        for student_id in student_ids:
            deps = self.connection.execute(
                """
                SELECT
                    (SELECT COUNT(1) FROM matriculas WHERE estudiante_id = ?) AS matr,
                    (SELECT COUNT(1) FROM grade_records WHERE estudiante_id = ?) AS notes,
                    (SELECT COUNT(1) FROM final_supplementary WHERE estudiante_id = ?) AS supp
                """,
                (student_id, student_id, student_id),
            ).fetchone()
            if deps and (deps["matr"] > 0 or deps["notes"] > 0 or deps["supp"] > 0):
                bloqueos.append(f"{student_id}: tiene matrículas o notas relacionadas")
                continue
            self.repo.eliminar(student_id)
            eliminados += 1
        return eliminados, bloqueos

    def validar_duplicado(self, data: dict, exclude_id: str | None = None) -> str | None:
        rows = self.listar_estudiantes()
        identificacion_data = self._normalizar_identificacion(data.get("identificacion"))
        codigo_data = self._normalizar_codigo(data.get("codigo"))

        for row in rows:
            if exclude_id and row.get("id_estudiante") == exclude_id:
                continue

            identificacion_row = self._normalizar_identificacion(row.get("identificacion"))
            if identificacion_data and identificacion_row and identificacion_data == identificacion_row:
                return "Duplicado por identificación"

            codigo_row = self._normalizar_codigo(row.get("codigo"))
            if codigo_data and codigo_row and codigo_data == codigo_row:
                return "Duplicado por código"

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
        raw_code = data.get("codigo")
        code = str(raw_code).strip() if raw_code is not None else ""
        if not code or code.lower() in {"none", "nan", "null"}:
            code = f"AUTO-{student_id[:8]}"

        return {
            "id_estudiante": student_id,
            "codigo": StudentService._normalizar_codigo(code) or f"AUTO-{student_id[:8]}",
            "apellidos": lastnames,
            "nombres": names,
            "identificacion": StudentService._normalizar_identificacion(identification),
        }

    @staticmethod
    def _normalizar_identificacion(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            return None
        if text.endswith(".0"):
            base = text[:-2]
            if base.isdigit():
                text = base
        return text

    @staticmethod
    def _normalizar_codigo(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() in {"none", "nan", "null"}:
            return None
        return text
