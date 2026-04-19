"""Vista funcional de asignaciones académicas."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QLabel,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.application.services.catalog_service import CatalogService
from src.application.services.teacher_service import TeacherService
from src.application.services.teaching_assignment_service import TeachingAssignmentService
from src.presentation.app_signals import AppSignals


class TeachingAssignmentsView(QWidget):
    def __init__(
        self,
        teaching_assignment_service: TeachingAssignmentService,
        teacher_service: TeacherService,
        catalog_service: CatalogService,
        app_signals: AppSignals | None = None,
    ) -> None:
        super().__init__()
        self.teaching_assignment_service = teaching_assignment_service
        self.teacher_service = teacher_service
        self.catalog_service = catalog_service
        self.app_signals = app_signals
        self.selected_assignment_id: str | None = None

        root = QVBoxLayout(self)
        title = QLabel("Asignaciones Académicas")
        title.setObjectName("Title")
        subtitle = QLabel("Asignar docente + asignatura + curso + paralelo + período")
        subtitle.setObjectName("Subtitle")

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)

        self.teacher_combo = QComboBox()
        self.subject_combo = QComboBox()
        self.course_combo = QComboBox()
        self.parallel_combo = QComboBox()
        self.period_combo = QComboBox()

        form.addRow("Docente", self.teacher_combo)
        form.addRow("Asignatura", self.subject_combo)
        form.addRow("Curso", self.course_combo)
        form.addRow("Paralelo", self.parallel_combo)
        form.addRow("Período", self.period_combo)

        actions = QHBoxLayout()
        self.save_button = QPushButton("Guardar asignación")
        self.save_button.clicked.connect(self.save_assignment)
        self.delete_button = QPushButton("Borrar")
        self.delete_button.clicked.connect(self.delete_assignment)
        actions.addWidget(self.save_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Docente", "Asignatura", "Curso", "Nombre", "Paralelo", "Período"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellClicked.connect(self.select_assignment)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(card)
        root.addLayout(actions)
        root.addWidget(self.table, 1)

        self.load_combos()
        self.load_assignments()

    def load_combos(self) -> None:
        self.teacher_combo.clear()
        for row in self.teacher_service.listar_docentes():
            label = f"{row.get('apellidos', '')} {row.get('nombres', '')}".strip()
            self.teacher_combo.addItem(label, row.get("id_docente"))

        self.subject_combo.clear()
        for row in self.catalog_service.listar_asignaturas():
            self.subject_combo.addItem(row.get("nombre", row.get("id_asignatura", "")), row.get("id_asignatura"))

        self.course_combo.clear()
        for row in self.catalog_service.listar_cursos():
            self.course_combo.addItem(row.get("nombre", row.get("id_curso", "")), row.get("id_curso"))

        self.parallel_combo.clear()
        for row in self.catalog_service.listar_paralelos():
            self.parallel_combo.addItem(row.get("nombre", row.get("id_paralelo", "")), row.get("id_paralelo"))

        self.period_combo.clear()
        for row in self.catalog_service.listar_periodos_lectivos():
            self.period_combo.addItem(row.get("id_periodo", ""), row.get("id_periodo"))

    def save_assignment(self) -> None:
        payload = {
            "docente_id": self.teacher_combo.currentData(),
            "asignatura_id": self.subject_combo.currentData(),
            "curso_id": self.course_combo.currentData(),
            "paralelo_id": self.parallel_combo.currentData(),
            "periodo_id": self.period_combo.currentData(),
        }
        ok, message = self.teaching_assignment_service.crear_asignacion(payload)
        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.load_assignments()
            if self.app_signals:
                self.app_signals.data_changed.emit("teaching_assignments")
        else:
            QMessageBox.warning(self, "Validación", message)

    def load_assignments(self) -> None:
        rows = self.teaching_assignment_service.listar_asignaciones()
        cursos = {row.get("id_curso"): row.get("nombre", "") for row in self.catalog_service.listar_cursos()}

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            course_id = row_data.get("curso_id", "")
            course_name = cursos.get(course_id, "")
            self.table.setItem(row, 0, QTableWidgetItem(row_data.get("id_asignacion", "")))
            self.table.setItem(row, 1, QTableWidgetItem(row_data.get("docente_id", "")))
            self.table.setItem(row, 2, QTableWidgetItem(row_data.get("asignatura_id", "")))
            self.table.setItem(row, 3, QTableWidgetItem(course_id))
            self.table.setItem(row, 4, QTableWidgetItem(course_name))
            self.table.setItem(row, 5, QTableWidgetItem(row_data.get("paralelo_id", "")))
            self.table.setItem(row, 6, QTableWidgetItem(row_data.get("periodo_id", "")))

    def select_assignment(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        self.selected_assignment_id = item.text() if item else None

    def delete_assignment(self) -> None:
        if not self.selected_assignment_id:
            QMessageBox.warning(self, "Validación", "Seleccione una asignación de la tabla.")
            return
        if QMessageBox.question(self, "Confirmación", "¿Desea borrar la asignación seleccionada?") != QMessageBox.Yes:
            return
        ok, message = self.teaching_assignment_service.eliminar_asignacion(self.selected_assignment_id)
        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.selected_assignment_id = None
            self.load_assignments()
            if self.app_signals:
                self.app_signals.data_changed.emit("teaching_assignments")
        else:
            QMessageBox.warning(self, "Validación", message)

    def refresh_data(self) -> None:
        self.load_combos()
        self.load_assignments()
