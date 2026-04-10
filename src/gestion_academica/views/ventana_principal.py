import math

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPageLayout, QPageSize, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gestion_academica.config.estilos import ORIENTACION_A4
from gestion_academica.data.datos_demo import cargar_datos_demo
from gestion_academica.views.tabla_calificaciones import TablaCalificaciones


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte de Calificaciones")
        self.setMinimumSize(980, 920)
        self._setup_ui()
        self.cargar_demo()

    def _setup_ui(self):
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout = QVBoxLayout(widget_central)

        toolbar = QHBoxLayout()
        btn_recargar = QPushButton("Recargar demo")
        btn_recargar.clicked.connect(self.cargar_demo)
        btn_imprimir = QPushButton("Imprimir")
        btn_imprimir.clicked.connect(self._imprimir)
        toolbar.addWidget(btn_recargar)
        toolbar.addWidget(btn_imprimir)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.scroll.setStyleSheet("QScrollArea { background: #d9d9d9; }")
        layout.addWidget(self.scroll)

        orientacion_texto = "A4 vertical" if ORIENTACION_A4 == "portrait" else "A4 horizontal"
        self.statusBar().showMessage(f"Listo — {orientacion_texto}")

    def cargar_demo(self):
        meta, estudiantes, resumen = cargar_datos_demo()
        self.scroll.setWidget(TablaCalificaciones(meta, estudiantes, resumen))
        orientacion_texto = "A4 vertical" if ORIENTACION_A4 == "portrait" else "A4 horizontal"
        self.statusBar().showMessage(f"Cargado demo — {len(estudiantes)} estudiantes — {orientacion_texto}")

    def _imprimir(self):
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter

        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Portrait if ORIENTACION_A4 == "portrait" else QPageLayout.Landscape)
        printer.setFullPage(False)

        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            widget = self.scroll.widget()
            if not widget:
                return

            painter = QPainter(printer)
            page_rect = printer.pageRect(QPrinter.DevicePixel)

            # Escala basada solo en el ancho para mantener el tamaño de texto correcto
            scale = page_rect.width() / widget.width()

            # Cuántos píxeles de pantalla caben en una página impresa
            pixels_por_pagina = page_rect.height() / scale

            widget_total_height = widget.height()
            y_offset = 0.0
            primera_pagina = True

            while y_offset < widget_total_height:
                if not primera_pagina:
                    printer.newPage()
                primera_pagina = False

                painter.save()
                painter.translate(page_rect.x(), page_rect.y())
                painter.scale(scale, scale)
                painter.translate(0, -y_offset)

                # Clip para que solo se vea la sección de esta página
                clip = QRectF(0, y_offset, widget.width(), pixels_por_pagina)
                painter.setClipRect(clip)
                widget.render(painter)

                painter.restore()
                y_offset += pixels_por_pagina

            painter.end()
            pages = math.ceil(widget_total_height / pixels_por_pagina)
            self.statusBar().showMessage(f"Impreso — {pages} página(s)")
