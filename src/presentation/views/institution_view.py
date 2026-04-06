"""Vista funcional de institución."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
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
from src.presentation.app_signals import AppSignals


class InstitutionView(QWidget):
    def __init__(self, institution_service: InstitutionService, app_signals: AppSignals | None = None) -> None:
        super().__init__()
        self.institution_service = institution_service
        self.app_signals = app_signals

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
        self.province_input = QLineEdit()
        self.city_input = QLineEdit()
        self.parish_input = QLineEdit()
        self.address_input = QLineEdit()
        self.amie_input = QLineEdit()
        self.rector_input = QLineEdit()
        self.vicerrector_input = QLineEdit()
        self.inspector_input = QLineEdit()

        self.logo_ministry_path_input = QLineEdit()
        self.logo_ministry_path_input.setReadOnly(True)
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setReadOnly(True)

        self.logo_ministry_button = QPushButton("Seleccionar logo ministerio")
        self.logo_ministry_button.clicked.connect(self._select_logo_ministry)
        self.logo_button = QPushButton("Seleccionar logo institucional")
        self.logo_button.clicked.connect(self._select_logo_institution)

        logo_ministry_row = QHBoxLayout()
        logo_ministry_row.addWidget(self.logo_ministry_path_input, 1)
        logo_ministry_row.addWidget(self.logo_ministry_button)

        logo_row = QHBoxLayout()
        logo_row.addWidget(self.logo_path_input, 1)
        logo_row.addWidget(self.logo_button)

        form.addRow("Nombre", self.name_input)
        form.addRow("Jornada", self.shift_input)
        form.addRow("Provincia", self.province_input)
        form.addRow("Ciudad", self.city_input)
        form.addRow("Parroquia", self.parish_input)
        form.addRow("Dirección", self.address_input)
        form.addRow("Código AMIE", self.amie_input)
        form.addRow("Rector(a)", self.rector_input)
        form.addRow("Vicerrector(a)", self.vicerrector_input)
        form.addRow("Inspector(a)", self.inspector_input)
        form.addRow("Logo Ministerio", logo_ministry_row)
        form.addRow("Logo Institucional", logo_row)

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
        data = self.institution_service.obtener_actual() or {}
        self.name_input.setText(data.get("nombre", ""))
        self.shift_input.setText(data.get("jornada", ""))
        self.province_input.setText(data.get("provincia") or "")
        self.city_input.setText(data.get("ciudad") or "")
        self.parish_input.setText(data.get("parroquia") or "")
        self.address_input.setText(data.get("direccion") or "")
        self.amie_input.setText(data.get("codigo_amie") or "")
        self.rector_input.setText(data.get("rector") or "")
        self.vicerrector_input.setText(data.get("vicerrector") or "")
        self.inspector_input.setText(data.get("inspector") or "")
        self.logo_ministry_path_input.setText(data.get("logo_ministerio_path") or "")
        self.logo_path_input.setText(data.get("logo_path") or "")

    def _select_logo_ministry(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar logo del ministerio",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp)",
        )
        if path:
            self.logo_ministry_path_input.setText(path)

    def _select_logo_institution(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar logo institucional",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp)",
        )
        if path:
            self.logo_path_input.setText(path)

    def _on_save(self) -> None:
        name = self.name_input.text().strip()
        shift = self.shift_input.text().strip() or "Por definir"

        if not name:
            QMessageBox.warning(self, "Validación", "El nombre de la institución es obligatorio.")
            return

        self.institution_service.crear_o_actualizar(
            nombre=name,
            jornada=shift,
            provincia=self.province_input.text().strip() or None,
            ciudad=self.city_input.text().strip() or None,
            parroquia=self.parish_input.text().strip() or None,
            direccion=self.address_input.text().strip() or None,
            codigo_amie=self.amie_input.text().strip() or None,
            rector=self.rector_input.text().strip() or None,
            vicerrector=self.vicerrector_input.text().strip() or None,
            inspector=self.inspector_input.text().strip() or None,
            logo_ministerio_path=self.logo_ministry_path_input.text().strip() or None,
            logo_path=self.logo_path_input.text().strip() or None,
        )
        QMessageBox.information(self, "Éxito", "Datos institucionales guardados correctamente.")
        if self.app_signals:
            self.app_signals.data_changed.emit("institution")

    def refresh_data(self) -> None:
        self.load_data()
