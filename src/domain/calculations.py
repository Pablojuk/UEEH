"""Funciones puras de cálculo académico (BLOQUE 1)."""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN
from typing import Iterable, Optional


def truncar_2_decimales(valor: float) -> float:
    """Trunca un valor numérico a 2 decimales (estilo TRUNC de Excel)."""
    return float(Decimal(str(valor)).quantize(Decimal("0.00"), rounding=ROUND_DOWN))


def resolver_mejora(nota_base: float, nota_mejora: Optional[float]) -> float:
    """Resuelve la nota aplicando regla de mejora cuando corresponde."""
    if nota_mejora is None:
        return nota_base

    if nota_mejora > nota_base:
        promedio = (nota_base + nota_mejora) / 2
        return truncar_2_decimales(promedio)

    return nota_base


def _promedio_resuelto(registros: Iterable[tuple[float, Optional[float]]]) -> float:
    valores = [resolver_mejora(base, mejora) for base, mejora in registros]
    if not valores:
        return 0.0
    return truncar_2_decimales(sum(valores) / len(valores))


def calcular_promedio_formativo(
    actividades: Iterable[tuple[float, Optional[float]]],
) -> float:
    """Calcula promedio formativo a partir de actividades (base, mejora)."""
    return _promedio_resuelto(actividades)


def calcular_promedio_sumativo(
    evaluaciones: Iterable[tuple[float, Optional[float]]],
) -> float:
    """Calcula promedio sumativo a partir de evaluaciones (base, mejora)."""
    return _promedio_resuelto(evaluaciones)


def calcular_nota_trimestral(promedio_formativo: float, promedio_sumativo: float) -> float:
    """Calcula nota trimestral con ponderación 70/30."""
    nota = (promedio_formativo * 0.70) + (promedio_sumativo * 0.30)
    return truncar_2_decimales(nota)


def calcular_promedio_anual(trimestre_1: float, trimestre_2: float, trimestre_3: float) -> float:
    """Calcula promedio anual a partir de los 3 trimestres."""
    return truncar_2_decimales((trimestre_1 + trimestre_2 + trimestre_3) / 3)


def calcular_cualitativo(promedio_final: float) -> str:
    """Devuelve escala cualitativa basada en promedio final."""
    escala = (
        (9.5, "A+"),
        (8.5, "A-"),
        (7.5, "B+"),
        (6.5, "B-"),
        (5.5, "C+"),
        (4.5, "C-"),
        (3.5, "D+"),
        (2.5, "D-"),
        (1.5, "E+"),
        (0.5, "E-"),
    )
    for limite, etiqueta in escala:
        if promedio_final >= limite:
            return etiqueta
    return "SIN_ESCALA"


def calcular_observacion_final(promedio_final: float) -> str:
    """Determina observación final según escala institucional."""
    if promedio_final >= 7:
        return "APB"
    if promedio_final > 4:
        return "SPL"
    if promedio_final >= 1:
        return "REP"
    return "REP"


def calcular_resultado_con_supletorio(nota_final: float, nota_supletorio: Optional[float]) -> float:
    """Aplica regla de supletorio y devuelve nota definitiva."""
    if nota_final >= 7:
        return truncar_2_decimales(nota_final)

    if nota_supletorio is not None and nota_supletorio >= 7:
        return 7.0

    return truncar_2_decimales(nota_final)
