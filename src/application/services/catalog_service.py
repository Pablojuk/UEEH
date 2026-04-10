"""Servicio de negocio para catálogos académicos."""

from __future__ import annotations

import sqlite3

from src.infrastructure.persistence.repositories import (
    AsignaturasRepository,
    CursosRepository,
    ParalelosRepository,
    PeriodosLectivosRepository,
)


class CatalogService:
    """Gestiona cursos, paralelos, asignaturas y períodos lectivos."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.cursos_repo = CursosRepository(connection)
        self.paralelos_repo = ParalelosRepository(connection)
        self.asignaturas_repo = AsignaturasRepository(connection)
        self.periodos_repo = PeriodosLectivosRepository(connection)

    def crear_curso(self, data: dict) -> None:
        self.cursos_repo.crear(data)

    def listar_cursos(self) -> list[dict]:
        return self.cursos_repo.listar()

    def actualizar_curso(self, course_id: str, data: dict) -> None:
        self.cursos_repo.actualizar(course_id, data)

    def eliminar_curso(self, course_id: str) -> None:
        self.cursos_repo.eliminar(course_id)

    def crear_paralelo(self, data: dict) -> None:
        self.paralelos_repo.crear(data)

    def listar_paralelos(self) -> list[dict]:
        return self.paralelos_repo.listar()

    def actualizar_paralelo(self, parallel_id: str, data: dict) -> None:
        self.paralelos_repo.actualizar(parallel_id, data)

    def eliminar_paralelo(self, parallel_id: str) -> None:
        self.paralelos_repo.eliminar(parallel_id)

    def crear_asignatura(self, data: dict) -> None:
        self.asignaturas_repo.crear(data)

    def listar_asignaturas(self) -> list[dict]:
        return self.asignaturas_repo.listar()

    def actualizar_asignatura(self, subject_id: str, data: dict) -> None:
        self.asignaturas_repo.actualizar(subject_id, data)

    def eliminar_asignatura(self, subject_id: str) -> None:
        self.asignaturas_repo.eliminar(subject_id)

    def crear_periodo_lectivo(self, data: dict) -> None:
        self.periodos_repo.crear(data)

    def listar_periodos_lectivos(self) -> list[dict]:
        return self.periodos_repo.listar()

    def actualizar_periodo_lectivo(self, period_id: str, data: dict) -> None:
        self.periodos_repo.actualizar(period_id, data)

    def eliminar_periodo_lectivo(self, period_id: str) -> None:
        self.periodos_repo.eliminar(period_id)
