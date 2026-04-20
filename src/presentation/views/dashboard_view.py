"""Vista de inicio con ficha institucional formal."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

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
        root.addStretch(1)

        self.refresh_data()

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
