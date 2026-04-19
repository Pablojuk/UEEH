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
from src.presentation.app_signals import AppSignals


class EnrollmentsView(QWidget):
    def __init__(
        self,
        enrollment_service: EnrollmentService,
        student_service: StudentService,
        catalog_service: CatalogService,
        app_signals: AppSignals | None = None,
    ) -> None:
        super().__init__()
        self.enrollment_service = enrollment_service
        self.student_service = student_service
        self.catalog_service = catalog_service
        self.app_signals = app_signals
        self._students_cache: list[dict] = []
        self.selected_enrollment_id: str | None = None

        root = QVBoxLayout(self)
        title = QLabel("Matrículas")
        title.setObjectName("Title")
        subtitle = QLabel("Asociar estudiantes a curso/paralelo/período")
        subtitle.setObjectName("Subtitle")

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)

        self.student_combo = QComboBox()
        self.student_filter_input = QLineEdit()
        self.student_filter_input.setPlaceholderText("🔍 Buscar estudiante por nombre, identificación o código")
        self.student_filter_input.textChanged.connect(self._filter_students)
        self.course_combo = QComboBox()
        self.course_combo.currentIndexChanged.connect(self.load_enrollments)
        self.parallel_combo = QComboBox()
        self.period_combo = QComboBox()

        student_row = QVBoxLayout()
        student_row.addWidget(self.student_filter_input)
        student_row.addWidget(self.student_combo)
        form.addRow("Estudiante", student_row)
        form.addRow("Curso", self.course_combo)
        form.addRow("Paralelo", self.parallel_combo)
        form.addRow("Período", self.period_combo)

        actions = QHBoxLayout()
        self.save_button = QPushButton("Guardar matrícula")
        self.save_button.clicked.connect(self.save_enrollment)
        self.delete_button = QPushButton("Borrar")
        self.delete_button.clicked.connect(self.delete_enrollment)
        actions.addWidget(self.save_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Estudiante", "Curso", "Nombre", "Paralelo", "Período"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellClicked.connect(self.select_enrollment)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(card)
        root.addLayout(actions)
        root.addWidget(self.table, 1)

        self.load_combos()
        self.load_enrollments()

    def load_combos(self) -> None:
        selected_student = self.student_combo.currentData()
        selected_course = self.course_combo.currentData()
        selected_parallel = self.parallel_combo.currentData()
        selected_period = self.period_combo.currentData()

        self._students_cache = sorted(
            self.student_service.listar_estudiantes(),
            key=lambda row: f"{row.get('apellidos', '').strip().lower()} {row.get('nombres', '').strip().lower()}",
        )
        self._filter_students(selected_student)

        self.course_combo.clear()
        for row in self.catalog_service.listar_cursos():
            self.course_combo.addItem(row.get("nombre", row.get("id_curso", "")), row.get("id_curso"))

        self.parallel_combo.clear()
        for row in self.catalog_service.listar_paralelos():
            self.parallel_combo.addItem(row.get("nombre", row.get("id_paralelo", "")), row.get("id_paralelo"))

        self.period_combo.clear()
        for row in self.catalog_service.listar_periodos_lectivos():
            self.period_combo.addItem(row.get("id_periodo", ""), row.get("id_periodo"))

        self._restore_combo_selection(self.course_combo, selected_course)
        self._restore_combo_selection(self.parallel_combo, selected_parallel)
        self._restore_combo_selection(self.period_combo, selected_period)

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
            if self.app_signals:
                self.app_signals.data_changed.emit("enrollments")
        else:
            QMessageBox.warning(self, "Validación", message)

    def load_enrollments(self) -> None:
        rows = self.enrollment_service.listar_matriculas()
        students = {s.get("id_estudiante"): s for s in self.student_service.listar_estudiantes()}
        courses = {row.get("id_curso"): row.get("nombre", "") for row in self.catalog_service.listar_cursos()}
        selected_course_id = self.course_combo.currentData()
        if selected_course_id:
            rows = [row for row in rows if row.get("curso_id") == selected_course_id]
        rows = sorted(
            rows,
            key=lambda row: (
                students.get(row.get("estudiante_id"), {}).get("apellidos", "").strip().lower(),
                students.get(row.get("estudiante_id"), {}).get("nombres", "").strip().lower(),
            ),
        )

        self.table.setRowCount(0)
        for row_data in rows:
            student = students.get(row_data.get("estudiante_id"), {})
            student_label = f"{student.get('apellidos', '')} {student.get('nombres', '')}".strip() or row_data.get("estudiante_id", "")
            course_id = row_data.get("curso_id", "")
            course_name = courses.get(course_id, "")
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(row_data.get("id_matricula", "")))
            self.table.setItem(row, 1, QTableWidgetItem(student_label))
            self.table.setItem(row, 2, QTableWidgetItem(course_id))
            self.table.setItem(row, 3, QTableWidgetItem(course_name))
            self.table.setItem(row, 4, QTableWidgetItem(row_data.get("paralelo_id", "")))
            self.table.setItem(row, 5, QTableWidgetItem(row_data.get("periodo_id", "")))

    def _filter_students(self, selected_student: str | None = None) -> None:
        query = self.student_filter_input.text().strip().lower()
        self.student_combo.clear()
        for student in self._students_cache:
            label = f"{student.get('apellidos', '')} {student.get('nombres', '')}".strip()
            identification = student.get("identificacion") or ""
            code = student.get("codigo") or ""
            searchable = f"{label} {identification} {code}".lower()
            if query and query not in searchable:
                continue
            display = f"{label} - {identification} - {code}".strip(" -") if identification or code else label
            self.student_combo.addItem(display, student.get("id_estudiante"))
        if selected_student:
            self._restore_combo_selection(self.student_combo, selected_student)

    @staticmethod
    def _restore_combo_selection(combo: QComboBox, selected_value: str | None) -> None:
        if not selected_value:
            return
        index = combo.findData(selected_value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def select_enrollment(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        self.selected_enrollment_id = item.text() if item else None

    def delete_enrollment(self) -> None:
        if not self.selected_enrollment_id:
            QMessageBox.warning(self, "Validación", "Seleccione una matrícula de la tabla.")
            return
        if QMessageBox.question(self, "Confirmación", "¿Desea borrar la matrícula seleccionada?") != QMessageBox.Yes:
            return
        ok, message = self.enrollment_service.eliminar_matricula(self.selected_enrollment_id)
        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.selected_enrollment_id = None
            self.load_enrollments()
            if self.app_signals:
                self.app_signals.data_changed.emit("enrollments")
        else:
            QMessageBox.warning(self, "Validación", message)

    def refresh_data(self) -> None:
        self.load_combos()
        self.load_enrollments()
