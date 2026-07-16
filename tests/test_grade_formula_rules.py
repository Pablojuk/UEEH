from __future__ import annotations

import unittest

from src.application.services.grade_registration_service import GradeRegistrationService
from src.infrastructure.persistence.db import initialize_database


class TestGradeFormulaRules(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = initialize_database(":memory:")
        self.service = GradeRegistrationService(self.conn)

    def tearDown(self) -> None:
        self.conn.close()

    def test_reglas_formula_casos_clave(self) -> None:
        row = {
            "actividad_1": 5,
            "mejora_1": 10,
            "actividad_2": 5,
            "mejora_2": None,
            "actividad_3": None,
            "mejora_3": 10,
            "proyecto": 8,
            "evaluacion": 6,
            "refuerzo": 9,
            "mejora_sumativa": 10,
        }
        out = self.service.recalcular_fila(row, numero_actividades=3)

        self.assertEqual(out["promedio_1"], 7.5)
        self.assertEqual(out["promedio_2"], 5.0)
        self.assertIsNone(out["promedio_3"])
        self.assertEqual(out["promedio_evaluacion_sumativa"], 7.0)
        self.assertEqual(out["promedio_con_mejora_sumativa"], 8.67)
        self.assertEqual(out["promedio_formativo"], 6.25)
        self.assertEqual(out["promedio_formativo_70"], 4.38)
        self.assertEqual(out["promedio_sumativo_30"], 2.6)
        self.assertEqual(out["nota_trimestral"], 6.98)
        self.assertEqual(out["cualitativo"], "B-")

    def test_actividad_vacia_no_cuenta_como_cero(self) -> None:
        row = {
            "actividad_1": 7.5,
            "mejora_1": None,
            "actividad_2": 8,
            "mejora_2": None,
            "actividad_3": 5,
            "mejora_3": None,
            "actividad_4": None,
            "mejora_4": None,
            "proyecto": 8,
            "evaluacion": 6,
            "refuerzo": None,
            "mejora_sumativa": None,
        }
        out = self.service.recalcular_fila(row, numero_actividades=4)
        self.assertEqual(out["promedio_formativo"], 6.83)


if __name__ == "__main__":
    unittest.main()
