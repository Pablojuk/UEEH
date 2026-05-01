"""Pruebas para servicio de acompañamiento integral en el aula."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.application.services.classroom_accompaniment_service import ClassroomAccompanimentService
from src.infrastructure.persistence.db import initialize_database


class TestClassroomAccompanimentService(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp.name
        tmp.close()
        self.conn = initialize_database(self.db_path)
        self.service = ClassroomAccompanimentService(self.conn)
        self._seed_base_data()

    def tearDown(self) -> None:
        self.conn.close()
        p = Path(self.db_path)
        if p.exists():
            p.unlink()

    def _seed_base_data(self) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO docentes (id_docente, nombres, apellidos, identificacion, titulo, activo) VALUES (?,?,?,?,?,?)",
                ("D1", "Ana", "Pérez", "123", "Lic.", 1),
            )
            self.conn.execute("INSERT INTO asignaturas (id_asignatura, nombre, codigo) VALUES (?,?,?)", ("A1", "Matemática", "MAT"))
            self.conn.execute("INSERT INTO cursos (id_curso, nombre, nivel) VALUES (?,?,?)", ("C1", "Primero", "EGB"))
            self.conn.execute("INSERT INTO paralelos (id_paralelo, nombre) VALUES (?,?)", ("P1", "A"))
            self.conn.execute(
                "INSERT INTO periodos_lectivos (id_periodo, anio_inicio, anio_fin, fecha_inicio, fecha_fin) VALUES (?,?,?,?,?)",
                ("2025-2026", 2025, 2026, None, None),
            )
            self.conn.execute(
                "INSERT INTO asignaciones_docente (id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) VALUES (?,?,?,?,?,?)",
                ("AS1", "D1", "A1", "C1", "P1", "2025-2026"),
            )
            self.conn.execute(
                "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres, identificacion) VALUES (?,?,?,?,?)",
                ("E1", "001", "López", "María", "111"),
            )
            self.conn.execute(
                "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id, numero_lista) VALUES (?,?,?,?,?,?)",
                ("M1", "E1", "C1", "P1", "2025-2026", 1),
            )

    def test_cargar_evaluacion_con_estudiantes(self) -> None:
        payload = self.service.cargar_evaluacion("AS1", 1)
        self.assertEqual(len(payload["students"]), 1)
        self.assertTrue(len(payload["active_skills"]) > 0)

    def test_guardar_y_recargar_evaluacion_por_trimestre(self) -> None:
        active_skills = ["autoconocimiento", "pensamiento_critico"]
        responses_t1 = {
            "E1": {
                "autoconocimiento": "Siempre",
                "pensamiento_critico": "Frecuentemente",
            }
        }
        ok, _ = self.service.guardar_evaluacion("AS1", 1, active_skills, responses_t1)
        self.assertTrue(ok)

        payload_t1 = self.service.cargar_evaluacion("AS1", 1)
        self.assertEqual(payload_t1["responses"]["E1"]["autoconocimiento"], "Siempre")
        self.assertEqual(payload_t1["responses"]["E1"]["pensamiento_critico"], "Frecuentemente")

        responses_t2 = {"E1": {"autoconocimiento": "Nunca", "pensamiento_critico": "Nunca"}}
        ok2, _ = self.service.guardar_evaluacion("AS1", 2, active_skills, responses_t2)
        self.assertTrue(ok2)

        payload_t2 = self.service.cargar_evaluacion("AS1", 2)
        self.assertEqual(payload_t2["responses"]["E1"]["autoconocimiento"], "Nunca")
        self.assertEqual(payload_t2["responses"]["E1"]["pensamiento_critico"], "Nunca")

        payload_t1_again = self.service.cargar_evaluacion("AS1", 1)
        self.assertEqual(payload_t1_again["responses"]["E1"]["autoconocimiento"], "Siempre")

    def test_calculo_resultados(self) -> None:
        result = self.service.calcular_resultado_estudiante(
            {
                "autoconocimiento": "Siempre",
                "pensamiento_critico": "Frecuentemente",
                "manejo_problemas": "Nunca",
            },
            ["autoconocimiento", "pensamiento_critico", "manejo_problemas"],
        )
        self.assertEqual(result["total_siempre"], 1)
        self.assertEqual(result["total_frecuentemente"], 1)
        self.assertEqual(result["total_nunca"], 1)
        self.assertEqual(result["puntaje_total_ponderado"], 8)
        self.assertIsInstance(result["valoracion_final"], str)

    def test_no_permite_guardar_mas_de_nueve_habilidades_activas(self) -> None:
        active_skills = [f"skill_{i}" for i in range(10)]
        ok, message = self.service.guardar_evaluacion("AS1", 1, active_skills, {})
        self.assertFalse(ok)
        self.assertIn("hasta 9 habilidades", message)

    def test_valoracion_final_comportamiento_por_puntaje(self) -> None:
        result = self.service.calcular_resultado_estudiante(
            {
                "autoconocimiento": "Siempre",
                "pensamiento_critico": "Siempre",
                "manejo_problemas": "Siempre",
                "toma_decisiones": "Siempre",
            },
            ["autoconocimiento", "pensamiento_critico", "manejo_problemas", "toma_decisiones"],
            variant="behavior",
        )
        self.assertEqual(result["puntaje_total_ponderado"], 16)
        self.assertEqual(
            result["valoracion_final"],
            "Transforma los desacuerdos en oportunidades de crecimiento y cooperación.",
        )

    def test_no_regresion_acompanamiento_en_variante_por_defecto(self) -> None:
        result = self.service.calcular_resultado_estudiante(
            {"autoconocimiento": "Siempre", "pensamiento_critico": "Siempre"},
            ["autoconocimiento", "pensamiento_critico"],
        )
        self.assertEqual(result["puntaje_total_ponderado"], 8)
        self.assertEqual(result["valoracion_final"], "")


if __name__ == "__main__":
    unittest.main()
