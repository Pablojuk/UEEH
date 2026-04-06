"""Vista funcional de gestión de docentes."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.application.services.teacher_service import TeacherService
from src.presentation.app_signals import AppSignals


class TeachersView(QWidget):
    def __init__(self, teacher_service: TeacherService, app_signals: AppSignals | None = None) -> None:
        super().__init__()
        self.teacher_service = teacher_service
        self.app_signals = app_signals
        self.editing_teacher_id: str | None = None

        root = QVBoxLayout(self)

        title = QLabel("Docentes")
        title.setObjectName("Title")
        subtitle = QLabel("Registro, edición y activación/inactivación")
        subtitle.setObjectName("Subtitle")

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o identificación")
        self.search_input.textChanged.connect(self.load_teachers)
        search_row.addWidget(self.search_input)

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)
        self.id_input = QLineEdit()
        self.names_input = QLineEdit()
        self.lastnames_input = QLineEdit()
        self.identification_input = QLineEdit()
        self.title_input = QLineEdit()

        form.addRow("ID docente", self.id_input)
        form.addRow("Nombres", self.names_input)
        form.addRow("Apellidos", self.lastnames_input)
        form.addRow("Identificación", self.identification_input)
        form.addRow("Título", self.title_input)

        actions = QHBoxLayout()
        self.new_button = QPushButton("Nuevo")
        self.new_button.clicked.connect(self.reset_form)
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_teacher)
        self.toggle_button = QPushButton("Activar/Inactivar")
        self.toggle_button.clicked.connect(self.toggle_teacher_status)
        self.delete_button = QPushButton("Borrar Docente")
        self.delete_button.clicked.connect(self.delete_teacher)
        self.import_button = QPushButton("Importar Excel/CSV")
        self.import_button.clicked.connect(self.import_teachers)

        actions.addWidget(self.new_button)
        actions.addWidget(self.save_button)
        actions.addWidget(self.toggle_button)
        actions.addWidget(self.delete_button)
        actions.addWidget(self.import_button)
        actions.addStretch(1)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Nombres", "Apellidos", "Identificación", "Título", "Estado"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellClicked.connect(self.select_teacher_from_table)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(search_row)
        root.addWidget(card)
        root.addLayout(actions)
        root.addWidget(self.table, 1)

        self.load_teachers()

    def reset_form(self) -> None:
        self.editing_teacher_id = None
        self.id_input.setEnabled(True)
        self.id_input.clear()
        self.names_input.clear()
        self.lastnames_input.clear()
        self.identification_input.clear()
        self.title_input.clear()
        self.table.clearSelection()

    def save_teacher(self) -> None:
        payload = {
            "id_docente": self.id_input.text().strip(),
            "nombres": self.names_input.text().strip(),
            "apellidos": self.lastnames_input.text().strip(),
            "identificacion": self.identification_input.text().strip(),
            "titulo": self.title_input.text().strip() or "No registrado",
        }

        if not all(payload.values()):
            QMessageBox.warning(self, "Validación", "Complete todos los campos del docente.")
            return

        try:
            if self.editing_teacher_id:
                self.teacher_service.actualizar_docente(
                    self.editing_teacher_id,
                    {
                        "nombres": payload["nombres"],
                        "apellidos": payload["apellidos"],
                        "identificacion": payload["identificacion"],
                        "titulo": payload["titulo"],
                    },
                )
            else:
                self.teacher_service.crear_docente(payload)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", f"No se pudo guardar el docente: {exc}")
            return

        QMessageBox.information(self, "Éxito", "Docente guardado correctamente.")
        self.reset_form()
        self.load_teachers()
        if self.app_signals:
            self.app_signals.data_changed.emit("teachers")

    def load_teachers(self) -> None:
        query = self.search_input.text().strip().lower()
        rows = self.teacher_service.listar_docentes()

        if query:
            rows = [
                row
                for row in rows
                if query in row.get("nombres", "").lower()
                or query in row.get("apellidos", "").lower()
                or query in row.get("identificacion", "").lower()
            ]

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(row_data.get("id_docente", "")))
            self.table.setItem(row, 1, QTableWidgetItem(row_data.get("nombres", "")))
            self.table.setItem(row, 2, QTableWidgetItem(row_data.get("apellidos", "")))
            self.table.setItem(row, 3, QTableWidgetItem(row_data.get("identificacion", "")))
            self.table.setItem(row, 4, QTableWidgetItem(row_data.get("titulo") or "No registrado"))
            estado = "Activo" if int(row_data.get("activo", 1)) == 1 else "Inactivo"
            status_item = QTableWidgetItem(estado)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, status_item)

    def select_teacher_from_table(self, row: int, _column: int) -> None:
        teacher_id = self.table.item(row, 0).text()
        data = self.teacher_service.obtener_docente(teacher_id)
        if not data:
            return

        self.editing_teacher_id = teacher_id
        self.id_input.setText(data.get("id_docente", ""))
        self.id_input.setEnabled(False)
        self.names_input.setText(data.get("nombres", ""))
        self.lastnames_input.setText(data.get("apellidos", ""))
        self.identification_input.setText(data.get("identificacion", ""))
        self.title_input.setText(data.get("titulo") or "No registrado")

    def toggle_teacher_status(self) -> None:
        if not self.editing_teacher_id:
            QMessageBox.warning(self, "Validación", "Seleccione un docente de la tabla.")
            return

        data = self.teacher_service.obtener_docente(self.editing_teacher_id)
        if not data:
            QMessageBox.warning(self, "Validación", "No se encontró el docente seleccionado.")
            return

        if int(data.get("activo", 1)) == 1:
            self.teacher_service.inactivar_docente(self.editing_teacher_id)
        else:
            self.teacher_service.activar_docente(self.editing_teacher_id)

        self.load_teachers()
        if self.app_signals:
            self.app_signals.data_changed.emit("teachers")

    def delete_teacher(self) -> None:
        if not self.editing_teacher_id:
            QMessageBox.warning(self, "Validación", "Seleccione un docente de la tabla.")
            return
        confirm = QMessageBox.question(self, "Confirmación", "¿Seguro que desea borrar el docente seleccionado?")
        if confirm != QMessageBox.Yes:
            return
        ok, message = self.teacher_service.eliminar_docente(self.editing_teacher_id)
        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.reset_form()
            self.load_teachers()
            if self.app_signals:
                self.app_signals.data_changed.emit("teachers")
        else:
            QMessageBox.warning(self, "Validación", message)

    def import_teachers(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de docentes",
            "",
            "Archivos soportados (*.xlsx *.xlsm *.csv)",
        )
        if not file_path:
            return
        try:
            summary = self.teacher_service.importar_desde_excel(file_path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", f"No se pudo importar: {exc}")
            return

        message = (
            f"Total leídos: {summary['total_leidos']}\n"
            f"Válidos: {summary['validos']}\n"
            f"Importados: {summary['importados']}\n"
            f"Omitidos: {summary['omitidos']}\n"
            f"Duplicados: {summary['duplicados']}\n"
            f"Errores: {len(summary['errores'])}"
        )
        if summary["errores"]:
            message += "\n\nDetalle:\n- " + "\n- ".join(summary["errores"][:15])
        QMessageBox.information(self, "Resultado importación", message)
        self.load_teachers()
        if self.app_signals:
            self.app_signals.data_changed.emit("teachers")

    def refresh_data(self) -> None:
        self.load_teachers()
