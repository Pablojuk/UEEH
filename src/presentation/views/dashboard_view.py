"""Vista de inicio con ficha institucional formal."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.application.services.institution_service import InstitutionService


class DashboardView(QWidget):
    def __init__(self, institution_service: InstitutionService) -> None:
        super().__init__()
        self.institution_service = institution_service
        self.value_labels: dict[str, QLabel] = {}

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        card = QFrame()
        card.setObjectName("Card")
        grid = QGridLayout(card)
        grid.setSpacing(2)

        header = QLabel("DATOS DE LA INSTITUCIÓN")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            "background-color: #facc15; border: 1px solid #111827; font-weight: 700; padding: 8px;"
        )
        grid.addWidget(header, 0, 0, 1, 6)

        row = 1
        row = self._add_field_row(grid, row, "Nombre de la institución", "nombre", span=5)

        self._add_label_cell(grid, row, 0, "Provincia")
        self._add_value_cell(grid, row, 1, "provincia")
        self._add_label_cell(grid, row, 2, "Ciudad")
        self._add_value_cell(grid, row, 3, "ciudad")
        self._add_label_cell(grid, row, 4, "Parroquia")
        self._add_value_cell(grid, row, 5, "parroquia")
        row += 1

        row = self._add_field_row(grid, row, "Dirección", "direccion", span=5)
        row = self._add_field_row(grid, row, "Código AMIE", "codigo_amie", span=5)
        row = self._add_field_row(grid, row, "Rector(a)", "rector", span=5)
        row = self._add_field_row(grid, row, "Vicerrector(a)", "vicerrector", span=5)
        self._add_field_row(grid, row, "Inspector(a)", "inspector", span=5)

        root.addWidget(card)
        root.addLayout(self._build_logo_panel())
        root.addStretch(1)
        root.addLayout(self._build_logo_panel())

        self.refresh_data()

    def _build_logo_panel(self) -> QHBoxLayout:
        panel = QHBoxLayout()
        panel.setSpacing(24)
        panel.setContentsMargins(0, 14, 0, 0)

        self.logo_ministerio_label = QLabel("Logo ministerial")
        self.logo_ministerio_label.setAlignment(Qt.AlignCenter)
        self.logo_ministerio_label.setFixedSize(320, 120)
        self.logo_ministerio_label.setStyleSheet("border: 1px dashed #cbd5e1; color: #94a3b8; border-radius: 8px;")

        self.logo_label = QLabel("Logo institucional")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(320, 120)
        self.logo_label.setStyleSheet("border: 1px dashed #cbd5e1; color: #94a3b8; border-radius: 8px;")

        ministerio_title = QLabel("MINISTERIO DE EDUCACIÓN, DEPORTE Y CULTURA")
        ministerio_title.setAlignment(Qt.AlignCenter)
        ministerio_title.setStyleSheet("font-weight: 700; color: #0f172a;")
        ministerio_box = QVBoxLayout()
        ministerio_box.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        ministerio_box.addWidget(ministerio_title)
        ministerio_box.addWidget(self.logo_ministerio_label)

        institucional_title = QLabel("LOGO INSTITUCIONAL")
        institucional_title.setAlignment(Qt.AlignCenter)
        institucional_title.setStyleSheet("font-weight: 700; color: #0f172a;")
        institucional_box = QVBoxLayout()
        institucional_box.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        institucional_box.addWidget(institucional_title)
        institucional_box.addWidget(self.logo_label)

        panel.addStretch(1)
        panel.addLayout(ministerio_box, 1)
        panel.addLayout(institucional_box, 1)
        panel.addStretch(1)
        return panel

    def _add_field_row(self, grid: QGridLayout, row: int, label: str, key: str, span: int = 1) -> int:
        self._add_label_cell(grid, row, 0, label)
        self._add_value_cell(grid, row, 1, key, span=span)
        return row + 1

    def _add_label_cell(self, grid: QGridLayout, row: int, col: int, text: str) -> None:
        label = QLabel(text)
        label.setStyleSheet("background-color: #fde68a; border: 1px solid #111827; padding: 6px; font-weight: 600;")
        grid.addWidget(label, row, col)

    def _add_value_cell(self, grid: QGridLayout, row: int, col: int, key: str, span: int = 1) -> None:
        value = QLabel("No registrado")
        value.setStyleSheet("background-color: #f8fafc; border: 1px solid #111827; padding: 6px;")
        self.value_labels[key] = value
        grid.addWidget(value, row, col, 1, span)

    def refresh_data(self) -> None:
        institution = self.institution_service.obtener_actual() or {}
        for key, label in self.value_labels.items():
            value = institution.get(key)
            label.setText(str(value).strip() if value else "No registrado")
        self._hide_duplicate_logo_placeholders()

    def _hide_duplicate_logo_placeholders(self) -> None:
        """Oculta placeholders de logo repetidos si quedaron en layouts antiguos."""
        duplicate_texts = {"Logo ministerial", "Logo institucional"}
        for label in self.findChildren(QLabel):
            if label.text().strip() in duplicate_texts:
                label.hide()
