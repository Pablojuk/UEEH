"""Vista funcional de estudiantes con importación básica."""

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

from src.application.services.student_import_service import StudentImportService
from src.application.services.student_service import StudentService


class StudentsView(QWidget):
    def __init__(self, student_service: StudentService, student_import_service: StudentImportService) -> None:
        super().__init__()
        self.student_service = student_service
        self.student_import_service = student_import_service
        self.editing_student_id: str | None = None

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        title = QLabel("Estudiantes")
        title.setObjectName("Title")
        subtitle = QLabel("Registro manual e importación desde Excel/CSV")
        subtitle.setObjectName("Subtitle")

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombres, apellidos, identificación o código")
        self.search_input.textChanged.connect(self.load_students)
        search_row.addWidget(self.search_input)

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)

        self.names_input = QLineEdit()
        self.lastnames_input = QLineEdit()
        self.identification_input = QLineEdit()
        self.code_input = QLineEdit()

        form.addRow("Nombres", self.names_input)
        form.addRow("Apellidos", self.lastnames_input)
        form.addRow("Identificación", self.identification_input)
        form.addRow("Código estudiante (opcional)", self.code_input)

        actions = QHBoxLayout()
        self.new_button = QPushButton("Nuevo")
        self.new_button.clicked.connect(self.reset_form)
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_student)
        self.import_button = QPushButton("Importar Excel/CSV")
        self.import_button.clicked.connect(self.import_students)

        actions.addWidget(self.new_button)
        actions.addWidget(self.save_button)
        actions.addWidget(self.import_button)
        actions.addStretch(1)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Apellidos", "Nombres", "Identificación"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellClicked.connect(self.select_student)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(search_row)
        root.addWidget(card)
        root.addLayout(actions)
        root.addWidget(self.table, 1)

        self.load_students()

    def reset_form(self) -> None:
        self.editing_student_id = None
        self.names_input.clear()
        self.lastnames_input.clear()
        self.identification_input.clear()
        self.code_input.clear()
        self.table.clearSelection()

    def save_student(self) -> None:
        payload = {
            "nombres": self.names_input.text().strip(),
            "apellidos": self.lastnames_input.text().strip(),
            "identificacion": self.identification_input.text().strip() or None,
            "codigo": self.code_input.text().strip() or None,
        }

        try:
            if self.editing_student_id:
                ok, message = self.student_service.actualizar_estudiante(self.editing_student_id, payload)
            else:
                ok, message = self.student_service.crear_estudiante(payload)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {exc}")
            return

        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.reset_form()
            self.load_students()
        else:
            QMessageBox.warning(self, "Validación", message)

    def load_students(self) -> None:
        query = self.search_input.text().strip()
        rows = self.student_service.buscar_estudiantes(query) if query else self.student_service.listar_estudiantes()

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(row_data.get("id_estudiante", "")))
            self.table.setItem(row, 1, QTableWidgetItem(row_data.get("apellidos", "")))
            self.table.setItem(row, 2, QTableWidgetItem(row_data.get("nombres", "")))
            self.table.setItem(row, 3, QTableWidgetItem(row_data.get("identificacion") or ""))

    def select_student(self, row: int, _column: int) -> None:
        student_id = self.table.item(row, 0).text()
        data = self.student_service.obtener_estudiante_por_id(student_id)
        if not data:
            return

        self.editing_student_id = student_id
        self.names_input.setText(data.get("nombres", ""))
        self.lastnames_input.setText(data.get("apellidos", ""))
        self.identification_input.setText(data.get("identificacion") or "")
        self.code_input.setText(data.get("codigo") or "")

    def import_students(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de estudiantes",
            "",
            "Archivos soportados (*.xlsx *.xlsm *.csv)",
        )
        if not file_path:
            return

        preview = self.student_import_service.generate_preview(file_path)
        if preview.errors:
            QMessageBox.warning(self, "Importación", "\n".join(preview.errors))
            return

        preview_count = len(preview.rows)
        answer = QMessageBox.question(
            self,
            "Vista previa",
            f"Filas detectadas para importar: {preview_count}.\n¿Desea continuar?",
        )
        if answer != QMessageBox.Yes:
            return

        summary = self.student_import_service.import_file(file_path)
        message = (
            f"Total leídos: {summary['total_leidos']}\n"
            f"Válidos: {summary['validos']}\n"
            f"Importados: {summary['importados']}\n"
            f"Omitidos: {summary['omitidos']}\n"
            f"Duplicados: {summary['duplicados']}"
        )
        if summary["errores"]:
            message += "\n\nErrores:\n- " + "\n- ".join(summary["errores"][:10])

        QMessageBox.information(self, "Resultado de importación", message)
        self.load_students()
