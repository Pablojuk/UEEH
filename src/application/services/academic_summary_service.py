"""Servicio de resumen académico anual y supletorio."""

from __future__ import annotations

import sqlite3
import uuid
import unicodedata
from typing import Any

from src.application.services.enrollment_service import student_alphabetical_key
from src.domain.calculations import (
    calcular_cualitativo,
    calcular_cualitativo_trimestral,
    calcular_escala_cualitativa,
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
                c.nivel AS curso_nivel,
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

    def listar_firmantes_disponibles(self) -> list[dict[str, str]]:
        rows = self.connection.execute(
            """
            SELECT id_docente, titulo, nombres, apellidos
            FROM docentes
            WHERE activo = 1
            ORDER BY apellidos, nombres
            """
        ).fetchall()

        firmantes: list[dict[str, str]] = []
        for row in rows:
            nombres = str(row["nombres"] or "").strip().split()
            apellidos = str(row["apellidos"] or "").strip().split()
            primer_nombre = nombres[0] if nombres else ""
            primer_apellido = apellidos[0] if apellidos else ""
            titulo = str(row["titulo"] or "").strip()
            firma = " ".join(part for part in [titulo, primer_nombre, primer_apellido] if part).strip()
            firmantes.append(
                {
                    "id_docente": row["id_docente"],
                    "firma": firma,
                }
            )
        return firmantes

    def obtener_resumen_por_asignacion(self, asignacion_id: str) -> list[dict[str, Any]]:
        return self.obtener_reporte_anual(asignacion_id)

    def obtener_reporte_trimestral(self, asignacion_id: str, trimestre_num: int) -> list[dict[str, Any]]:
        if trimestre_num not in (1, 2, 3):
            raise ValueError("El trimestre debe ser 1, 2 o 3")

        asignacion = self.connection.execute(
            "SELECT * FROM asignaciones_docente WHERE id_asignacion = ?", (asignacion_id,)
        ).fetchone()
        if not asignacion:
            return []

        rows = self.connection.execute(
            """
            SELECT
                e.id_estudiante,
                e.codigo,
                e.apellidos,
                e.nombres,
                e.apellidos || ' ' || e.nombres AS estudiante,
                m.numero_lista,
                g.promedio_formativo AS aportes_calificacion,
                g.promedio_sumativo AS sumativas_calificacion,
                g.nota_trimestral AS promedio_original,
                g.nota_trimestral AS nota_trimestral
            FROM matriculas m
            JOIN estudiantes e ON e.id_estudiante = m.estudiante_id
            LEFT JOIN grade_records g
                ON g.estudiante_id = e.id_estudiante
                AND g.asignacion_id = ?
                AND g.trimestre_num = ?
            WHERE m.curso_id = ? AND m.paralelo_id = ? AND m.periodo_id = ?
            ORDER BY
                CASE WHEN m.numero_lista IS NULL THEN 1 ELSE 0 END,
                m.numero_lista,
                e.apellidos,
                e.nombres
            """,
            (asignacion_id, trimestre_num, asignacion["curso_id"], asignacion["paralelo_id"], asignacion["periodo_id"]),
        ).fetchall()
        rows = sorted((dict(row) for row in rows), key=student_alphabetical_key)

        resultado: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item.pop("codigo", None)
            item.pop("apellidos", None)
            item.pop("nombres", None)
            aportes = item.get("aportes_calificacion")
            sumativas = item.get("sumativas_calificacion")
            aportes_70 = round((aportes or 0) * 0.70, 2) if aportes is not None else None
            sumativas_30 = round((sumativas or 0) * 0.30, 2) if sumativas is not None else None
            promedio_original = item.get("promedio_original")
            promedio = (
                promedio_original
                if promedio_original is not None
                else round((aportes_70 or 0) + (sumativas_30 or 0), 2)
                if aportes_70 is not None and sumativas_30 is not None
                else None
            )

            item["aportes_70"] = aportes_70
            item["sumativas_30"] = sumativas_30
            item["promedio_final"] = promedio
            item["cualitativa"] = calcular_cualitativo_trimestral(promedio)
            item["promedio_trimestral"] = promedio
            item["cualitativo"] = item["cualitativa"]
            item["equivalencia"] = calcular_escala_cualitativa(item.get("promedio_final"))
            item["observacion"] = (
                calcular_observacion_final(item.get("promedio_final")) if item.get("promedio_final") is not None else ""
            )
            resultado.append(item)
        return resultado

    def obtener_reporte_anual(self, asignacion_id: str) -> list[dict[str, Any]]:
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
        estudiantes = sorted((dict(row) for row in estudiantes), key=student_alphabetical_key)

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

        asignatura = self.connection.execute(
            "SELECT nombre FROM asignaturas WHERE id_asignatura = ?",
            (asignacion["asignatura_id"],),
        ).fetchone()
        curso = self.connection.execute("SELECT nombre FROM cursos WHERE id_curso = ?", (asignacion["curso_id"],)).fetchone()
        simplified_egb = self._is_simplified_egb_course(curso["nombre"] if curso else "", asignatura["nombre"] if asignatura else "")

        resumenes: list[dict[str, Any]] = []
        for student in estudiantes:
            student_row = dict(student)
            student_id = student_row["id_estudiante"]
            t1 = tri_map.get((student_id, 1))
            t2 = tri_map.get((student_id, 2))
            t3 = tri_map.get((student_id, 3))
            promedio = self._calcular_promedio_anual_seguro(t1, t2, t3)
            supletorio = supp_map.get(student_id)
            if promedio is None:
                promedio_final = supletorio
            else:
                promedio_final = calcular_resultado_con_supletorio(promedio, supletorio)

            base = {
                    "estudiante_id": student_id,
                    "estudiante": f"{student_row.get('apellidos', '')} {student_row.get('nombres', '')}".strip(),
                    "codigo": student_row.get("codigo"),
                    "numero_lista": student_row.get("numero_lista"),
                    "trimestre_1": t1,
                    "trimestre_2": t2,
                    "trimestre_3": t3,
                    "equivalencia_t1": calcular_escala_cualitativa(t1),
                    "equivalencia_t2": calcular_escala_cualitativa(t2),
                    "equivalencia_t3": calcular_escala_cualitativa(t3),
                    "promedio": promedio,
                    "cualitativa_anual": calcular_escala_cualitativa(promedio),
                    "supletorio": supletorio,
                    "promedio_final": promedio_final,
                    "cualitativo": calcular_cualitativo(promedio) if promedio is not None else "",
                    "cualitativo_final": calcular_escala_cualitativa(promedio_final),
                    "observacion": calcular_observacion_final(promedio_final) if promedio_final is not None else "",
                    "nota_definitiva": promedio_final,
                }
            if simplified_egb:
                c1 = calcular_cualitativo_trimestral(t1)
                c2 = calcular_cualitativo_trimestral(t2)
                c3 = calcular_cualitativo_trimestral(t3)
                cual_anual = calcular_cualitativo_trimestral(promedio) if promedio is not None else ""
                base.update(
                    {
                        "equivalencia_t1": c1,
                        "equivalencia_t2": c2,
                        "equivalencia_t3": c3,
                        "cualitativo_t1": c1,
                        "cualitativo_t2": c2,
                        "cualitativo_t3": c3,
                        "cualitativa_anual": cual_anual,
                        "cualitativo_final": cual_anual,
                        "equivalencia": self._calcular_equivalencia_egb_basica(cual_anual),
                    }
                )
            resumenes.append(base)

        return resumenes

    @staticmethod
    def _normalize_text(value: Any) -> str:
        normalized = unicodedata.normalize("NFD", str(value or "").strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())

    def _is_simplified_egb_course(self, curso_nombre: str, asignatura_nombre: str) -> bool:
        subject = self._normalize_text(asignatura_nombre)
        if subject in {
            "orientacion vocacional y profesional",
            "comportamiento",
            "acompanamiento integral en el aula",
            "animacion a la lectura",
        }:
            return False
        course = self._normalize_text(curso_nombre)
        return any(
            alias in course
            for alias in {
                "2do de egb", "2do egb", "segundo de egb", "segundo egb",
                "3ro de egb", "3ro egb", "tercero de egb", "tercero egb",
                "4to de egb", "4to egb", "cuarto de egb", "cuarto egb",
            }
        )

    @staticmethod
    def _calcular_equivalencia_egb_basica(cualitativo: str) -> str:
        key = str(cualitativo or "").strip().upper()
        if key in {"A+", "A-", "B+"}:
            return "Destreza o aprendizaje alcanzado"
        if key in {"B-", "C+", "C-"}:
            return "Destreza o aprendizaje en proceso de desarrollo"
        if key in {"D+", "D-", "E+", "E-"}:
            return "Destreza o aprendizaje iniciado"
        return ""

    def recalcular_resumenes(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        recalculados: list[dict[str, Any]] = []
        for row in rows:
            t1 = self._normalizar_nota_opcional(row.get("trimestre_1"), "trimestre_1")
            t2 = self._normalizar_nota_opcional(row.get("trimestre_2"), "trimestre_2")
            t3 = self._normalizar_nota_opcional(row.get("trimestre_3"), "trimestre_3")
            supletorio = self._normalizar_nota_opcional(row.get("supletorio"), "supletorio")

            promedio = self._calcular_promedio_anual_seguro(t1, t2, t3)
            if promedio is None:
                promedio_final = supletorio
            else:
                promedio_final = calcular_resultado_con_supletorio(promedio, supletorio)
            recalculados.append(
                {
                    **row,
                    "trimestre_1": t1,
                    "trimestre_2": t2,
                    "trimestre_3": t3,
                    "equivalencia_t1": calcular_escala_cualitativa(t1),
                    "equivalencia_t2": calcular_escala_cualitativa(t2),
                    "equivalencia_t3": calcular_escala_cualitativa(t3),
                    "promedio": promedio,
                    "cualitativa_anual": calcular_escala_cualitativa(promedio),
                    "promedio_final": promedio_final,
                    "cualitativo": calcular_cualitativo(promedio) if promedio is not None else "",
                    "cualitativo_final": calcular_escala_cualitativa(promedio_final),
                    "observacion": calcular_observacion_final(promedio_final) if promedio_final is not None else "",
                    "supletorio": supletorio,
                    "nota_definitiva": promedio_final,
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
    def _calcular_promedio_anual_seguro(t1: float | None, t2: float | None, t3: float | None) -> float | None:
        if t1 is None and t2 is None and t3 is None:
            return None
        return calcular_promedio_anual(t1 or 0.0, t2 or 0.0, t3 or 0.0)
