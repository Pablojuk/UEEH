import math
import os
from typing import Sequence

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gestion_academica.config.estilos import (
    A4_ALTO_PX,
    A4_ANCHO_PX,
    A4_MARGEN_EXTERNO,
    ANCHOS_COLUMNAS,
    COLOR_APROBADO,
    COLOR_BORDE,
    COLOR_FILA_IMPAR,
    COLOR_FILA_PAR,
    COLOR_HEADER_INSTITUCION,
    COLOR_HEADER_TABLA,
    COLOR_REPROBADO,
    COLOR_RESUMEN_TITULO,
    COLOR_SUBHEADER,
    COLOR_TEXTO_HEADER,
    COLOR_TEXTO_NORMAL,
    COLORES_GRAFICO,
    ESPACIO_BAJO_PROMEDIO,
    ESPACIO_FIRMAS,
    FIRMAS_DEFAULT,
    FUENTE_DATOS,
    FUENTE_FIRMA,
    FUENTE_FIRMA_CARGO,
    FUENTE_HEADER,
    FUENTE_RESUMEN,
    FUENTE_TITULO,
    LOGO_ALTO,
    LOGO_ANCHO,
    ORIENTACION_A4,
    RUTA_LOGO_INSTITUCION,
    RUTA_LOGO_MINEDUC,
    esc,
)


def crear_celda(
    texto: str,
    fuente: QFont | None = None,
    alineacion=Qt.AlignCenter,
    bg: QColor | None = None,
    fg: QColor | None = None,
    negrita: bool = False,
) -> QTableWidgetItem:
    item = QTableWidgetItem(str(texto))
    item.setTextAlignment(alineacion | Qt.AlignVCenter)
    if fuente:
        item.setFont(fuente)
    if negrita:
        fuente_item = item.font()
        fuente_item.setBold(True)
        item.setFont(fuente_item)
    if bg:
        item.setBackground(QBrush(bg))
    if fg:
        item.setForeground(QBrush(fg))
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    return item


