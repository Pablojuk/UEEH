"""Servicio de registro de notas por asignación y trimestre."""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

from src.domain.calculations import calcular_nota_trimestral, calcular_promedio_formativo, calcular_promedio_sumativo
from src.infrastructure.persistence.repositories import GradeActivityConfigRepository, GradeRecordsRepository


class GradeRegistrationService:
    """Casos de uso para carga, cálculo y guardado de notas trimestrales."""

    SUMMATIVE_FIELDS = ("proyecto", "evaluacion", "refuerzo", "mejora_sumativa")

    def __init__(self, connection: sqlite3.Connection, min_grade: float = 0.0, max_grade: float = 10.0) -> None:
        self.connection = connection
        self.repo = GradeRecordsRepository(connection)
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
        }
        if row:
            self.activity_config_repo.actualizar(row["id_config"], payload)
        else:
            self.activity_config_repo.crear({"id_config": str(uuid.uuid4()), **payload})
        return True, "Configuración de actividades actualizada"

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
            fila = self.recalcular_fila(fila, numero_actividades)
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
            calculada = self.recalcular_fila(validada, numero_actividades)
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

    def validar_y_normalizar_fila(self, fila: dict[str, Any], numero_actividades: int = 3) -> dict[str, Any]:
        salida = dict(fila)
        for idx in range(1, numero_actividades + 1):
            salida[f"actividad_{idx}"] = self._normalizar_nota(fila.get(f"actividad_{idx}"), f"actividad_{idx}")
            salida[f"mejora_{idx}"] = self._normalizar_nota(fila.get(f"mejora_{idx}"), f"mejora_{idx}")
        for campo in self.SUMMATIVE_FIELDS:
            salida[campo] = self._normalizar_nota(fila.get(campo), campo)
        return salida

    def recalcular_fila(self, fila: dict[str, Any], numero_actividades: int = 3) -> dict[str, Any]:
        data = self.validar_y_normalizar_fila(fila, numero_actividades)

        actividades_formativas = []
        for idx in range(1, numero_actividades + 1):
            actividades_formativas.append((data.get(f"actividad_{idx}") or 0.0, data.get(f"mejora_{idx}")))

        promedio_formativo = calcular_promedio_formativo(actividades_formativas)
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
            "promedio_formativo": 0.0,
            "promedio_sumativo": 0.0,
            "nota_trimestral": 0.0,
        }
        for idx in range(1, numero_actividades + 1):
            base[f"actividad_{idx}"] = None
            base[f"mejora_{idx}"] = None
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
