"""Servicio para evaluación cualitativa de acompañamiento integral en el aula."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from src.domain.calculations import calcular_valoracion_acompanamiento
from src.infrastructure.persistence.repositories import (
    ClassroomAccompanimentRepository,
    ClassroomAccompanimentSkillConfigRepository,
)

RESPONSE_OPTIONS = ("Siempre", "Frecuentemente", "Ocasionalmente", "Nunca")
MAX_ACTIVE_SKILLS = 9

SKILL_CATEGORIES: tuple[dict[str, Any], ...] = (
    {
        "category": "HABILIDADES COGNITIVAS",
        "skills": (
            ("autoconocimiento", "Autoconocimiento"),
            ("pensamiento_critico", "Pensamiento crítico"),
            ("manejo_problemas", "Manejo de problemas"),
            ("toma_decisiones", "Toma de decisiones"),
            ("pensamiento_creativo", "Pensamiento creativo"),
        ),
    },
    {
        "category": "HABILIDADES SOCIALES",
        "skills": (
            ("trabajo_equipo", "Trabajo en equipo"),
            ("conciencia_social", "Conciencia social"),
            ("pensamiento_etico", "Pensamiento ético"),
            ("empatia", "Empatía"),
            ("relaciones_interpersonales", "Relaciones interpersonales"),
            ("manejo_conflictos", "Manejo de conflictos"),
            ("comunicacion_efectiva_asertiva", "Comunicación efectiva/asertiva"),
            ("conciencia_global", "Conciencia global"),
        ),
    },
    {
        "category": "HABILIDADES EMOCIONALES",
        "skills": (
            ("manejo_emociones_sentimientos", "Manejo de emociones y sentimientos"),
            ("manejo_estres_tension", "Manejo de estrés y tensión"),
        ),
    },
)


class ClassroomAccompanimentService:
    """Casos de uso de acompañamiento por asignación y trimestre."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.repo = ClassroomAccompanimentRepository(connection)
        self.skill_config_repo = ClassroomAccompanimentSkillConfigRepository(connection)

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
                c.nivel AS curso_nivel,
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

    def obtener_contexto(self, asignacion_id: str) -> dict[str, Any] | None:
        for contexto in self.listar_contextos_disponibles():
            if contexto.get("id_asignacion") == asignacion_id:
                return contexto
        return None

    def obtener_datos_institucion(self) -> dict[str, Any]:
        row = self.connection.execute(
            """
            SELECT nombre, rector, logo_path, logo_ministerio_path
            FROM institucion
            ORDER BY id_institucion
            LIMIT 1
            """
        ).fetchone()
        return dict(row) if row else {}

    def listar_firmantes_disponibles(self) -> list[str]:
        rows = self.connection.execute(
            """
            SELECT titulo, nombres, apellidos
            FROM docentes
            WHERE activo = 1
            ORDER BY apellidos, nombres
            """
        ).fetchall()
        firmantes: list[str] = []
        for row in rows:
            nombres = str(row["nombres"] or "").strip().split()
            apellidos = str(row["apellidos"] or "").strip().split()
            primer_nombre = nombres[0] if nombres else ""
            primer_apellido = apellidos[0] if apellidos else ""
            titulo = str(row["titulo"] or "").strip()
            firma = " ".join(part for part in [titulo, primer_nombre, primer_apellido] if part).strip()
            if firma:
                firmantes.append(firma)

        institucion = self.obtener_datos_institucion()
        rector = str(institucion.get("rector") or "").strip()
        if rector and rector not in firmantes:
            firmantes.insert(0, rector)
        return firmantes

    def listar_habilidades_base(self) -> list[dict[str, str]]:
        habilidades: list[dict[str, str]] = []
        for group in SKILL_CATEGORIES:
            for key, label in group["skills"]:
                habilidades.append({"key": key, "label": label, "category": group["category"]})
        return habilidades

    def cargar_evaluacion(self, asignacion_id: str, trimestre_num: int) -> dict[str, Any]:
        if trimestre_num not in (1, 2, 3):
            raise ValueError("El trimestre debe ser 1, 2 o 3")

        asignacion = self.connection.execute(
            "SELECT * FROM asignaciones_docente WHERE id_asignacion = ?", (asignacion_id,)
        ).fetchone()
        if not asignacion:
            return {
                "students": [],
                "skill_categories": self._skill_categories_with_visibility({}, [], []),
                "active_skills": [],
                "responses": {},
                "results": {},
                "validation_message": "",
            }

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

        skills = self.listar_habilidades_base()
        configured_visibility = self._load_visibility(asignacion_id, trimestre_num)
        if configured_visibility:
            active_skills = [s["key"] for s in skills if configured_visibility.get(s["key"], False)]
            active_skills, exceeded = self._limit_active_skills(active_skills)
        else:
            active_skills = [s["key"] for s in skills[:MAX_ACTIVE_SKILLS]]
            exceeded = False

        saved_rows = self.connection.execute(
            """
            SELECT estudiante_id, habilidad_clave, valor
            FROM acompanamiento_evaluaciones
            WHERE asignacion_id = ? AND trimestre_num = ?
            """,
            (asignacion_id, trimestre_num),
        ).fetchall()

        responses: dict[str, dict[str, str]] = {}
        for row in saved_rows:
            sid = row["estudiante_id"]
            responses.setdefault(sid, {})[row["habilidad_clave"]] = row["valor"]

        students_out: list[dict[str, Any]] = []
        for estudiante in estudiantes:
            sid = estudiante["id_estudiante"]
            students_out.append(
                {
                    "student_id": sid,
                    "code": estudiante["codigo"],
                    "name": f"{estudiante['apellidos']} {estudiante['nombres']}".strip(),
                    "numero_lista": estudiante["numero_lista"],
                }
            )

        results = self._build_results(students_out, active_skills, responses)
        return {
            "students": students_out,
            "skill_categories": self._skill_categories_with_visibility(configured_visibility, skills, active_skills),
            "active_skills": active_skills,
            "responses": responses,
            "results": results,
            "validation_message": (
                f"Solo se pueden seleccionar hasta {MAX_ACTIVE_SKILLS} habilidades activas para esta evaluación."
                if exceeded
                else ""
            ),
        }

    def guardar_evaluacion(
        self,
        asignacion_id: str,
        trimestre_num: int,
        active_skills: list[str],
        responses: dict[str, dict[str, str]],
    ) -> tuple[bool, str]:
        if trimestre_num not in (1, 2, 3):
            return False, "Trimestre inválido"
        if len(active_skills) > MAX_ACTIVE_SKILLS:
            return False, f"Solo se pueden seleccionar hasta {MAX_ACTIVE_SKILLS} habilidades activas para esta evaluación."

        all_skills = [skill["key"] for skill in self.listar_habilidades_base()]
        visible_map = {key: key in set(active_skills) for key in all_skills}

        with self.connection:
            self.connection.execute(
                "DELETE FROM acompanamiento_habilidades_config WHERE asignacion_id = ? AND trimestre_num = ?",
                (asignacion_id, trimestre_num),
            )
            for key in all_skills:
                self.skill_config_repo.crear(
                    {
                        "id_config": str(uuid.uuid4()),
                        "asignacion_id": asignacion_id,
                        "trimestre_num": trimestre_num,
                        "habilidad_clave": key,
                        "visible": 1 if visible_map[key] else 0,
                    }
                )

            self.connection.execute(
                "DELETE FROM acompanamiento_evaluaciones WHERE asignacion_id = ? AND trimestre_num = ?",
                (asignacion_id, trimestre_num),
            )

            guardados = 0
            for student_id, skill_values in responses.items():
                for skill_key in active_skills:
                    value = (skill_values or {}).get(skill_key, "").strip()
                    if value not in RESPONSE_OPTIONS:
                        continue
                    self.repo.crear(
                        {
                            "id_evaluacion": str(uuid.uuid4()),
                            "asignacion_id": asignacion_id,
                            "trimestre_num": trimestre_num,
                            "estudiante_id": student_id,
                            "habilidad_clave": skill_key,
                            "valor": value,
                        }
                    )
                    guardados += 1

        return True, f"Evaluaciones guardadas: {guardados}"

    def calcular_resultado_estudiante(self, skill_values: dict[str, str], active_skills: list[str]) -> dict[str, Any]:
        if len(active_skills) > MAX_ACTIVE_SKILLS:
            return {
                "total_siempre": 0,
                "total_frecuentemente": 0,
                "total_ocasionalmente": 0,
                "total_nunca": 0,
                "puntaje_total_ponderado": None,
                "valoracion_final": "",
                "validation_message": f"Solo se pueden seleccionar hasta {MAX_ACTIVE_SKILLS} habilidades activas para esta evaluación.",
            }
        counts = {option: 0 for option in RESPONSE_OPTIONS}
        for skill_key in active_skills:
            value = (skill_values or {}).get(skill_key)
            if value in counts:
                counts[value] += 1

        puntaje_total = (
            (counts["Siempre"] * 4)
            + (counts["Frecuentemente"] * 3)
            + (counts["Ocasionalmente"] * 2)
            + (counts["Nunca"] * 1)
        )
        final = calcular_valoracion_acompanamiento(
            total_siempre=counts["Siempre"],
            total_frecuentemente=counts["Frecuentemente"],
            total_ocasionalmente=counts["Ocasionalmente"],
            total_nunca=counts["Nunca"],
        )
        return {
            "total_siempre": counts["Siempre"],
            "total_frecuentemente": counts["Frecuentemente"],
            "total_ocasionalmente": counts["Ocasionalmente"],
            "total_nunca": counts["Nunca"],
            "puntaje_total_ponderado": puntaje_total,
            "valoracion_final": final,
            "validation_message": "",
        }

    def _build_results(
        self,
        students: list[dict[str, Any]],
        active_skills: list[str],
        responses: dict[str, dict[str, str]],
    ) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for student in students:
            sid = student["student_id"]
            out[sid] = self.calcular_resultado_estudiante(responses.get(sid, {}), active_skills)
        return out

    def _load_visibility(self, asignacion_id: str, trimestre_num: int) -> dict[str, bool]:
        rows = self.connection.execute(
            """
            SELECT habilidad_clave, visible
            FROM acompanamiento_habilidades_config
            WHERE asignacion_id = ? AND trimestre_num = ?
            """,
            (asignacion_id, trimestre_num),
        ).fetchall()
        return {row["habilidad_clave"]: bool(row["visible"]) for row in rows}

    @staticmethod
    def _skill_categories_with_visibility(
        visibility: dict[str, bool],
        skills: list[dict[str, str]],
        active_skills: list[str],
    ) -> list[dict[str, Any]]:
        active_set = set(active_skills)
        by_category: dict[str, list[dict[str, Any]]] = {}
        for skill in skills:
            by_category.setdefault(skill["category"], []).append(
                {
                    "key": skill["key"],
                    "label": skill["label"],
                    "visible": skill["key"] in active_set,
                }
            )

        categories = []
        for category_name, category_skills in by_category.items():
            categories.append({"category": category_name, "skills": category_skills})
        return categories

    @staticmethod
    def _limit_active_skills(active_skills: list[str]) -> tuple[list[str], bool]:
        normalized = list(dict.fromkeys(active_skills))
        if len(normalized) <= MAX_ACTIVE_SKILLS:
            return normalized, False
        return normalized[:MAX_ACTIVE_SKILLS], True
