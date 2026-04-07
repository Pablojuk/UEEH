from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QPageLayout, QPageSize, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from config.estilos import ORIENTACION_A4
from data.datos_demo import cargar_datos_demo
from views.tabla_calificaciones import TablaCalificaciones


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
            painter = QPainter(printer)
            widget = self.scroll.widget()
            if widget:
                page = printer.pageRect(QPrinter.DevicePixel)
                scale_x = page.width() / widget.width()
                scale_y = page.height() / widget.height()
                scale = min(scale_x, scale_y)
                painter.translate(page.x(), page.y())
                painter.scale(scale, scale)
                widget.render(painter, QPoint(), QRectF(widget.rect()))
            painter.end()
