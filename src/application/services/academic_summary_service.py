"""Servicio de resumen académico anual y supletorio."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from src.domain.calculations import (
    calcular_cualitativo,
    calcular_observacion_final,
    calcular_promedio_anual,
    calcular_resultado_con_supletorio,
)
from src.infrastructure.persistence.repositories import FinalSupplementaryRepository


class AcademicSummaryService:
    """Consolida trimestres y calcula resultado final por estudiante."""

    def __init__(self, connection: sqlite3.Connection, min_grade: float = 0.0, max_grade: float = 10.0) -> None:
        self.connection = connection
        self.supp_repo = FinalSupplementaryRepository(connection)
        self.min_grade = min_grade
        self.max_grade = max_grade

    def listar_contextos_disponibles(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
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
        ).fetchall()

        contextos: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            docente = f"{item.get('docente_apellidos', '')} {item.get('docente_nombres', '')}".strip()
            asignatura = item.get("asignatura_nombre") or item.get("asignatura_id")
            curso = item.get("curso_nombre") or item.get("curso_id")
            paralelo = item.get("paralelo_nombre") or item.get("paralelo_id")
            periodo = item.get("periodo_id")
            item["display"] = f"{asignatura} | {curso}-{paralelo} | {docente} | {periodo}"
            contextos.append(item)
        return contextos

    def obtener_resumen_por_asignacion(self, asignacion_id: str) -> list[dict[str, Any]]:
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

        if not estudiantes:
            return []

        trimestres = self.connection.execute(
            "SELECT estudiante_id, trimestre_num, nota_trimestral FROM grade_records WHERE asignacion_id = ?",
            (asignacion_id,),
        ).fetchall()
        tri_map: dict[tuple[str, int], float | None] = {}
        for row in trimestres:
            tri_map[(row["estudiante_id"], row["trimestre_num"])] = row["nota_trimestral"]

        supletorios = self.connection.execute(
            "SELECT estudiante_id, nota_supletorio FROM final_supplementary WHERE asignacion_id = ?",
            (asignacion_id,),
        ).fetchall()
        supp_map = {row["estudiante_id"]: row["nota_supletorio"] for row in supletorios}

        resumenes: list[dict[str, Any]] = []
        for student in estudiantes:
            student_row = dict(student)
            student_id = student_row["id_estudiante"]
            t1 = tri_map.get((student_id, 1))
            t2 = tri_map.get((student_id, 2))
            t3 = tri_map.get((student_id, 3))
            promedio_final = self._calcular_promedio_anual_seguro(t1, t2, t3)
            supletorio = supp_map.get(student_id)
            nota_definitiva = calcular_resultado_con_supletorio(promedio_final, supletorio)

            resumenes.append(
                {
                    "estudiante_id": student_id,
                    "estudiante": f"{student_row.get('apellidos', '')} {student_row.get('nombres', '')}".strip(),
                    "codigo": student_row.get("codigo"),
                    "numero_lista": student_row.get("numero_lista"),
                    "trimestre_1": t1,
                    "trimestre_2": t2,
                    "trimestre_3": t3,
                    "promedio_final": promedio_final,
                    "cualitativo": calcular_cualitativo(promedio_final),
                    "observacion": calcular_observacion_final(promedio_final),
                    "supletorio": supletorio,
                    "nota_definitiva": nota_definitiva,
                }
            )

        return resumenes

    def recalcular_resumenes(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        recalculados: list[dict[str, Any]] = []
        for row in rows:
            t1 = self._normalizar_nota_opcional(row.get("trimestre_1"), "trimestre_1")
            t2 = self._normalizar_nota_opcional(row.get("trimestre_2"), "trimestre_2")
            t3 = self._normalizar_nota_opcional(row.get("trimestre_3"), "trimestre_3")
            supletorio = self._normalizar_nota_opcional(row.get("supletorio"), "supletorio")

            promedio_final = self._calcular_promedio_anual_seguro(t1, t2, t3)
            recalculados.append(
                {
                    **row,
                    "trimestre_1": t1,
                    "trimestre_2": t2,
                    "trimestre_3": t3,
                    "promedio_final": promedio_final,
                    "cualitativo": calcular_cualitativo(promedio_final),
                    "observacion": calcular_observacion_final(promedio_final),
                    "supletorio": supletorio,
                    "nota_definitiva": calcular_resultado_con_supletorio(promedio_final, supletorio),
                }
            )
        return recalculados

    def guardar_supletorios(self, asignacion_id: str, rows: list[dict[str, Any]]) -> tuple[bool, str]:
        existentes = self.connection.execute(
            "SELECT * FROM final_supplementary WHERE asignacion_id = ?", (asignacion_id,)
        ).fetchall()
        by_student = {row["estudiante_id"]: dict(row) for row in existentes}

        procesados = 0
        with self.connection:
            for row in rows:
                estudiante_id = str(row.get("estudiante_id", "")).strip()
                if not estudiante_id:
                    continue

                supletorio = self._normalizar_nota_opcional(row.get("supletorio"), "supletorio")
                actual = by_student.get(estudiante_id)

                if supletorio is None:
                    if actual:
                        self.connection.execute(
                            "DELETE FROM final_supplementary WHERE id_supletorio = ?",
                            (actual["id_supletorio"],),
                        )
                    procesados += 1
                    continue

                payload = {
                    "estudiante_id": estudiante_id,
                    "asignacion_id": asignacion_id,
                    "nota_supletorio": supletorio,
                }
                if actual:
                    self.supp_repo.actualizar(actual["id_supletorio"], payload)
                else:
                    self.supp_repo.crear({"id_supletorio": str(uuid.uuid4()), **payload})
                procesados += 1

        return True, f"Supletorios procesados: {procesados}"

    def _normalizar_nota_opcional(self, value: Any, field: str) -> float | None:
        if value is None:
            return None
        text = str(value).strip()
        if text == "":
            return None

        try:
            number = float(text)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Valor no numérico en {field}") from exc

        if number < self.min_grade or number > self.max_grade:
            raise ValueError(f"Valor fuera de rango en {field}. Rango permitido {self.min_grade} a {self.max_grade}")
        return number

    @staticmethod
    def _calcular_promedio_anual_seguro(t1: float | None, t2: float | None, t3: float | None) -> float:
        return calcular_promedio_anual(t1 or 0.0, t2 or 0.0, t3 or 0.0)
