"""Modelos de dominio para el sistema académico (BLOQUE 1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class ConfiguracionSistema:
    clave_inicial_hash: str
    primer_uso_completado: bool
    escala_maxima: float = 10.0
    escala_minima: float = 0.0


@dataclass(frozen=True)
class Institucion:
    id_institucion: str
    nombre: str
    jornada: str


@dataclass(frozen=True)
class Docente:
    id_docente: str
    nombres: str
    apellidos: str
    identificacion: str


@dataclass(frozen=True)
class Curso:
    id_curso: str
    nombre: str
    nivel: str


@dataclass(frozen=True)
class Paralelo:
    id_paralelo: str
    nombre: str


@dataclass(frozen=True)
class Asignatura:
    id_asignatura: str
    nombre: str
    codigo: Optional[str] = None


@dataclass(frozen=True)
class PeriodoLectivo:
    id_periodo: str
    anio_inicio: int
    anio_fin: int
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


@dataclass(frozen=True)
class Estudiante:
    id_estudiante: str
    codigo: str
    apellidos: str
    nombres: str
    identificacion: Optional[str] = None


@dataclass(frozen=True)
class Matricula:
    id_matricula: str
    estudiante_id: str
    curso_id: str
    paralelo_id: str
    periodo_id: str
    numero_lista: Optional[int] = None


@dataclass(frozen=True)
class AsignacionDocente:
    id_asignacion: str
    docente_id: str
    asignatura_id: str
    curso_id: str
    paralelo_id: str
    periodo_id: str


@dataclass(frozen=True)
class Trimestre:
    id_trimestre: str
    numero: int
    nombre: str
    periodo_id: str


@dataclass(frozen=True)
class RegistroActividad:
    id_registro: str
    estudiante_id: str
    asignacion_id: str
    trimestre_id: str
    actividad_nombre: str
    nota_base: float
    nota_mejora: Optional[float] = None


@dataclass(frozen=True)
class RegistroSumativo:
    id_registro: str
    estudiante_id: str
    asignacion_id: str
    trimestre_id: str
    evaluacion_nombre: str
    nota_base: float
    nota_mejora: Optional[float] = None


@dataclass(frozen=True)
class ResumenTrimestral:
    id_resumen: str
    estudiante_id: str
    asignacion_id: str
    trimestre_id: str
    promedio_formativo: float
    promedio_sumativo: float
    nota_trimestral: float


@dataclass(frozen=True)
class ResumenFinal:
    id_resumen_final: str
    estudiante_id: str
    asignacion_id: str
    promedio_anual: float
    cualitativo: str
    observacion: str


@dataclass(frozen=True)
class Supletorio:
    id_supletorio: str
    estudiante_id: str
    asignacion_id: str
    nota_supletorio: float
    nota_final_previa: float
    nota_final_definitiva: float
    aprobado: bool
