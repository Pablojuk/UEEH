"""Vista funcional de matrículas."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
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

from src.application.services.catalog_service import CatalogService
from src.application.services.enrollment_service import EnrollmentService
from src.application.services.student_service import StudentService


class EnrollmentsView(QWidget):
    def __init__(
        self,
        enrollment_service: EnrollmentService,
        student_service: StudentService,
        catalog_service: CatalogService,
    ) -> None:
        super().__init__()
        self.enrollment_service = enrollment_service
        self.student_service = student_service
        self.catalog_service = catalog_service

        root = QVBoxLayout(self)
        title = QLabel("Matrículas")
        title.setObjectName("Title")
        subtitle = QLabel("Asociar estudiantes a curso/paralelo/período")
        subtitle.setObjectName("Subtitle")

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por estudiante, curso, paralelo o período")
        self.search_input.textChanged.connect(self.load_enrollments)
        search_row.addWidget(self.search_input)

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)

        self.student_combo = QComboBox()
        self.course_combo = QComboBox()
        self.parallel_combo = QComboBox()
        self.period_combo = QComboBox()

        form.addRow("Estudiante", self.student_combo)
        form.addRow("Curso", self.course_combo)
        form.addRow("Paralelo", self.parallel_combo)
        form.addRow("Período", self.period_combo)

        actions = QHBoxLayout()
        self.save_button = QPushButton("Guardar matrícula")
        self.save_button.clicked.connect(self.save_enrollment)
        actions.addWidget(self.save_button)
        actions.addStretch(1)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Estudiante", "Curso", "Paralelo", "Período"])
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(search_row)
        root.addWidget(card)
        root.addLayout(actions)
        root.addWidget(self.table, 1)

        self.load_combos()
        self.load_enrollments()

    def load_combos(self) -> None:
        self.student_combo.clear()
        for student in self.student_service.listar_estudiantes():
            label = f"{student.get('apellidos', '')} {student.get('nombres', '')}".strip()
            self.student_combo.addItem(label, student.get("id_estudiante"))

        self.course_combo.clear()
        for row in self.catalog_service.listar_cursos():
            self.course_combo.addItem(row.get("nombre", row.get("id_curso", "")), row.get("id_curso"))

        self.parallel_combo.clear()
        for row in self.catalog_service.listar_paralelos():
            self.parallel_combo.addItem(row.get("nombre", row.get("id_paralelo", "")), row.get("id_paralelo"))

        self.period_combo.clear()
        for row in self.catalog_service.listar_periodos_lectivos():
            self.period_combo.addItem(row.get("id_periodo", ""), row.get("id_periodo"))

    def save_enrollment(self) -> None:
        payload = {
            "estudiante_id": self.student_combo.currentData(),
            "curso_id": self.course_combo.currentData(),
            "paralelo_id": self.parallel_combo.currentData(),
            "periodo_id": self.period_combo.currentData(),
        }
        ok, message = self.enrollment_service.crear_matricula(payload)
        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.load_enrollments()
        else:
            QMessageBox.warning(self, "Validación", message)

    def load_enrollments(self) -> None:
        query = self.search_input.text().strip()
        rows = self.enrollment_service.buscar_matriculas(query) if query else self.enrollment_service.listar_matriculas()

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(row_data.get("id_matricula", "")))
            self.table.setItem(row, 1, QTableWidgetItem(row_data.get("estudiante_id", "")))
            self.table.setItem(row, 2, QTableWidgetItem(row_data.get("curso_id", "")))
            self.table.setItem(row, 3, QTableWidgetItem(row_data.get("paralelo_id", "")))
            self.table.setItem(row, 4, QTableWidgetItem(row_data.get("periodo_id", "")))
