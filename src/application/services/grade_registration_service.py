"""Servicio de registro de notas por asignación y trimestre."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from src.domain.calculations import (
    calcular_nota_trimestral,
    calcular_promedio_formativo,
    calcular_promedio_sumativo,
)
from src.infrastructure.persistence.repositories import GradeRecordsRepository


class GradeRegistrationService:
    """Casos de uso para carga, cálculo y guardado de notas trimestrales."""

    FORMATIVE_FIELDS = ("actividad_1", "mejora_1", "actividad_2", "mejora_2", "actividad_3", "mejora_3")
    SUMMATIVE_FIELDS = ("proyecto", "evaluacion", "refuerzo", "mejora_sumativa")

    def __init__(self, connection: sqlite3.Connection, min_grade: float = 0.0, max_grade: float = 10.0) -> None:
        self.connection = connection
        self.repo = GradeRecordsRepository(connection)
        self.min_grade = min_grade
        self.max_grade = max_grade

    def listar_contextos_disponibles(self) -> list[dict[str, Any]]:
        query = """
            SELECT
                a.id_asignacion,
                a.docente_id,
                a.asignatura_id,
                a.curso_id,
                a.paralelo_id,
                a.periodo_id,
                d.nombres AS docente_nombres,
                d.apellidos AS docente_apellidos,
                s.nombre AS asignatura_nombre,
                c.nombre AS curso_nombre,
                p.nombre AS paralelo_nombre
            FROM asignaciones_docente a
            LEFT JOIN docentes d ON d.id_docente = a.docente_id
            LEFT JOIN asignaturas s ON s.id_asignatura = a.asignatura_id
            LEFT JOIN cursos c ON c.id_curso = a.curso_id
            LEFT JOIN paralelos p ON p.id_paralelo = a.paralelo_id
            ORDER BY a.id_asignacion
        """
        rows = self.connection.execute(query).fetchall()
        contextos: list[dict[str, Any]] = []
        for row in rows:
            row_data = dict(row)
            docente = f"{row_data.get('docente_apellidos', '')} {row_data.get('docente_nombres', '')}".strip()
            asignatura = row_data.get("asignatura_nombre") or row_data.get("asignatura_id")
            curso = row_data.get("curso_nombre") or row_data.get("curso_id")
            paralelo = row_data.get("paralelo_nombre") or row_data.get("paralelo_id")
            periodo = row_data.get("periodo_id")
            row_data["display"] = f"{asignatura} | {curso}-{paralelo} | {docente} | {periodo}"
            contextos.append(row_data)
        return contextos

    def cargar_registro(self, asignacion_id: str, trimestre_num: int) -> list[dict[str, Any]]:
        if trimestre_num not in (1, 2, 3):
            raise ValueError("El trimestre debe ser 1, 2 o 3")

        asignacion = self.connection.execute(
            "SELECT * FROM asignaciones_docente WHERE id_asignacion = ?", (asignacion_id,)
        ).fetchone()
        if not asignacion:
            return []

        estudiantes = self.connection.execute(
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
            (asignacion["curso_id"], asignacion["paralelo_id"], asignacion["periodo_id"]),
        ).fetchall()

        registros_guardados = self.connection.execute(
            "SELECT * FROM grade_records WHERE asignacion_id = ? AND trimestre_num = ?",
            (asignacion_id, trimestre_num),
        ).fetchall()
        por_estudiante = {row["estudiante_id"]: dict(row) for row in registros_guardados}

        resultado: list[dict[str, Any]] = []
        for estudiante in estudiantes:
            estudiante_row = dict(estudiante)
            registro = por_estudiante.get(estudiante_row["id_estudiante"])
            fila = self._fila_base_estudiante(estudiante_row)
            if registro:
                fila.update(registro)
            fila = self.recalcular_fila(fila)
            resultado.append(fila)
        return resultado

    def guardar_registros(self, asignacion_id: str, trimestre_num: int, filas: list[dict[str, Any]]) -> tuple[bool, str]:
        if trimestre_num not in (1, 2, 3):
            return False, "Trimestre inválido"

        existentes = self.connection.execute(
            "SELECT * FROM grade_records WHERE asignacion_id = ? AND trimestre_num = ?",
            (asignacion_id, trimestre_num),
        ).fetchall()
        por_estudiante = {row["estudiante_id"]: dict(row) for row in existentes}

        procesados = 0
        for fila in filas:
            estudiante_id = str(fila.get("estudiante_id", "")).strip()
            if not estudiante_id:
                continue

            validada = self.validar_y_normalizar_fila(fila)
            calculada = self.recalcular_fila(validada)
            payload = {
                "estudiante_id": estudiante_id,
                "asignacion_id": asignacion_id,
                "trimestre_num": trimestre_num,
                **{campo: calculada.get(campo) for campo in self.FORMATIVE_FIELDS + self.SUMMATIVE_FIELDS},
                "promedio_formativo": calculada.get("promedio_formativo"),
                "promedio_sumativo": calculada.get("promedio_sumativo"),
                "nota_trimestral": calculada.get("nota_trimestral"),
            }

            existente = por_estudiante.get(estudiante_id)
            if existente:
                self.repo.actualizar(existente["id_registro"], payload)
            else:
                self.repo.crear({"id_registro": str(uuid.uuid4()), **payload})
            procesados += 1

        return True, f"Registros guardados: {procesados}"

    def validar_y_normalizar_fila(self, fila: dict[str, Any]) -> dict[str, Any]:
        salida = dict(fila)
        for campo in self.FORMATIVE_FIELDS + self.SUMMATIVE_FIELDS:
            salida[campo] = self._normalizar_nota(fila.get(campo), campo)
        return salida

    def recalcular_fila(self, fila: dict[str, Any]) -> dict[str, Any]:
        data = self.validar_y_normalizar_fila(fila)

        promedio_formativo = calcular_promedio_formativo(
            [
                (data["actividad_1"] or 0.0, data["mejora_1"]),
                (data["actividad_2"] or 0.0, data["mejora_2"]),
                (data["actividad_3"] or 0.0, data["mejora_3"]),
            ]
        )
        promedio_sumativo = calcular_promedio_sumativo(
            [
                (data["proyecto"] or 0.0, data["mejora_sumativa"]),
                (data["evaluacion"] or 0.0, None),
                (data["refuerzo"] or 0.0, None),
            ]
        )
        nota_trimestral = calcular_nota_trimestral(promedio_formativo, promedio_sumativo)

        data["promedio_formativo"] = promedio_formativo
        data["promedio_sumativo"] = promedio_sumativo
        data["nota_trimestral"] = nota_trimestral
        return data

    def _normalizar_nota(self, valor: Any, campo: str) -> float | None:
        if valor is None:
            return None

        texto = str(valor).strip()
        if texto == "":
            return None

        try:
            nota = float(texto)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Valor no numérico en {campo}") from exc

        if nota < self.min_grade or nota > self.max_grade:
            raise ValueError(f"Valor fuera de rango en {campo}. Rango permitido {self.min_grade} a {self.max_grade}")

        return nota

    def _fila_base_estudiante(self, estudiante: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_registro": None,
            "estudiante_id": estudiante["id_estudiante"],
            "estudiante": f"{estudiante.get('apellidos', '')} {estudiante.get('nombres', '')}".strip(),
            "codigo": estudiante.get("codigo"),
            "numero_lista": estudiante.get("numero_lista"),
            "asignacion_id": None,
            "trimestre_num": None,
            "actividad_1": None,
            "mejora_1": None,
            "actividad_2": None,
            "mejora_2": None,
            "actividad_3": None,
            "mejora_3": None,
            "proyecto": None,
            "evaluacion": None,
            "refuerzo": None,
            "mejora_sumativa": None,
            "promedio_formativo": 0.0,
            "promedio_sumativo": 0.0,
            "nota_trimestral": 0.0,
        }