class LogoLabel(QLabel):
    def __init__(self, ruta: str, texto_fallback: str, ancho: int = LOGO_ANCHO, alto: int = LOGO_ALTO, parent=None):
        super().__init__(parent)
        self.setFixedSize(ancho, alto)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: transparent; border: none;")
        pixmap = QPixmap(ruta) if ruta and os.path.exists(ruta) else QPixmap()
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(ancho - 8, alto - 8, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.setText(texto_fallback)
            self.setWordWrap(True)
            self.setStyleSheet(
                "background: rgba(255,255,255,0.12); color: white; border: 1px solid rgba(255,255,255,0.35);"
            )
            self.setFont(QFont("Calibri", max(7, int(round(7 * (ancho / 52)))), QFont.Bold))


class PieChartWidget(QWidget):
    def __init__(self, resumen: Sequence, parent=None):
        super().__init__(parent)
        self.resumen = list(resumen)
        self.setFixedWidth(esc(300))
        self.setFixedHeight(esc(170))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)
        painter.setPen(QPen(COLOR_BORDE, 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        total = sum(max(0, int(log.cantidad)) for log in self.resumen)
        if total <= 0:
            painter.drawText(self.rect(), Qt.AlignCenter, "Sin datos")
            return

        pie_rect = QRectF(esc(25), esc(15), esc(140), esc(110))
        start_angle = 0.0
        for i, log in enumerate(self.resumen):
            cantidad = max(0, int(log.cantidad))
            porcentaje = cantidad / total if total else 0
            span = 360.0 * porcentaje
            color = COLORES_GRAFICO[i % len(COLORES_GRAFICO)]
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawPie(pie_rect, int(start_angle * 16), int(span * 16))

            if porcentaje > 0:
                angle_mid = math.radians(start_angle + span / 2)
                cx = pie_rect.center().x() + math.cos(angle_mid) * esc(42)
                cy = pie_rect.center().y() - math.sin(angle_mid) * esc(42)
                painter.setPen(Qt.black)
                painter.setFont(QFont("Calibri", max(7, esc(10))))
                painter.drawText(
                    QRectF(cx - esc(18), cy - esc(10), esc(36), esc(20)),
                    Qt.AlignCenter,
                    f"{round(porcentaje * 100):.0f}%",
                )
            start_angle += span

        legend_x = esc(240)
        legend_y = esc(26)
        painter.setFont(QFont("Calibri", max(7, esc(9))))
        for i, _log in enumerate(self.resumen):
            color = COLORES_GRAFICO[i % len(COLORES_GRAFICO)]
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawRect(legend_x, legend_y + i * esc(28), esc(10), esc(10))
            painter.setPen(Qt.black)
            painter.drawText(legend_x + esc(18), legend_y + esc(10) + i * esc(28), str(i + 1))
        painter.end()


class SummaryTableWidget(QFrame):
    def __init__(self, resumen, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("background: white; border: 1px solid #000000;")
        self.setFixedSize(esc(410), esc(140))

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(0)

        widths = [esc(28), esc(290), esc(58), esc(44)]
        heights = [esc(24), esc(26), esc(26), esc(26), esc(26)]
        for i, width in enumerate(widths):
            layout.setColumnMinimumWidth(i, width)
        for i, height in enumerate(heights):
            layout.setRowMinimumHeight(i, height)

        header = self._make_cell(
            "Cuadro de logros en la evaluación de los aprendizajes",
            FUENTE_RESUMEN,
            Qt.AlignCenter,
            bold=True,
        )
        layout.addWidget(header, 0, 0, 1, 4)

        # Calcular total desde cantidades reales para que los % sean siempre correctos
        total = sum(max(0, int(log.cantidad)) for log in resumen)

        for i, log in enumerate(resumen, start=1):
            cantidad = max(0, int(log.cantidad))
            pct = cantidad / total if total > 0 else 0
            layout.addWidget(self._make_cell(str(i), FUENTE_DATOS), i, 0)
            layout.addWidget(self._make_cell(log.descripcion, FUENTE_DATOS, Qt.AlignLeft | Qt.AlignVCenter), i, 1)
            layout.addWidget(self._make_cell(str(cantidad), FUENTE_DATOS), i, 2)
            layout.addWidget(self._make_cell(self._formato_pct(pct), FUENTE_DATOS), i, 3)

    def _make_cell(self, text, font, alignment=Qt.AlignCenter, bold=False):
        label = QLabel(text)
        f = QFont(font)
        f.setBold(bold or font.bold())
        label.setFont(f)
        label.setAlignment(alignment)
        label.setStyleSheet("border-right: 1px solid #000000; border-bottom: 1px solid #000000; padding: 1px 4px;")
        return label

    @staticmethod
    def _formato_pct(valor: float) -> str:
        return f"{round(valor * 100):.0f}%"


class PromedioWidget(QFrame):
    def __init__(self, promedio: float, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("background: white; border: 1px solid #000000;")
        self.setFixedSize(esc(378), esc(28))

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(0)
        layout.setColumnMinimumWidth(0, esc(336))
        layout.setColumnMinimumWidth(1, esc(40))
        layout.setRowMinimumHeight(0, esc(28))

        etiqueta = QLabel("Promedio")
        etiqueta.setAlignment(Qt.AlignCenter)
        etiqueta.setFont(FUENTE_DATOS)
        etiqueta.setStyleSheet("border-right: 1px solid #000000; padding: 1px 4px;")

        valor = QLabel(f"{promedio:.2f}".replace(".", ","))
        valor.setAlignment(Qt.AlignCenter)
        fuente_valor = QFont(FUENTE_DATOS)
        fuente_valor.setBold(True)
        valor.setFont(fuente_valor)
        valor.setStyleSheet("padding: 1px 4px;")

        layout.addWidget(etiqueta, 0, 0)
        layout.addWidget(valor, 0, 1)


class FirmasWidget(QWidget):
    def __init__(self, firmas, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(esc(10), 0, esc(10), 0)
        layout.setSpacing(esc(16))

        for nombre, cargo in firmas:
            bloque = QWidget()
            bloque_layout = QVBoxLayout(bloque)
            bloque_layout.setContentsMargins(0, 0, 0, 0)
            bloque_layout.setSpacing(esc(3))

            linea = QFrame()
            linea.setFrameShape(QFrame.HLine)
            linea.setFrameShadow(QFrame.Plain)
            linea.setStyleSheet("color: #000000; background: #000000; min-height: 1px; max-height: 1px;")

            lbl_nombre = QLabel(nombre)
            lbl_nombre.setAlignment(Qt.AlignCenter)
            lbl_nombre.setFont(FUENTE_FIRMA)

            lbl_cargo = QLabel(cargo)
            lbl_cargo.setAlignment(Qt.AlignCenter)
            lbl_cargo.setFont(FUENTE_FIRMA_CARGO)

            bloque_layout.addWidget(linea)
            bloque_layout.addWidget(lbl_nombre)
            bloque_layout.addWidget(lbl_cargo)
            layout.addWidget(bloque, 1)


class TablaCalificaciones(QWidget):
    NUM_COLS = 11

    def __init__(self, meta, estudiantes, resumen, parent=None):
        super().__init__(parent)
        self.meta = meta
        self.estudiantes = estudiantes
        self.resumen = resumen
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: white;")
        self.setFixedWidth(A4_ANCHO_PX)
        self.setMinimumHeight(A4_ALTO_PX)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(A4_MARGEN_EXTERNO, A4_MARGEN_EXTERNO, A4_MARGEN_EXTERNO, A4_MARGEN_EXTERNO)
        layout.setSpacing(0)

        marco = QFrame()
        marco.setFixedWidth(A4_ANCHO_PX - (A4_MARGEN_EXTERNO * 2))
        marco.setMinimumHeight(A4_ALTO_PX - (A4_MARGEN_EXTERNO * 2))
        marco.setStyleSheet("QFrame { background: white; border: 2px solid #1E4DFF; }")

        marco_layout = QVBoxLayout(marco)
        marco_layout.setContentsMargins(0, 0, 0, esc(8))
        marco_layout.setSpacing(0)
        marco_layout.addWidget(self._crear_header_superior())
        marco_layout.addWidget(self._crear_tabla_principal())
        marco_layout.addWidget(self._crear_bloque_inferior())

        layout.addWidget(marco)

    def _crear_header_superior(self):
        wrapper = QWidget()
        wrapper.setStyleSheet("background: white;")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        fila_1 = QWidget()
        fila_1.setStyleSheet(f"background: {COLOR_HEADER_INSTITUCION.name()};")
        fila_1_layout = QHBoxLayout(fila_1)
        fila_1_layout.setContentsMargins(esc(12), esc(8), esc(12), esc(8))
        fila_1_layout.setSpacing(esc(8))

        logo_izq = LogoLabel(RUTA_LOGO_INSTITUCION, "LOGO")
        logo_der = LogoLabel(RUTA_LOGO_MINEDUC, "MINEDUC")

        titulo = QLabel(self.meta.institucion)
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setWordWrap(True)
        fuente_titulo = QFont("Calibri", 22, QFont.Bold)
        titulo.setFont(fuente_titulo)
        titulo.setStyleSheet("color: white; border: none;")

        fila_1_layout.addWidget(logo_izq, 0, Qt.AlignVCenter)
        fila_1_layout.addStretch(1)
        fila_1_layout.addWidget(titulo, 3)
        fila_1_layout.addStretch(1)
        fila_1_layout.addWidget(logo_der, 0, Qt.AlignVCenter)

        fila_2 = QLabel("")
        fila_2.setFixedHeight(esc(22))
        fila_2.setStyleSheet(f"background: {COLOR_HEADER_TABLA.name()};")

        fila_3 = QLabel("CUADRO DE CALIFICACIÓN")
        fila_3.setAlignment(Qt.AlignCenter)
        fila_3.setFixedHeight(esc(28))
        fila_3.setFont(FUENTE_HEADER)
        fila_3.setStyleSheet(
            f"background: {COLOR_HEADER_TABLA.name()}; color: white; font-weight: bold; border: none;"
        )

        meta_widget = QWidget()
        meta_widget.setStyleSheet(f"background: {COLOR_SUBHEADER.name()};")
        meta_layout = QGridLayout(meta_widget)
        meta_layout.setContentsMargins(esc(8), esc(4), esc(8), esc(4))
        meta_layout.setHorizontalSpacing(esc(12 if ORIENTACION_A4 == 'portrait' else 18))
        meta_layout.setVerticalSpacing(esc(2))

        etiquetas = [
            f"Docente: {self.meta.docente}",
            f"Asignatura: {self.meta.asignatura}",
            f"Paralelo: {self.meta.paralelo}",
            f"Trimestre: {self.meta.trimestre}",
            f"Tutor: {self.meta.tutor}",
        ]

        if ORIENTACION_A4 == "portrait":
            posiciones = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]
        else:
            posiciones = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]

        for texto, (fila, col) in zip(etiquetas, posiciones):
            lbl = QLabel(texto)
            lbl.setFont(FUENTE_DATOS)
            lbl.setStyleSheet("border: none; color: black;")
            meta_layout.addWidget(lbl, fila, col)

        layout.addWidget(fila_1)
        layout.addWidget(fila_2)
        layout.addWidget(fila_3)
        layout.addWidget(meta_widget)
        return wrapper

    def _crear_tabla_principal(self):
        n_est = len(self.estudiantes)
        total_rows = 2 + n_est
        self.tabla = QTableWidget(total_rows, self.NUM_COLS)
        t = self.tabla
        t.setShowGrid(True)
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionMode(QTableWidget.SingleSelection)
        t.setAlternatingRowColors(False)
        t.setStyleSheet(
            "QTableWidget { gridline-color: #B7B7B7; border: none; background: white; }"
            "QTableWidget::item { padding: 2px; }"
        )
        for i in range(total_rows):
            t.setRowHeight(i, esc(23))
        t.setRowHeight(0, esc(26))
        t.setRowHeight(1, esc(23))
        for col, ancho in ANCHOS_COLUMNAS.items():
            t.setColumnWidth(col, ancho)
        self._llenar_encabezado_tabla()
        self._llenar_datos_estudiantes()

        # Ajustar alto de la tabla al contenido real para evitar scrollbar interno
        total_height = t.rowHeight(0) + t.rowHeight(1) + n_est * esc(23) + 2
        t.setFixedHeight(total_height)
        t.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        t.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        return t

    def _llenar_encabezado_tabla(self):
        t = self.tabla
        row_h1 = 0
        row_h2 = 1
        headers = [
            (0, "N°", 1, 2),
            (1, "Nómina", 1, 2),
            (2, "Aportes", 2, 1),
            (4, "Proy. Inter.", 2, 1),
            (6, "Examen", 2, 1),
            (8, "Promedio\nfinal", 1, 2),
            (9, "Cualitativa", 1, 2),
            (10, "Observación", 1, 2),
        ]
        for col, texto, colspan, rowspan in headers:
            if rowspan == 2:
                t.setSpan(row_h1, col, 2, colspan)
            else:
                t.setSpan(row_h1, col, 1, colspan)
            t.setItem(
                row_h1,
                col,
                crear_celda(
                    texto,
                    fuente=FUENTE_HEADER,
                    bg=COLOR_HEADER_TABLA,
                    fg=COLOR_TEXTO_HEADER,
                    negrita=True,
                ),
            )

        sub_headers = [
            (2, "Calificación"),
            (3, "70%"),
            (4, "Calificación"),
            (5, "15%"),
            (6, "Calificación"),
            (7, "15%"),
        ]
        for col, texto in sub_headers:
            t.setItem(
                row_h2,
                col,
                crear_celda(texto, fuente=FUENTE_DATOS, bg=COLOR_SUBHEADER, fg=COLOR_TEXTO_NORMAL),
            )

    def _llenar_datos_estudiantes(self):
        t = self.tabla
        row_inicio = 2
        for i, est in enumerate(self.estudiantes):
            row = row_inicio + i
            bg = COLOR_FILA_PAR if i % 2 == 0 else COLOR_FILA_IMPAR
            t.setItem(row, 0, crear_celda(str(est.numero), fuente=FUENTE_DATOS, bg=bg))
            t.setItem(row, 1, crear_celda(est.nombre, fuente=FUENTE_DATOS, bg=bg, alineacion=Qt.AlignLeft))
            t.setItem(row, 2, crear_celda(f"{est.cal_aportes:.2f}", fuente=FUENTE_DATOS, bg=bg))
            t.setItem(row, 3, crear_celda(f"{est.pond_aportes:.2f}", fuente=FUENTE_DATOS, bg=bg))
            t.setItem(row, 4, crear_celda(f"{est.cal_proyecto:.2f}", fuente=FUENTE_DATOS, bg=bg))
            t.setItem(row, 5, crear_celda(f"{est.pond_proyecto:.2f}", fuente=FUENTE_DATOS, bg=bg))
            t.setItem(row, 6, crear_celda(f"{est.cal_examen:.2f}", fuente=FUENTE_DATOS, bg=bg))
            t.setItem(row, 7, crear_celda(f"{est.pond_examen:.2f}", fuente=FUENTE_DATOS, bg=bg))
            t.setItem(row, 8, crear_celda(f"{est.promedio_final:.2f}", fuente=FUENTE_DATOS, bg=bg, negrita=True))
            t.setItem(row, 9, crear_celda(est.cualitativa, fuente=FUENTE_DATOS, bg=bg))
            obs_bg = COLOR_APROBADO if est.observacion == "Aprobado" else COLOR_REPROBADO
            t.setItem(row, 10, crear_celda(est.observacion, fuente=FUENTE_DATOS, bg=obs_bg))

    def _crear_bloque_inferior(self):
        bloque = QWidget()
        bloque.setStyleSheet("background: white; border: none;")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        titulo = QLabel("")
        titulo.setFont(FUENTE_RESUMEN)
        titulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        titulo.setFixedHeight(esc(24))
        titulo.setStyleSheet(
            f"background: {COLOR_RESUMEN_TITULO.name()}; color: black; padding-left: 4px; border: 1px solid #B7B7B7; border-top: none;"
        )
        layout.addWidget(titulo)

        fila_superior = QHBoxLayout()
        fila_superior.setContentsMargins(esc(24), esc(10), esc(24), 0)
        fila_superior.setSpacing(esc(28))
        fila_superior.addWidget(SummaryTableWidget(self.resumen), 3)
        fila_superior.addWidget(PieChartWidget(self.resumen), 2)
        layout.addLayout(fila_superior)

        promedio_wrapper = QWidget()
        promedio_layout = QHBoxLayout(promedio_wrapper)
        promedio_layout.setContentsMargins(0, esc(18), 0, 0)
        promedio_layout.setSpacing(0)
        promedio_layout.addStretch(1)
        promedio_layout.addWidget(PromedioWidget(self._promedio_general()))
        promedio_layout.addStretch(1)
        layout.addWidget(promedio_wrapper)

        layout.addSpacing(ESPACIO_BAJO_PROMEDIO)
        layout.addSpacing(ESPACIO_FIRMAS)
        layout.addWidget(FirmasWidget(FIRMAS_DEFAULT))
        layout.addStretch(1)
        layout.addSpacing(esc(8))
        return bloque

    def _promedio_general(self) -> float:
        if not self.estudiantes:
            return 0.0
        return sum(float(est.promedio_final) for est in self.estudiantes) / len(self.estudiantes)
