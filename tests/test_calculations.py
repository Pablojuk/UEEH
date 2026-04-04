"""Pruebas unitarias para cálculos de dominio."""

import unittest

from src.domain.calculations import (
    calcular_cualitativo,
    calcular_nota_trimestral,
    calcular_observacion_final,
    calcular_promedio_anual,
    calcular_promedio_formativo,
    calcular_promedio_sumativo,
    calcular_resultado_con_supletorio,
    resolver_mejora,
    truncar_2_decimales,
)


class TestTruncamiento(unittest.TestCase):
    def test_truncar_dos_decimales(self) -> None:
        self.assertEqual(truncar_2_decimales(8.999), 8.99)

    def test_truncar_numero_entero(self) -> None:
        self.assertEqual(truncar_2_decimales(7.0), 7.0)


class TestMejora(unittest.TestCase):
    def test_mejora_mayor_aplica_promedio_truncado(self) -> None:
        # (8 + 10) / 2 = 9.0
        self.assertEqual(resolver_mejora(8.0, 10.0), 9.0)

    def test_mejora_igual_no_aplica(self) -> None:
        self.assertEqual(resolver_mejora(7.5, 7.5), 7.5)

    def test_mejora_menor_no_aplica(self) -> None:
        self.assertEqual(resolver_mejora(9.2, 8.0), 9.2)

    def test_sin_mejora(self) -> None:
        self.assertEqual(resolver_mejora(6.8, None), 6.8)


class TestPromedios(unittest.TestCase):
    def test_promedio_formativo_normal(self) -> None:
        actividades = [(8.0, None), (9.0, 10.0), (7.0, 6.0)]
        # Resueltas: 8.0, 9.5, 7.0 -> promedio 8.166... -> 8.16
        self.assertEqual(calcular_promedio_formativo(actividades), 8.16)

    def test_promedio_sumativo_normal(self) -> None:
        evaluaciones = [(7.0, 9.0), (8.0, None)]
        # Resueltas: 8.0, 8.0 -> 8.0
        self.assertEqual(calcular_promedio_sumativo(evaluaciones), 8.0)

    def test_promedio_formativo_vacio(self) -> None:
        self.assertEqual(calcular_promedio_formativo([]), 0.0)

    def test_nota_trimestral_ponderada(self) -> None:
        # 8.16*0.7 + 8*0.3 = 8.112 -> 8.11
        self.assertEqual(calcular_nota_trimestral(8.16, 8.0), 8.11)

    def test_promedio_anual(self) -> None:
        # (8.11 + 7.00 + 9.56) / 3 = 8.2233... -> 8.22
        self.assertEqual(calcular_promedio_anual(8.11, 7.0, 9.56), 8.22)


class TestCualitativoYObservacion(unittest.TestCase):
    def test_cualitativo_limites(self) -> None:
        self.assertEqual(calcular_cualitativo(9.5), "A+")
        self.assertEqual(calcular_cualitativo(8.5), "A-")
        self.assertEqual(calcular_cualitativo(0.5), "E-")

    def test_cualitativo_fuera_escala(self) -> None:
        self.assertEqual(calcular_cualitativo(0.49), "SIN_ESCALA")

    def test_observacion_apb(self) -> None:
        self.assertEqual(calcular_observacion_final(7.0), "APB")

    def test_observacion_spl(self) -> None:
        self.assertEqual(calcular_observacion_final(6.99), "SPL")
        self.assertEqual(calcular_observacion_final(4.01), "SPL")

    def test_observacion_rep(self) -> None:
        self.assertEqual(calcular_observacion_final(4.0), "REP")
        self.assertEqual(calcular_observacion_final(1.0), "REP")


class TestSupletorio(unittest.TestCase):
    def test_sin_necesidad_de_supletorio(self) -> None:
        self.assertEqual(calcular_resultado_con_supletorio(8.33, None), 8.33)

    def test_aprueba_con_supletorio(self) -> None:
        self.assertEqual(calcular_resultado_con_supletorio(6.99, 7.0), 7.0)

    def test_no_aprueba_supletorio(self) -> None:
        self.assertEqual(calcular_resultado_con_supletorio(6.99, 6.5), 6.99)

    def test_sin_nota_supletorio(self) -> None:
        self.assertEqual(calcular_resultado_con_supletorio(5.25, None), 5.25)


if __name__ == "__main__":
    unittest.main()
