"""Vista de inicio con métricas y accesos rápidos."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class DashboardView(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, counters_provider) -> None:
        super().__init__()
        self.counters_provider = counters_provider
        self.metric_labels: dict[str, QLabel] = {}

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Inicio")
        title.setObjectName("Title")
        subtitle = QLabel("Resumen general del sistema académico")
        subtitle.setObjectName("Subtitle")

        metrics_card = QFrame()
        metrics_card.setObjectName("Card")
        metrics_grid = QGridLayout(metrics_card)
        metrics_grid.setContentsMargins(12, 12, 12, 12)

        definitions = [
            ("students", "Estudiantes"),
            ("teachers", "Docentes"),
            ("courses", "Cursos"),
            ("assignments", "Asignaciones"),
            ("enrollments", "Matrículas"),
        ]
        for idx, (key, label) in enumerate(definitions):
            box = QFrame()
            box.setObjectName("Card")
            box_layout = QVBoxLayout(box)
            box_layout.addWidget(QLabel(label))
            value_label = QLabel("0")
            value_label.setStyleSheet("font-size: 22px; font-weight: 600;")
            box_layout.addWidget(value_label)
            self.metric_labels[key] = value_label
            metrics_grid.addWidget(box, idx // 3, idx % 3)

        shortcuts_card = QFrame()
        shortcuts_card.setObjectName("Card")
        shortcuts_layout = QHBoxLayout(shortcuts_card)
        for key, text in [
            ("students", "Ir a Estudiantes"),
            ("teachers", "Ir a Docentes"),
            ("enrollments", "Ir a Matrículas"),
            ("grades", "Ir a Notas"),
        ]:
            button = QPushButton(text)
            button.clicked.connect(lambda _=False, section=key: self.navigate_requested.emit(section))
            shortcuts_layout.addWidget(button)

        institutional_text = QFrame()
        institutional_text.setObjectName("Card")
        text_layout = QVBoxLayout(institutional_text)
        paragraph = QLabel(
            "Bienvenido al panel académico. Aquí puede monitorear el estado general del sistema y acceder "
            "rápidamente a los módulos más utilizados para mantener registros actualizados."
        )
        paragraph.setWordWrap(True)
        text_layout.addWidget(paragraph)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(metrics_card)
        layout.addWidget(shortcuts_card)
        layout.addWidget(institutional_text)
        layout.addStretch(1)

        self.refresh_data()

    def refresh_data(self) -> None:
        counters = self.counters_provider()
        self.metric_labels["students"].setText(str(counters.get("students", 0)))
        self.metric_labels["teachers"].setText(str(counters.get("teachers", 0)))
        self.metric_labels["courses"].setText(str(counters.get("courses", 0)))
        self.metric_labels["assignments"].setText(str(counters.get("assignments", 0)))
        self.metric_labels["enrollments"].setText(str(counters.get("enrollments", 0)))
