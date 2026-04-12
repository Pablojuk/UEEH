"""Pruebas del servicio de resumen académico."""

from __future__ import annotations

import unittest

from src.application.services.academic_summary_service import AcademicSummaryService
from src.infrastructure.persistence.db import initialize_database


class TestAcademicSummaryService(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = initialize_database(":memory:")
        self.service = AcademicSummaryService(self.conn)
        self._seed_context()

    def tearDown(self) -> None:
        self.conn.close()

    def _seed_context(self) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO docentes (id_docente, nombres, apellidos, identificacion, activo) VALUES (?, ?, ?, ?, ?)",
                ("D1", "Ana", "Perez", "123", 1),
            )
            self.conn.execute(
                "INSERT INTO asignaturas (id_asignatura, nombre, codigo) VALUES (?, ?, ?)",
                ("A1", "Matematica", "MAT"),
            )
            self.conn.execute(
                "INSERT INTO cursos (id_curso, nombre, nivel) VALUES (?, ?, ?)",
                ("C1", "Primero", "Basica"),
            )
            self.conn.execute("INSERT INTO paralelos (id_paralelo, nombre) VALUES (?, ?)", ("P1", "A"))
            self.conn.execute(
                "INSERT INTO periodos_lectivos (id_periodo, anio_inicio, anio_fin, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?, ?)",
                ("2025-2026", 2025, 2026, None, None),
            )
            self.conn.execute(
                "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres, identificacion) VALUES (?, ?, ?, ?, ?)",
                ("E1", "EST-1", "Lopez", "Maria", "999"),
            )
            self.conn.execute(
                "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id, numero_lista) VALUES (?, ?, ?, ?, ?, ?)",
                ("M1", "E1", "C1", "P1", "2025-2026", 1),
            )
            self.conn.execute(
                "INSERT INTO asignaciones_docente (id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) VALUES (?, ?, ?, ?, ?, ?)",
                ("AS1", "D1", "A1", "C1", "P1", "2025-2026"),
            )

            self.conn.execute(
                """
                INSERT INTO grade_records (
                    id_registro, estudiante_id, asignacion_id, trimestre_num,
                    actividad_1, mejora_1, actividad_2, mejora_2, actividad_3, mejora_3,
                    proyecto, evaluacion, refuerzo, mejora_sumativa,
                    promedio_formativo, promedio_sumativo, nota_trimestral
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("G1", "E1", "AS1", 1, 8, None, 8, None, 8, None, 8, 8, 8, None, 8, 8, 8),
            )
            self.conn.execute(
                """
                INSERT INTO grade_records (
                    id_registro, estudiante_id, asignacion_id, trimestre_num,
                    actividad_1, mejora_1, actividad_2, mejora_2, actividad_3, mejora_3,
                    proyecto, evaluacion, refuerzo, mejora_sumativa,
                    promedio_formativo, promedio_sumativo, nota_trimestral
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("G2", "E1", "AS1", 2, 7, None, 7, None, 7, None, 7, 7, 7, None, 7, 7, 7),
            )
            self.conn.execute(
                """
                INSERT INTO grade_records (
                    id_registro, estudiante_id, asignacion_id, trimestre_num,
                    actividad_1, mejora_1, actividad_2, mejora_2, actividad_3, mejora_3,
                    proyecto, evaluacion, refuerzo, mejora_sumativa,
                    promedio_formativo, promedio_sumativo, nota_trimestral
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("G3", "E1", "AS1", 3, 6, None, 6, None, 6, None, 6, 6, 6, None, 6, 6, 6),
            )

    def test_consolidar_notas_3_trimestres(self) -> None:
        rows = self.service.obtener_resumen_por_asignacion("AS1")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["trimestre_1"], 8)
        self.assertEqual(rows[0]["trimestre_2"], 7)
        self.assertEqual(rows[0]["trimestre_3"], 6)

    def test_calcular_promedio_final_cualitativo_observacion(self) -> None:
        row = self.service.obtener_resumen_por_asignacion("AS1")[0]
        self.assertEqual(row["promedio_final"], 7.0)
        self.assertEqual(row["cualitativo"], "B-")
        self.assertEqual(row["cualitativo_final"], "B-")
        self.assertEqual(row["observacion"], "APB")

    def test_aplicar_supletorio_correctamente(self) -> None:
        ok, _ = self.service.guardar_supletorios("AS1", [{"estudiante_id": "E1", "supletorio": 7}])
        self.assertTrue(ok)
        row = self.service.obtener_resumen_por_asignacion("AS1")[0]
        self.assertEqual(row["nota_definitiva"], 7.0)

    def test_manejar_estudiante_sin_todos_los_trimestres(self) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM grade_records WHERE trimestre_num = 3")
        row = self.service.obtener_resumen_por_asignacion("AS1")[0]
        self.assertEqual(row["trimestre_3"], None)
        self.assertEqual(row["promedio_final"], 5.0)

    def test_contexto_sin_estudiantes(self) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM matriculas")
        rows = self.service.obtener_resumen_por_asignacion("AS1")
        self.assertEqual(rows, [])

    def test_reporte_trimestral_usa_trimestre_seleccionado(self) -> None:
        rows = self.service.obtener_reporte_trimestral("AS1", 2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["aportes_calificacion"], 7)
        self.assertEqual(rows[0]["sumativas_calificacion"], 7)

    def test_reporte_anual_incluye_equivalencias_por_trimestre(self) -> None:
        row = self.service.obtener_reporte_anual("AS1")[0]
        self.assertEqual(row["equivalencia_t1"], "AA")
        self.assertEqual(row["equivalencia_t2"], "AA")
        self.assertEqual(row["equivalencia_t3"], "PA")


if __name__ == "__main__":
    unittest.main()
