"""Vista funcional de institución."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.application.services.institution_service import InstitutionService


class InstitutionView(QWidget):
    def __init__(self, institution_service: InstitutionService) -> None:
        super().__init__()
        self.institution_service = institution_service

        root = QVBoxLayout(self)

        title = QLabel("Institución")
        title.setObjectName("Title")
        subtitle = QLabel("Configurar y actualizar datos institucionales")
        subtitle.setObjectName("Subtitle")

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)

        self.name_input = QLineEdit()
        self.shift_input = QLineEdit()

        form.addRow("Nombre", self.name_input)
        form.addRow("Jornada", self.shift_input)

        actions = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self._on_save)
        actions.addWidget(self.save_button)
        actions.addStretch(1)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(card)
        root.addLayout(actions)
        root.addStretch(1)

        self.load_data()

    def load_data(self) -> None:
        data = self.institution_service.obtener_actual()
        if not data:
            self.name_input.clear()
            self.shift_input.clear()
            return

        self.name_input.setText(data.get("nombre", ""))
        self.shift_input.setText(data.get("jornada", ""))

    def _on_save(self) -> None:
        name = self.name_input.text().strip()
        shift = self.shift_input.text().strip() or "Por definir"

        if not name:
            QMessageBox.warning(self, "Validación", "El nombre de la institución es obligatorio.")
            return

        self.institution_service.crear_o_actualizar(nombre=name, jornada=shift)
        QMessageBox.information(self, "Éxito", "Datos institucionales guardados correctamente.")
