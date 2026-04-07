from PySide6.QtGui import QColor, QFont

ORIENTACION_A4 = "portrait"

A4_ANCHO_LANDSCAPE = 1123
A4_ALTO_LANDSCAPE = 794
A4_ANCHO_PORTRAIT = 794
A4_ALTO_PORTRAIT = 1123

if ORIENTACION_A4 == "portrait":
    A4_ANCHO_PX = A4_ANCHO_PORTRAIT
    A4_ALTO_PX = A4_ALTO_PORTRAIT
    ESCALA_UI = 0.72
else:
    A4_ANCHO_PX = A4_ANCHO_LANDSCAPE
    A4_ALTO_PX = A4_ALTO_LANDSCAPE
    ESCALA_UI = 1.0


def esc(valor: int) -> int:
    return max(1, int(round(valor * ESCALA_UI)))


A4_MARGEN_EXTERNO = esc(8)

RUTA_LOGO_INSTITUCION = r"C:\Users\ASUS\OneDrive\Escritorio\-preview.png"
RUTA_LOGO_MINEDUC = r"C:\Users\ASUS\OneDrive\Escritorio\MINEDEC.png"
LOGO_ANCHO = 130
LOGO_ALTO = 130

COLOR_HEADER_INSTITUCION = QColor("#1F4E79")
COLOR_HEADER_TABLA = QColor("#2E75B6")
COLOR_SUBHEADER = QColor("#9DC3E6")
COLOR_FILA_PAR = QColor("#FFFFFF")
COLOR_FILA_IMPAR = QColor("#F7FAFD")
COLOR_RESUMEN_TITULO = QColor("#E9DDB8")
COLOR_TEXTO_HEADER = QColor("#FFFFFF")
COLOR_TEXTO_NORMAL = QColor("#000000")
COLOR_APROBADO = QColor("#E2EFDA")
COLOR_REPROBADO = QColor("#FCE4D6")
COLOR_BORDE = QColor("#B7B7B7")
COLOR_FONDO_PAGINA = QColor("#FFFFFF")

COLORES_GRAFICO = [
    QColor("#4472C4"),
    QColor("#ED7D31"),
    QColor("#A5A5A5"),
    QColor("#FFC000"),
]

FUENTE_TITULO = QFont("Calibri", max(9, int(round(12 * ESCALA_UI))), QFont.Bold)
FUENTE_HEADER = QFont("Calibri", max(8, int(round(9 * ESCALA_UI))), QFont.Bold)
FUENTE_DATOS = QFont("Calibri", max(7, int(round(9 * ESCALA_UI))))
FUENTE_RESUMEN = QFont("Calibri", max(7, int(round(8 * ESCALA_UI))), QFont.Bold)
FUENTE_FIRMA = QFont("Calibri", max(9, int(round(10 * ESCALA_UI))))
FUENTE_FIRMA_CARGO = QFont("Calibri", max(9, int(round(10 * ESCALA_UI))))

ANCHOS_COLUMNAS = {
    0: esc(38),
    1: esc(285),
    2: esc(78),
    3: esc(52),
    4: esc(78),
    5: esc(52),
    6: esc(78),
    7: esc(52),
    8: esc(72),
    9: esc(70),
    10: esc(82),
    11: esc(110),
}

ESPACIO_FIRMAS = esc(82)
ESPACIO_BAJO_PROMEDIO = esc(16)

FIRMAS_DEFAULT = [
    ("Econ. Pablo Juca", "Docente"),
    ("Lcdo. Nelson Bermeo", "Coordinador de Área"),
    ("Econ. Pablo Juca", "Rector"),
    ("Lcdo. José Sumba", "Tutor de Curso"),
]
