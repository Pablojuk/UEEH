"""Servicio de asistencias: sábana mensual, justificaciones y consolidados."""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any


class AttendanceService:
    VALID = {"P", "A", "F", "J"}

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list_assignments(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT a.id_asignacion, s.nombre AS asignatura, c.nombre AS curso, p.nombre AS paralelo, a.periodo_id
            FROM asignaciones_docente a
            LEFT JOIN asignaturas s ON s.id_asignatura = a.asignatura_id
            LEFT JOIN cursos c ON c.id_curso = a.curso_id
            LEFT JOIN paralelos p ON p.id_paralelo = a.paralelo_id
            ORDER BY s.nombre, c.nombre, p.nombre
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def list_students_for_assignment(self, assignment_id: str) -> list[dict[str, Any]]:
        asign = self.connection.execute("SELECT curso_id, paralelo_id, periodo_id FROM asignaciones_docente WHERE id_asignacion=?", (assignment_id,)).fetchone()
        if not asign:
            return []
        rows = self.connection.execute(
            """
            SELECT e.id_estudiante, e.apellidos || ' ' || e.nombres AS estudiante, m.numero_lista
            FROM matriculas m JOIN estudiantes e ON e.id_estudiante=m.estudiante_id
            WHERE m.curso_id=? AND m.paralelo_id=? AND m.periodo_id=?
            ORDER BY CASE WHEN m.numero_lista IS NULL THEN 1 ELSE 0 END, m.numero_lista, e.apellidos, e.nombres
            """, (asign["curso_id"], asign["paralelo_id"], asign["periodo_id"]))
        return [dict(r) for r in rows]

    def weekdays_for_month(self, year: int, month: int) -> list[date]:
        d = date(year, month, 1)
        result = []
        while d.month == month:
            if d.weekday() < 5:
                result.append(d)
            d += timedelta(days=1)
        return result[:20]

    def load_month_sheet(self, assignment_id: str, year: int, month: int) -> dict[tuple[str, str], str]:
        start = date(year, month, 1).isoformat()
        end = (date(year + (month // 12), (month % 12) + 1, 1) - timedelta(days=1)).isoformat()
        rows = self.connection.execute(
            "SELECT student_id, date, status FROM attendance_records WHERE assignment_id=? AND date BETWEEN ? AND ?",
            (assignment_id, start, end),
        ).fetchall()
        return {(r["student_id"], r["date"]): r["status"] for r in rows}

    def save_attendance(self, assignment_id: str, records: list[dict[str, Any]]) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self.connection:
            for rec in records:
                status = str(rec.get("status") or "").strip().upper()
                if status and status not in self.VALID:
                    continue
                self.connection.execute(
                    """
                    INSERT INTO attendance_records(id, assignment_id, student_id, date, status, observation, created_at, updated_at)
                    VALUES (lower(hex(randomblob(16))), ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(assignment_id, student_id, date)
                    DO UPDATE SET status=excluded.status, observation=excluded.observation, updated_at=excluded.updated_at
                    """,
                    (assignment_id, rec.get("student_id"), rec.get("date"), status or None, rec.get("observation"), now, now),
                )

    def save_justification(self, assignment_id: str, student_id: str, on_date: str, reason: str, observation: str) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self.connection:
            self.connection.execute(
                "INSERT INTO attendance_justifications(id, assignment_id, student_id, date, reason, observation, created_at) VALUES (lower(hex(randomblob(16))),?,?,?,?,?,?,?)",
                (assignment_id, student_id, on_date, reason, observation, now),
            )
            self.connection.execute(
                """
                INSERT INTO attendance_records(id, assignment_id, student_id, date, status, observation, created_at, updated_at)
                VALUES (lower(hex(randomblob(16))), ?, ?, ?, 'J', ?, ?, ?)
                ON CONFLICT(assignment_id, student_id, date)
                DO UPDATE SET status='J', observation=excluded.observation, updated_at=excluded.updated_at
                """,
                (assignment_id, student_id, on_date, observation, now, now),
            )
