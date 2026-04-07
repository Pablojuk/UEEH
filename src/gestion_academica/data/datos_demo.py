from dataclasses import dataclass
from typing import Optional


@dataclass
class EstudianteCalificacion:
    numero: int
    nombre: str
    cal_aportes: float
    pond_aportes: float
    cal_proyecto: float
    pond_proyecto: float
    cal_examen: float
    pond_examen: float
    promedio: float
    cualitativa: str
    supletorio: Optional[float]
    promedio_final: float
    observacion: str


@dataclass
class MetadatosReporte:
    institucion: str = ""
    docente: str = ""
    asignatura: str = ""
    paralelo: str = ""
    trimestre: str = ""
    curso: str = ""
    tutor: str = ""


@dataclass
class ResumenLogros:
    categoria: str
    descripcion: str
    cantidad: int
    porcentaje: float


def _cualitativa(promedio: float) -> str:
    if promedio >= 9:
        return "DA"
    if promedio >= 7:
        return "AA"
    if promedio >= 5:
        return "PA"
    return "NA"


def _observacion(promedio_final: float) -> str:
    return "Aprobado" if promedio_final >= 7 else "No aprobado"


def cargar_datos_demo():
    meta = MetadatosReporte(
        institucion="Unidad Educativa Emiliano Hinoztroza",
        docente="Econ. Pablo Hernan Juca Farfan",
        asignatura="ECA",
        paralelo="A",
        trimestre="Tercero",
        curso="10mo EGB",
        tutor="Lcdo. José Sumba",
    )

    base_estudiantes = [
        (1, "GUAILLAZACA LALVAY KARELI SOFIA", 10.00, 7.00, 9.71, 1.46, 10.00, 1.50),
        (2, "GUAYLLASACA NIEVES ALAN ROMEO", 10.00, 7.00, 10.00, 1.50, 10.00, 1.50),
        (3, "MEJIA SINCHE ARIEL RAMIRO", 8.00, 5.60, 9.71, 1.46, 10.00, 1.50),
        (4, "MERCHAN PIZARRO MONICA MARIBEL", 7.00, 4.90, 9.71, 1.46, 10.00, 1.50),
        (5, "PINEDA SARMIENTO DEXSI ESTEFANIA", 8.75, 6.12, 9.00, 1.35, 10.00, 1.50),
        (6, "PUCHA GUAYLLASACA NIKSON FERNANDO", 10.00, 7.00, 10.00, 1.50, 10.00, 1.50),
        (7, "SACA SACASARI DANI ALEXANDER", 8.00, 5.60, 9.00, 1.35, 10.00, 1.50),
        (8, "SANCHEZ RAMON NATHALY ELIZABETH", 8.00, 5.60, 9.00, 1.35, 10.00, 1.50),
        (9, "SEGOVIA CHAVEZ HENRY DANIEL", 8.50, 5.95, 10.00, 1.50, 10.00, 1.50),
    ]

    estudiantes = []
    for numero, nombre, cal_ap, pond_ap, cal_pr, pond_pr, cal_ex, pond_ex in base_estudiantes:
        promedio = round(pond_ap + pond_pr + pond_ex, 2)
        cualitativa = _cualitativa(promedio)
        promedio_final = promedio
        observacion = _observacion(promedio_final)

        estudiantes.append(
            EstudianteCalificacion(
                numero=numero,
                nombre=nombre,
                cal_aportes=cal_ap,
                pond_aportes=pond_ap,
                cal_proyecto=cal_pr,
                pond_proyecto=pond_pr,
                cal_examen=cal_ex,
                pond_examen=pond_ex,
                promedio=promedio,
                cualitativa=cualitativa,
                supletorio=None,
                promedio_final=promedio_final,
                observacion=observacion,
            )
        )

    total = len(estudiantes) or 1
    da = sum(1 for e in estudiantes if e.cualitativa == "DA")
    aa = sum(1 for e in estudiantes if e.cualitativa == "AA")
    pa = sum(1 for e in estudiantes if e.cualitativa == "PA")
    na = sum(1 for e in estudiantes if e.cualitativa == "NA")

    resumen = [
        ResumenLogros("DA", "Domina los aprendizajes (DA) 9 - 10", da, da / total),
        ResumenLogros("AA", "Alcanza los aprendizajes (AA) 7 - 8,99", aa, aa / total),
        ResumenLogros("PA", "Próximo a alcanzar (PA) 5 - 6,99", pa, pa / total),
        ResumenLogros("NA", "No alcanza los aprendizajes (NA) <=5", na, na / total),
    ]

    return meta, estudiantes, resumen
