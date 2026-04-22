"""Funciones puras de cálculo académico (BLOQUE 1)."""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Iterable, Optional


def truncar_2_decimales(valor: float) -> float:
    """Trunca un valor numérico a 2 decimales (estilo TRUNC de Excel)."""
    return float(Decimal(str(valor)).quantize(Decimal("0.00"), rounding=ROUND_DOWN))


def redondear_2_decimales(valor: float) -> float:
    """Redondea a 2 decimales con criterio estándar."""
    return float(Decimal(str(valor)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))


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


def calcular_promedio_actividad(actividad: Optional[float], refuerzo: Optional[float]) -> Optional[float]:
    if actividad is None:
        return None
    if refuerzo is None:
        return redondear_2_decimales(actividad)
    return redondear_2_decimales((actividad + refuerzo) / 2)


def calcular_promedio_evaluacion_sumativa(
    proyecto_interdisciplinar: Optional[float],
    evaluacion_trimestral: Optional[float],
) -> Optional[float]:
    if proyecto_interdisciplinar is None or evaluacion_trimestral is None:
        return None
    return redondear_2_decimales((proyecto_interdisciplinar + evaluacion_trimestral) / 2)


def calcular_promedio_con_mejora(
    promedio_evaluacion_sumativa: Optional[float],
    calificacion_refuerzo_pedagogico: Optional[float],
    evaluacion_mejora: Optional[float],
) -> Optional[float]:
    if promedio_evaluacion_sumativa is None:
        return None
    valores = [promedio_evaluacion_sumativa]
    if calificacion_refuerzo_pedagogico is not None:
        valores.append(calificacion_refuerzo_pedagogico)
    if evaluacion_mejora is not None:
        valores.append(evaluacion_mejora)
    return redondear_2_decimales(sum(valores) / len(valores))


def calcular_promedio_evaluacion_formativa(lista_promedios_actividades: Iterable[Optional[float]]) -> Optional[float]:
    valores = [valor for valor in lista_promedios_actividades if valor is not None]
    if not valores:
        return None
    return redondear_2_decimales(sum(valores) / len(valores))


def calcular_cualitativo_trimestral(promedio_trimestral: Optional[float]) -> str:
    if promedio_trimestral is None or promedio_trimestral < 0.5:
        return ""
    return calcular_cualitativo(promedio_trimestral)


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


def calcular_valoracion_acompanamiento(
    total_siempre: int,
    total_frecuentemente: int,
    total_ocasionalmente: int,
    total_nunca: int,
) -> str:
    """Calcula valoración cualitativa para acompañamiento usando puntaje ponderado (1..36)."""
    puntaje_total = calcular_puntaje_ponderado_acompanamiento(
        total_siempre=total_siempre,
        total_frecuentemente=total_frecuentemente,
        total_ocasionalmente=total_ocasionalmente,
        total_nunca=total_nunca,
    )
    return calcular_valoracion_acompanamiento_desde_puntaje(puntaje_total)


def calcular_puntaje_ponderado_acompanamiento(
    total_siempre: int,
    total_frecuentemente: int,
    total_ocasionalmente: int,
    total_nunca: int,
) -> int:
    """Convierte conteos de respuestas en puntaje ponderado."""
    return (
        (int(total_siempre) * 4)
        + (int(total_frecuentemente) * 3)
        + (int(total_ocasionalmente) * 2)
        + (int(total_nunca) * 1)
    )


def calcular_valoracion_acompanamiento_desde_puntaje(puntaje_total: int) -> str:
    """Evalúa la escala cualitativa institucional con base en puntaje total ponderado."""
    if 35 <= puntaje_total <= 36:
        return "A+"
    if 33 <= puntaje_total <= 34:
        return "A-"
    if 30 <= puntaje_total <= 32:
        return "B+"
    if 27 <= puntaje_total <= 29:
        return "B-"
    if 20 <= puntaje_total <= 26:
        return "C+"
    if 18 <= puntaje_total <= 19:
        return "C-"
    if 15 <= puntaje_total <= 17:
        return "D+"
    if 13 <= puntaje_total <= 14:
        return "D-"
    if 11 <= puntaje_total <= 12:
        return "E+"
    if 9 <= puntaje_total <= 10:
        return "E-"
    return ""
