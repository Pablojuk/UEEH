"""Servicio de registro de notas por asignación y trimestre."""

from __future__ import annotations

import json
import sqlite3
import uuid
import unicodedata
from typing import Any

from src.domain.calculations import (
    calcular_cualitativo_trimestral,
    calcular_escala_cualitativa,
    calcular_promedio_actividad,
    calcular_promedio_con_mejora,
    calcular_promedio_evaluacion_formativa,
    calcular_promedio_evaluacion_sumativa,
    redondear_2_decimales,
)
from src.infrastructure.persistence.repositories import (
    AnimationReadingEvaluationRepository,
    GradeActivityConfigRepository,
    GradeRecordsRepository,
    VocationalOrientationEvaluationRepository,
)


class GradeRegistrationService:
    """Casos de uso para carga, cálculo y guardado de notas trimestrales."""

    SUMMATIVE_FIELDS = ("proyecto", "evaluacion", "refuerzo", "mejora_sumativa")
    ORIENTATION_SUBJECT_NAME = "orientacion vocacional y profesional"
    EXCLUDED_SPECIAL_SUBJECTS = {
        "orientacion vocacional y profesional",
        "comportamiento",
        "acompanamiento integral en el aula",
        "animacion a la lectura",
    }
    ORIENTATION_ALLOWED_COURSE_KEYS = {"8", "9", "10"}

    def __init__(self, connection: sqlite3.Connection, min_grade: float = 0.0, max_grade: float = 10.0) -> None:
        self.connection = connection
        self.repo = GradeRecordsRepository(connection)
        self.animation_repo = AnimationReadingEvaluationRepository(connection)
        self.orientation_repo = VocationalOrientationEvaluationRepository(connection)
        self.activity_config_repo = GradeActivityConfigRepository(connection)
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

    def obtener_numero_actividades(self, asignacion_id: str, trimestre_num: int) -> int:
        row = self.connection.execute(
            "SELECT numero_actividades FROM grade_activity_config WHERE asignacion_id = ? AND trimestre_num = ?",
            (asignacion_id, trimestre_num),
        ).fetchone()
        if row:
            return int(row["numero_actividades"])
        return 3

    def configurar_numero_actividades(self, asignacion_id: str, trimestre_num: int, numero_actividades: int) -> tuple[bool, str]:
        if numero_actividades < 1 or numero_actividades > 20:
            return False, "El número de actividades debe estar entre 1 y 20"
        row = self.connection.execute(
            "SELECT * FROM grade_activity_config WHERE asignacion_id = ? AND trimestre_num = ?",
            (asignacion_id, trimestre_num),
        ).fetchone()
        payload = {
            "asignacion_id": asignacion_id,
            "trimestre_num": trimestre_num,
            "numero_actividades": numero_actividades,
            "metadata_json": row["metadata_json"] if row and "metadata_json" in row.keys() else None,
        }
        if row:
            self.activity_config_repo.actualizar(row["id_config"], payload)
        else:
            self.activity_config_repo.crear({"id_config": str(uuid.uuid4()), **payload})
        return True, "Configuración de actividades actualizada"

    def obtener_configuracion_actividades(self, asignacion_id: str, trimestre_num: int) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT numero_actividades, metadata_json FROM grade_activity_config WHERE asignacion_id = ? AND trimestre_num = ?",
            (asignacion_id, trimestre_num),
        ).fetchone()
        numero_actividades = int(row["numero_actividades"]) if row else 3
        metadata = self._parse_metadata_json(row["metadata_json"] if row else None, numero_actividades)
        return {
            "numero_actividades": numero_actividades,
            "metadata": metadata,
        }

    def guardar_configuracion_actividades(
        self,
        asignacion_id: str,
        trimestre_num: int,
        metadata: list[dict[str, str]],
    ) -> tuple[bool, str]:
        row = self.connection.execute(
            "SELECT * FROM grade_activity_config WHERE asignacion_id = ? AND trimestre_num = ?",
            (asignacion_id, trimestre_num),
        ).fetchone()
        numero_actividades = int(row["numero_actividades"]) if row else max(len(metadata), 1)
        metadata_normalizada = self._normalize_activity_metadata(metadata, numero_actividades)
        payload = {
            "asignacion_id": asignacion_id,
            "trimestre_num": trimestre_num,
            "numero_actividades": numero_actividades,
            "metadata_json": json.dumps(metadata_normalizada, ensure_ascii=False),
        }
        if row:
            self.activity_config_repo.actualizar(row["id_config"], payload)
        else:
            self.activity_config_repo.crear({"id_config": str(uuid.uuid4()), **payload})
        return True, "Configuración de actividades guardada"

    def cargar_registro(self, asignacion_id: str, trimestre_num: int) -> list[dict[str, Any]]:
        if trimestre_num not in (1, 2, 3):
            raise ValueError("El trimestre debe ser 1, 2 o 3")

        asignacion = self.connection.execute(
            "SELECT * FROM asignaciones_docente WHERE id_asignacion = ?", (asignacion_id,)
        ).fetchone()
        if not asignacion:
            return []

        numero_actividades = self.obtener_numero_actividades(asignacion_id, trimestre_num)
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
            fila = self._fila_base_estudiante(estudiante_row, numero_actividades)
            if registro:
                fila.update(self._expand_dynamic_fields(registro, numero_actividades))
            fila = self.recalcular_fila(
                fila,
                numero_actividades,
                usar_logica_basica=self.usar_logica_cuantitativa_basica(asignacion_id),
            )
            resultado.append(fila)
        return resultado

    def guardar_registros(self, asignacion_id: str, trimestre_num: int, filas: list[dict[str, Any]]) -> tuple[bool, str]:
        if trimestre_num not in (1, 2, 3):
            return False, "Trimestre inválido"

        numero_actividades = self.obtener_numero_actividades(asignacion_id, trimestre_num)
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

            validada = self.validar_y_normalizar_fila(fila, numero_actividades)
            calculada = self.recalcular_fila(
                validada,
                numero_actividades,
                usar_logica_basica=self.usar_logica_cuantitativa_basica(asignacion_id),
            )
            actividades, mejoras = self._extract_activities(calculada, numero_actividades)
            payload = {
                "estudiante_id": estudiante_id,
                "asignacion_id": asignacion_id,
                "trimestre_num": trimestre_num,
                "actividad_1": actividades[0] if len(actividades) > 0 else None,
                "mejora_1": mejoras[0] if len(mejoras) > 0 else None,
                "actividad_2": actividades[1] if len(actividades) > 1 else None,
                "mejora_2": mejoras[1] if len(mejoras) > 1 else None,
                "actividad_3": actividades[2] if len(actividades) > 2 else None,
                "mejora_3": mejoras[2] if len(mejoras) > 2 else None,
                **{campo: calculada.get(campo) for campo in self.SUMMATIVE_FIELDS},
                "promedio_formativo": calculada.get("promedio_formativo"),
                "promedio_sumativo": calculada.get("promedio_sumativo"),
                "nota_trimestral": calculada.get("nota_trimestral"),
                "actividades_json": json.dumps(actividades, ensure_ascii=False),
                "mejoras_json": json.dumps(mejoras, ensure_ascii=False),
            }

            existente = por_estudiante.get(estudiante_id)
            if existente:
                self.repo.actualizar(existente["id_registro"], payload)
            else:
                self.repo.crear({"id_registro": str(uuid.uuid4()), **payload})
            procesados += 1

        return True, f"Registros guardados: {procesados}"

    def guardar_animacion_lectura_evaluacion(self, payload: dict[str, Any]) -> tuple[bool, str]:
        asignacion_id = str(payload.get("asignacion_id") or "").strip()
        trimestre_num = int(payload.get("trimestre_num") or 0)
        nivel = str(payload.get("nivel") or "").strip()
        filas = payload.get("filas") or []

        if not asignacion_id:
            return False, "Seleccione una asignación."
        if trimestre_num not in (1, 2, 3):
            return False, "Seleccione un trimestre válido."
        if not nivel:
            return False, "Seleccione un nivel educativo."
        if not isinstance(filas, list) or not filas:
            return False, "No existen estudiantes para guardar."
        if payload.get("has_invalid_notes"):
            return False, "Existen notas inválidas (fuera de 0-10). Corrija antes de guardar."

        with self.connection:
            self.connection.execute(
                "DELETE FROM animacion_lectura_evaluaciones WHERE asignacion_id = ? AND trimestre_num = ?",
                (asignacion_id, trimestre_num),
            )
            guardados = 0
            for row in filas:
                estudiante_id = str(row.get("estudiante_id") or "").strip()
                if not estudiante_id:
                    continue
                notas = row.get("notas_indicadores") or []
                self.animation_repo.crear(
                    {
                        "id_evaluacion": str(uuid.uuid4()),
                        "asignacion_id": asignacion_id,
                        "trimestre_num": trimestre_num,
                        "nivel": nivel,
                        "estudiante_id": estudiante_id,
                        "notas_indicadores_json": json.dumps(notas, ensure_ascii=False),
                        "valor_promedio": row.get("promedio"),
                        "cualitativo": str(row.get("cualitativo") or "").strip() or None,
                        "cualitativo_1": str(row.get("cualitativo_1") or "").strip() or None,
                    }
                )
                guardados += 1
        return True, f"Evaluaciones de Animación a la Lectura guardadas: {guardados}"

    def obtener_animacion_lectura_evaluacion(
        self,
        asignacion_id: str,
        trimestre_num: int,
        nivel: str | None = None,
    ) -> list[dict[str, Any]]:
        if trimestre_num not in (1, 2, 3):
            raise ValueError("El trimestre debe ser 1, 2 o 3")

        params: list[Any] = [asignacion_id, trimestre_num]
        nivel_clause = ""
        if str(nivel or "").strip():
            nivel_clause = " AND e.nivel = ? "
            params.append(str(nivel).strip())

        rows = self.connection.execute(
            f"""
            SELECT
                e.estudiante_id,
                e.nivel,
                e.notas_indicadores_json,
                e.valor_promedio,
                e.cualitativo,
                e.cualitativo_1,
                s.apellidos,
                s.nombres,
                m.numero_lista
            FROM animacion_lectura_evaluaciones e
            JOIN estudiantes s ON s.id_estudiante = e.estudiante_id
            LEFT JOIN asignaciones_docente a ON a.id_asignacion = e.asignacion_id
            LEFT JOIN matriculas m ON m.estudiante_id = e.estudiante_id
                AND m.curso_id = a.curso_id
                AND m.paralelo_id = a.paralelo_id
                AND m.periodo_id = a.periodo_id
            WHERE e.asignacion_id = ? AND e.trimestre_num = ? {nivel_clause}
            ORDER BY
                CASE WHEN m.numero_lista IS NULL THEN 1 ELSE 0 END,
                m.numero_lista,
                s.apellidos,
                s.nombres
            """,
            params,
        ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "estudiante_id": row["estudiante_id"],
                    "estudiante": f"{row['apellidos']} {row['nombres']}".strip(),
                    "nivel": row["nivel"],
                    "notas_indicadores": self._json_to_list(row["notas_indicadores_json"]),
                    "valor": row["valor_promedio"],
                    "cualitativo": str(row["cualitativo"] or ""),
                    "cualitativo_1": str(row["cualitativo_1"] or ""),
                }
            )
        return out

    def guardar_orientacion_vocacional_evaluacion(self, payload: dict[str, Any]) -> tuple[bool, str]:
        asignacion_id = str(payload.get("asignacion_id") or "").strip()
        trimestre_num = int(payload.get("trimestre_num") or 0)
        curso_clave = str(payload.get("curso_clave") or "").strip()
        filas = payload.get("filas") or []

        if not asignacion_id:
            return False, "Seleccione una asignación."
        if trimestre_num not in (1, 2, 3):
            return False, "Seleccione un trimestre válido."
        if curso_clave not in self.ORIENTATION_ALLOWED_COURSE_KEYS:
            return False, "Curso no válido para Orientación Vocacional y Profesional."
        if not isinstance(filas, list) or not filas:
            return False, "No existen estudiantes para guardar."

        with self.connection:
            self.connection.execute(
                "DELETE FROM orientacion_vocacional_evaluaciones WHERE asignacion_id = ? AND trimestre_num = ?",
                (asignacion_id, trimestre_num),
            )
            guardados = 0
            for row in filas:
                estudiante_id = str(row.get("estudiante_id") or "").strip()
                if not estudiante_id:
                    continue
                respuestas = row.get("respuestas") or []
                self.orientation_repo.crear(
                    {
                        "id_evaluacion": str(uuid.uuid4()),
                        "asignacion_id": asignacion_id,
                        "trimestre_num": trimestre_num,
                        "curso_clave": curso_clave,
                        "estudiante_id": estudiante_id,
                        "respuestas_json": json.dumps(respuestas, ensure_ascii=False),
                        "puntaje_total": row.get("puntaje_total"),
                        "calificacion": str(row.get("calificacion") or "").strip() or None,
                    }
                )
                guardados += 1
        return True, f"Evaluaciones de Orientación Vocacional guardadas: {guardados}"

    def obtener_orientacion_vocacional_evaluacion(self, asignacion_id: str, trimestre_num: int) -> list[dict[str, Any]]:
        if trimestre_num not in (1, 2, 3):
            raise ValueError("El trimestre debe ser 1, 2 o 3")
        rows = self.connection.execute(
            """
            SELECT
                e.estudiante_id,
                e.curso_clave,
                e.respuestas_json,
                e.puntaje_total,
                e.calificacion,
                s.apellidos,
                s.nombres,
                m.numero_lista
            FROM orientacion_vocacional_evaluaciones e
            JOIN estudiantes s ON s.id_estudiante = e.estudiante_id
            LEFT JOIN asignaciones_docente a ON a.id_asignacion = e.asignacion_id
            LEFT JOIN matriculas m ON m.estudiante_id = e.estudiante_id
                AND m.curso_id = a.curso_id
                AND m.paralelo_id = a.paralelo_id
                AND m.periodo_id = a.periodo_id
            WHERE e.asignacion_id = ? AND e.trimestre_num = ?
            ORDER BY
                CASE WHEN m.numero_lista IS NULL THEN 1 ELSE 0 END,
                m.numero_lista,
                s.apellidos,
                s.nombres
            """,
            (asignacion_id, trimestre_num),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "estudiante_id": row["estudiante_id"],
                    "estudiante": f"{row['apellidos']} {row['nombres']}".strip(),
                    "curso_clave": str(row["curso_clave"] or ""),
                    "respuestas": self._json_to_list(row["respuestas_json"]),
                    "puntaje_total": row["puntaje_total"],
                    "calificacion": str(row["calificacion"] or ""),
                }
            )
        return out

    def validar_curso_orientacion_vocacional(self, asignacion_id: str) -> tuple[bool, str | None, str]:
        row = self.connection.execute(
            """
            SELECT s.nombre AS asignatura_nombre, c.nombre AS curso_nombre
            FROM asignaciones_docente a
            LEFT JOIN asignaturas s ON s.id_asignatura = a.asignatura_id
            LEFT JOIN cursos c ON c.id_curso = a.curso_id
            WHERE a.id_asignacion = ?
            """,
            (asignacion_id,),
        ).fetchone()
        if not row:
            return False, None, ""
        subject_name = self._normalize_text(str(row["asignatura_nombre"] or ""))
        if subject_name != self.ORIENTATION_SUBJECT_NAME:
            return True, None, str(row["curso_nombre"] or "")
        course_name = str(row["curso_nombre"] or "")
        course_key = self.detect_orientation_course_key(course_name)
        if course_key not in self.ORIENTATION_ALLOWED_COURSE_KEYS:
            return False, None, course_name
        return True, course_key, course_name

    @classmethod
    def detect_orientation_course_key(cls, course_name: str) -> str | None:
        normalized = cls._normalize_text(course_name)
        tokens = set(normalized.split())
        if any(t in tokens for t in {"8", "8vo", "octavo"}):
            return "8"
        if any(t in tokens for t in {"9", "9no", "noveno"}):
            return "9"
        if any(t in tokens for t in {"10", "10mo", "decimo", "decimo"}):
            return "10"
        return None

    def validar_y_normalizar_fila(self, fila: dict[str, Any], numero_actividades: int = 3) -> dict[str, Any]:
        salida = dict(fila)
        for idx in range(1, numero_actividades + 1):
            salida[f"actividad_{idx}"] = self._normalizar_nota(fila.get(f"actividad_{idx}"), f"actividad_{idx}")
            salida[f"mejora_{idx}"] = self._normalizar_nota(fila.get(f"mejora_{idx}"), f"mejora_{idx}")
        for campo in self.SUMMATIVE_FIELDS:
            salida[campo] = self._normalizar_nota(fila.get(campo), campo)
        return salida

    def recalcular_fila(self, fila: dict[str, Any], numero_actividades: int = 3, usar_logica_basica: bool = False) -> dict[str, Any]:
        data = self.validar_y_normalizar_fila(fila, numero_actividades)

        actividades_formativas = []
        for idx in range(1, numero_actividades + 1):
            actividad = data.get(f"actividad_{idx}")
            if actividad is None:
                continue
            actividades_formativas.append((actividad, data.get(f"mejora_{idx}")))

        promedios_actividades: list[float | None] = []
        for idx in range(1, numero_actividades + 1):
            promedio = calcular_promedio_actividad(data.get(f"actividad_{idx}"), data.get(f"mejora_{idx}"))
            data[f"promedio_{idx}"] = promedio
            promedios_actividades.append(promedio)

        promedio_eval_sumativa = calcular_promedio_evaluacion_sumativa(data.get("proyecto"), data.get("evaluacion"))
        promedio_con_mejora = calcular_promedio_con_mejora(promedio_eval_sumativa, data.get("refuerzo"), data.get("mejora_sumativa"))
        promedio_formativa = calcular_promedio_evaluacion_formativa(promedios_actividades)
        if usar_logica_basica:
            componentes = [v for v in [*promedios_actividades, data.get("proyecto"), data.get("evaluacion")] if v is not None]
            promedio_trimestral = redondear_2_decimales(sum(componentes) / len(componentes)) if componentes else None
            promedio_formativa_70 = None
            promedio_sumativa_30 = None
            promedio_con_mejora = None
            promedio_eval_sumativa = None
        else:
            promedio_formativa_70 = redondear_2_decimales(promedio_formativa * 0.70) if promedio_formativa is not None else None
            promedio_sumativa_30 = redondear_2_decimales(promedio_con_mejora * 0.30) if promedio_con_mejora is not None else None
            promedio_trimestral = (
                redondear_2_decimales(promedio_formativa_70 + promedio_sumativa_30)
                if promedio_formativa_70 is not None and promedio_sumativa_30 is not None
                else None
            )

        data["promedio_evaluacion_sumativa"] = promedio_eval_sumativa
        data["promedio_con_mejora_sumativa"] = promedio_con_mejora
        data["promedio_formativo"] = promedio_formativa
        data["promedio_formativo_70"] = promedio_formativa_70
        data["promedio_sumativo_30"] = promedio_sumativa_30
        data["promedio_sumativo"] = promedio_con_mejora
        data["nota_trimestral"] = promedio_trimestral
        data["cualitativo"] = calcular_cualitativo_trimestral(promedio_trimestral)
        data["cualitativo_adicional"] = (
            self._calcular_equivalencia_egb_basica(data["cualitativo"]) if usar_logica_basica else calcular_escala_cualitativa(promedio_trimestral)
        )
        return data

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

    def _normalizar_nota(self, valor: Any, campo: str) -> float | None:
        if valor is None:
            return None

        texto = str(valor).strip()
        if texto == "":
            return None
        if texto.upper() in {"J", "JP", "JUST", "JUSTIFICADO", "NP", "N/P", "NO PRESENTADO"}:
            return None

        texto_normalizado = texto.replace(",", ".")
        try:
            nota = float(texto_normalizado)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Valor no numérico en {campo}") from exc

        if nota < self.min_grade or nota > self.max_grade:
            raise ValueError(f"Valor fuera de rango en {campo}. Rango permitido {self.min_grade} a {self.max_grade}")

        return redondear_2_decimales(nota)

    def _fila_base_estudiante(self, estudiante: dict[str, Any], numero_actividades: int) -> dict[str, Any]:
        base = {
            "id_registro": None,
            "estudiante_id": estudiante["id_estudiante"],
            "estudiante": f"{estudiante.get('apellidos', '')} {estudiante.get('nombres', '')}".strip(),
            "codigo": estudiante.get("codigo"),
            "numero_lista": estudiante.get("numero_lista"),
            "asignacion_id": None,
            "trimestre_num": None,
            "proyecto": None,
            "evaluacion": None,
            "refuerzo": None,
            "mejora_sumativa": None,
            "promedio_evaluacion_sumativa": None,
            "promedio_con_mejora_sumativa": None,
            "promedio_formativo": None,
            "promedio_formativo_70": None,
            "promedio_sumativo_30": None,
            "promedio_sumativo": None,
            "nota_trimestral": None,
            "cualitativo": "",
            "cualitativo_adicional": "",
        }
        for idx in range(1, numero_actividades + 1):
            base[f"actividad_{idx}"] = None
            base[f"mejora_{idx}"] = None
            base[f"promedio_{idx}"] = None
        return base

    def _expand_dynamic_fields(self, registro: dict[str, Any], numero_actividades: int) -> dict[str, Any]:
        out = dict(registro)
        actividades = self._json_to_list(registro.get("actividades_json"))
        mejoras = self._json_to_list(registro.get("mejoras_json"))

        legacy_actividades = [registro.get("actividad_1"), registro.get("actividad_2"), registro.get("actividad_3")]
        legacy_mejoras = [registro.get("mejora_1"), registro.get("mejora_2"), registro.get("mejora_3")]
        for idx in range(3):
            if idx >= len(actividades):
                actividades.append(legacy_actividades[idx])
            if idx >= len(mejoras):
                mejoras.append(legacy_mejoras[idx])

        while len(actividades) < numero_actividades:
            actividades.append(None)
        while len(mejoras) < numero_actividades:
            mejoras.append(None)

        for idx in range(1, numero_actividades + 1):
            out[f"actividad_{idx}"] = actividades[idx - 1]
            out[f"mejora_{idx}"] = mejoras[idx - 1]
        return out

    @staticmethod
    def _json_to_list(value: Any) -> list[Any]:
        if not value:
            return []
        try:
            data = json.loads(value)
            return data if isinstance(data, list) else []
        except Exception:  # noqa: BLE001
            return []

    @staticmethod
    def _extract_activities(data: dict[str, Any], numero_actividades: int) -> tuple[list[Any], list[Any]]:
        actividades = [data.get(f"actividad_{idx}") for idx in range(1, numero_actividades + 1)]
        mejoras = [data.get(f"mejora_{idx}") for idx in range(1, numero_actividades + 1)]
        return actividades, mejoras

    @staticmethod
    def _parse_metadata_json(raw_value: Any, numero_actividades: int) -> list[dict[str, str]]:
        if not raw_value:
            return GradeRegistrationService._normalize_activity_metadata([], numero_actividades)
        try:
            data = json.loads(raw_value)
        except Exception:  # noqa: BLE001
            data = []
        if not isinstance(data, list):
            data = []
        return GradeRegistrationService._normalize_activity_metadata(data, numero_actividades)

    @staticmethod
    def _normalize_activity_metadata(data: list[Any], numero_actividades: int) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for idx in range(numero_actividades):
            item = data[idx] if idx < len(data) and isinstance(data[idx], dict) else {}
            out.append(
                {
                    "nombre": str(item.get("nombre", "")).strip(),
                    "fecha_actividad": str(item.get("fecha_actividad", "")).strip(),
                    "fecha_refuerzo": str(item.get("fecha_refuerzo", "")).strip(),
                }
            )
        return out

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFD", str(value or "").strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())
    def usar_logica_cuantitativa_basica(self, asignacion_id: str) -> bool:
        row = self.connection.execute(
            """
            SELECT s.nombre AS asignatura_nombre, c.nombre AS curso_nombre
            FROM asignaciones_docente a
            LEFT JOIN asignaturas s ON s.id_asignatura = a.asignatura_id
            LEFT JOIN cursos c ON c.id_curso = a.curso_id
            WHERE a.id_asignacion = ?
            """,
            (asignacion_id,),
        ).fetchone()
        if not row:
            return False
        subject_name = self._normalize_text(str(row["asignatura_nombre"] or ""))
        if subject_name in self.EXCLUDED_SPECIAL_SUBJECTS:
            return False
        return self._detectar_segundo_tercero_cuarto_egb(str(row["curso_nombre"] or ""))

    @classmethod
    def _detectar_segundo_tercero_cuarto_egb(cls, curso_nombre: str) -> bool:
        normalized = cls._normalize_text(curso_nombre)
        tokens = set(normalized.split())
        if "egb" not in tokens:
            return False
        return any(t in tokens for t in {"2do", "segundo", "3ro", "tercero", "4to", "cuarto"})
