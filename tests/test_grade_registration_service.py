"""Pruebas del servicio de registro de notas."""

from __future__ import annotations

import unittest

from src.application.services.grade_registration_service import GradeRegistrationService
from src.infrastructure.persistence.db import initialize_database
from src.infrastructure.persistence.seed import CATALOG_COURSES


class TestGradeRegistrationService(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = initialize_database(":memory:")
        self.service = GradeRegistrationService(self.conn)
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
                "INSERT INTO asignaturas (id_asignatura, nombre, codigo) VALUES (?, ?, ?)",
                ("A2", "Orientación Vocacional y Profesional", "OVP"),
            )
            self.conn.execute(
                "INSERT INTO cursos (id_curso, nombre, nivel) VALUES (?, ?, ?)",
                ("C1", "Primero", "Basica"),
            )
            self.conn.execute(
                "INSERT INTO cursos (id_curso, nombre, nivel) VALUES (?, ?, ?)",
                ("C2", "Segundo de EGB", "Basica"),
            )
            self.conn.execute(
                "INSERT INTO cursos (id_curso, nombre, nivel) VALUES (?, ?, ?)",
                ("C8", "8vo de EGB", "Básica Superior"),
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
                "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id, numero_lista) VALUES (?, ?, ?, ?, ?, ?)",
                ("M2", "E1", "C8", "P1", "2025-2026", 1),
            )
            self.conn.execute(
                "INSERT INTO asignaciones_docente (id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) VALUES (?, ?, ?, ?, ?, ?)",
                ("AS1", "D1", "A1", "C1", "P1", "2025-2026"),
            )
            self.conn.execute(
                "INSERT INTO asignaciones_docente (id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) VALUES (?, ?, ?, ?, ?, ?)",
                ("AS-OVP", "D1", "A2", "C8", "P1", "2025-2026"),
            )
            self.conn.execute(
                "INSERT INTO asignaciones_docente (id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) VALUES (?, ?, ?, ?, ?, ?)",
                ("AS-EGB", "D1", "A1", "C2", "P1", "2025-2026"),
            )

    def test_cargar_estudiantes_de_contexto_valido(self) -> None:
        rows = self.service.cargar_registro("AS1", 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["estudiante_id"], "E1")

    def test_guardar_notas_nuevas(self) -> None:
        ok, _ = self.service.guardar_registros(
            "AS1",
            1,
            [
                {
                    "estudiante_id": "E1",
                    "actividad_1": 9,
                    "mejora_1": 10,
                    "actividad_2": 8,
                    "mejora_2": None,
                    "actividad_3": 7,
                    "mejora_3": 8,
                    "proyecto": 9,
                    "evaluacion": 8,
                    "refuerzo": 7,
                    "mejora_sumativa": 10,
                }
            ],
        )
        self.assertTrue(ok)

        row = self.conn.execute(
            "SELECT * FROM grade_records WHERE estudiante_id = ? AND asignacion_id = ? AND trimestre_num = ?",
            ("E1", "AS1", 1),
        ).fetchone()
        self.assertIsNotNone(row)

    def test_actualizar_notas_existentes_sin_duplicar(self) -> None:
        self.service.guardar_registros("AS1", 1, [{"estudiante_id": "E1", "actividad_1": 7, "proyecto": 7}])
        self.service.guardar_registros("AS1", 1, [{"estudiante_id": "E1", "actividad_1": 10, "proyecto": 9}])

        count = self.conn.execute(
            "SELECT COUNT(*) AS total FROM grade_records WHERE estudiante_id = ? AND asignacion_id = ? AND trimestre_num = ?",
            ("E1", "AS1", 1),
        ).fetchone()["total"]
        self.assertEqual(count, 1)

        row = self.conn.execute(
            "SELECT actividad_1, proyecto FROM grade_records WHERE estudiante_id = ? AND asignacion_id = ? AND trimestre_num = ?",
            ("E1", "AS1", 1),
        ).fetchone()
        self.assertEqual(row["actividad_1"], 10)
        self.assertEqual(row["proyecto"], 9)

    def test_recalcular_promedios_correctamente(self) -> None:
        fila = self.service.recalcular_fila(
            {
                "estudiante_id": "E1",
                "actividad_1": 9,
                "mejora_1": 10,
                "actividad_2": 8,
                "mejora_2": None,
                "actividad_3": 7,
                "mejora_3": 8,
                "proyecto": 9,
                "evaluacion": 8,
                "refuerzo": 7,
                "mejora_sumativa": 10,
            }
        )
        self.assertEqual(fila["promedio_formativo"], 8.33)
        self.assertEqual(fila["promedio_evaluacion_sumativa"], 8.5)
        self.assertEqual(fila["promedio_sumativo"], 8.5)
        self.assertEqual(fila["promedio_formativo_70"], 5.83)
        self.assertEqual(fila["promedio_sumativo_30"], 2.55)
        self.assertEqual(fila["nota_trimestral"], 8.38)
        self.assertEqual(fila["cualitativo_adicional"], "AA")

    def test_equivalencia_reutiliza_limite_academico_de_4_01(self) -> None:
        fila = self.service.recalcular_fila(
            {
                "estudiante_id": "E1",
                "actividad_1": 4.01,
                "actividad_2": 4.01,
                "actividad_3": 4.01,
                "proyecto": 4.01,
                "evaluacion": 4.01,
            }
        )
        self.assertEqual(fila["nota_trimestral"], 4.01)
        self.assertEqual(fila["cualitativo_adicional"], "PA")

    def test_acepta_decimal_con_coma_y_redondea(self) -> None:
        fila = self.service.validar_y_normalizar_fila(
            {
                "actividad_1": "8,756",
                "mejora_1": None,
                "actividad_2": "7.1",
                "mejora_2": None,
                "actividad_3": "6",
                "mejora_3": None,
                "proyecto": "9,5",
                "evaluacion": "8.333",
                "refuerzo": None,
                "mejora_sumativa": None,
            }
        )
        self.assertEqual(fila["actividad_1"], 8.76)
        self.assertEqual(fila["evaluacion"], 8.33)

    def test_contexto_sin_estudiantes_retorna_vacio(self) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO asignaciones_docente (id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) VALUES (?, ?, ?, ?, ?, ?)",
                ("AS2", "D1", "A1", "C1", "P1", "2025-2026"),
            )
            self.conn.execute("DELETE FROM matriculas")

        rows = self.service.cargar_registro("AS2", 1)
        self.assertEqual(rows, [])

    def test_cargar_estudiantes_de_2do_egb_en_asignacion_cuantitativa(self) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id, numero_lista) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("M-EGB", "E1", "C2", "P1", "2025-2026", 1),
            )

        rows = self.service.cargar_registro("AS-EGB", 1)
        self.assertEqual([row["estudiante_id"] for row in rows], ["E1"])

    def test_mensaje_claro_cuando_asignacion_no_tiene_matriculas(self) -> None:
        rows, message = self.service.cargar_registro_con_estado("AS-EGB", 1)
        self.assertEqual(rows, [])
        self.assertEqual(
            message,
            "No se encontraron estudiantes matriculados para Segundo de EGB, "
            "paralelo A, período 2025-2026.",
        )

    def test_diferencia_curso_paralelo_y_periodo_por_ids_exactos(self) -> None:
        with self.conn:
            self.conn.execute("INSERT INTO paralelos (id_paralelo, nombre) VALUES (?, ?)", ("P2", "B"))
            self.conn.execute(
                "INSERT INTO periodos_lectivos (id_periodo, anio_inicio, anio_fin) VALUES (?, ?, ?)",
                ("2026-2027", 2026, 2027),
            )
            for student_id in ("E2", "E3", "E4"):
                self.conn.execute(
                    "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres) VALUES (?, ?, ?, ?)",
                    (student_id, f"EST-{student_id}", "Prueba", student_id),
                )
            self.conn.executemany(
                "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    ("MX1", "E2", "C2", "P1", "2025-2026"),
                    ("MX2", "E3", "C2", "P2", "2025-2026"),
                    ("MX3", "E4", "C2", "P1", "2026-2027"),
                ],
            )

        rows = self.service.cargar_registro("AS-EGB", 1)
        self.assertEqual([row["estudiante_id"] for row in rows], ["E2"])

    def test_carga_estudiantes_en_todos_los_cursos_del_catalogo(self) -> None:
        with self.conn:
            for index, course in enumerate(CATALOG_COURSES):
                student_id = f"EC-{index}"
                self.conn.execute(
                    "INSERT INTO cursos (id_curso, nombre, nivel) VALUES (?, ?, ?)",
                    (course["id_curso"], course["nombre"], course["nivel"]),
                )
                self.conn.execute(
                    "INSERT INTO estudiantes (id_estudiante, codigo, apellidos, nombres) VALUES (?, ?, ?, ?)",
                    (student_id, f"COD-{index}", "Sintético", str(index)),
                )
                self.conn.execute(
                    "INSERT INTO matriculas (id_matricula, estudiante_id, curso_id, paralelo_id, periodo_id) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (f"MC-{index}", student_id, course["id_curso"], "P1", "2025-2026"),
                )
                self.conn.execute(
                    "INSERT INTO asignaciones_docente "
                    "(id_asignacion, docente_id, asignatura_id, curso_id, paralelo_id, periodo_id) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (f"AC-{index}", "D1", "A1", course["id_curso"], "P1", "2025-2026"),
                )

        for index, _course in enumerate(CATALOG_COURSES):
            with self.subTest(course=index):
                rows = self.service.cargar_registro(f"AC-{index}", 1)
                self.assertEqual([row["estudiante_id"] for row in rows], [f"EC-{index}"])

    def test_persistencia_metadata_actividades(self) -> None:
        ok, _ = self.service.configurar_numero_actividades("AS1", 1, 2)
        self.assertTrue(ok)
        ok, _ = self.service.guardar_configuracion_actividades(
            "AS1",
            1,
            [
                {"nombre": "Trabajo grupal", "fecha_actividad": "2026-04-01", "fecha_refuerzo": "2026-04-05"},
                {"nombre": "Exposición", "fecha_actividad": "2026-04-10", "fecha_refuerzo": ""},
            ],
        )
        self.assertTrue(ok)
        cfg = self.service.obtener_configuracion_actividades("AS1", 1)
        self.assertEqual(cfg["numero_actividades"], 2)
        self.assertEqual(cfg["metadata"][0]["nombre"], "Trabajo grupal")
        self.assertEqual(cfg["metadata"][0]["fecha_refuerzo"], "2026-04-05")

    def test_guardar_y_consultar_animacion_lectura(self) -> None:
        ok, message = self.service.guardar_animacion_lectura_evaluacion(
            {
                "asignacion_id": "AS1",
                "trimestre_num": 1,
                "nivel": "media",
                "filas": [
                    {
                        "estudiante_id": "E1",
                        "estudiante": "Lopez Maria",
                        "notas_indicadores": [8.5, 9.0],
                        "promedio": 8.75,
                        "cualitativo": "A-",
                        "cualitativo_1": "A",
                    }
                ],
                "has_invalid_notes": False,
            }
        )
        self.assertTrue(ok)
        self.assertIn("guardadas", message.lower())

        rows = self.service.obtener_animacion_lectura_evaluacion("AS1", 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["estudiante_id"], "E1")
        self.assertEqual(rows[0]["nivel"], "media")
        self.assertEqual(rows[0]["valor"], 8.75)
        self.assertEqual(rows[0]["cualitativo"], "A-")
        self.assertEqual(rows[0]["cualitativo_1"], "A")
        self.assertEqual(rows[0]["notas_indicadores"], [8.5, 9.0])

    def test_guardado_animacion_lectura_rechaza_payload_invalido(self) -> None:
        ok, message = self.service.guardar_animacion_lectura_evaluacion(
            {
                "asignacion_id": "AS1",
                "trimestre_num": 1,
                "nivel": "",
                "filas": [],
                "has_invalid_notes": False,
            }
        )
        self.assertFalse(ok)
        self.assertIn("nivel", message.lower())

    def test_guardar_y_consultar_orientacion_vocacional(self) -> None:
        ok, message = self.service.guardar_orientacion_vocacional_evaluacion(
            {
                "asignacion_id": "AS-OVP",
                "trimestre_num": 1,
                "curso_clave": "8",
                "filas": [
                    {
                        "estudiante_id": "E1",
                        "respuestas": [3, 3, 3, 2, 3],
                        "puntaje_total": 14,
                        "calificacion": "A+",
                    }
                ],
            }
        )
        self.assertTrue(ok)
        self.assertIn("orientación vocacional", message.lower())

        rows = self.service.obtener_orientacion_vocacional_evaluacion("AS-OVP", 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["curso_clave"], "8")
        self.assertEqual(rows[0]["respuestas"], [3, 3, 3, 2, 3])
        self.assertEqual(rows[0]["puntaje_total"], 14)
        self.assertEqual(rows[0]["calificacion"], "A+")

    def test_detecta_curso_orientacion(self) -> None:
        self.assertEqual(self.service.detect_orientation_course_key("Décimo de EGB"), "10")
        self.assertEqual(self.service.detect_orientation_course_key("Noveno"), "9")

    def test_detecta_logica_cuantitativa_basica_y_excluye_especiales(self) -> None:
        self.assertTrue(self.service.usar_logica_cuantitativa_basica("AS-EGB"))
        self.assertFalse(self.service.usar_logica_cuantitativa_basica("AS-OVP"))

    def test_recalculo_logica_cuantitativa_basica(self) -> None:
        fila = self.service.recalcular_fila(
            {
                "estudiante_id": "E1",
                "actividad_1": 8,
                "mejora_1": 10,
                "actividad_2": 7,
                "mejora_2": 7,
                "actividad_3": 9,
                "mejora_3": 9,
                "proyecto": 10,
                "evaluacion": 6,
            },
            usar_logica_basica=True,
        )
        self.assertEqual(fila["nota_trimestral"], 8.2)
        self.assertEqual(fila["cualitativo_adicional"], "Destreza o aprendizaje alcanzado")
        self.assertEqual(self.service.detect_orientation_course_key("8vo EGB"), "8")

    def test_valida_curso_orientacion_desde_asignacion(self) -> None:
        valid, course_key, _ = self.service.validar_curso_orientacion_vocacional("AS-OVP")
        self.assertTrue(valid)
        self.assertEqual(course_key, "8")


if __name__ == "__main__":
    unittest.main()
