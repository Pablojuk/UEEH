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
        self.student_filter_input = QLineEdit()
        self.student_filter_input.setPlaceholderText("🔍 Buscar estudiante por nombre o identificación")
        self.student_filter_input.textChanged.connect(self._filter_students)
        self.course_combo = QComboBox()
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
        self._students_cache = self.student_service.listar_estudiantes()
        self._filter_students()

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
            if self.app_signals:
                self.app_signals.data_changed.emit("enrollments")
        else:
            QMessageBox.warning(self, "Validación", message)

    def load_enrollments(self) -> None:
        query = self.search_input.text().strip().lower()
        rows = self.enrollment_service.listar_matriculas()
        students = {s.get("id_estudiante"): s for s in self.student_service.listar_estudiantes()}
        if query:
            filtered: list[dict] = []
            for row in rows:
                student = students.get(row.get("estudiante_id"), {})
                student_text = f"{student.get('apellidos', '')} {student.get('nombres', '')} {student.get('identificacion', '')}".lower()
                search_text = f"{student_text} {row.get('curso_id', '')} {row.get('paralelo_id', '')} {row.get('periodo_id', '')}".lower()
                if query in search_text:
                    filtered.append(row)
            rows = filtered

        self.table.setRowCount(0)
        for row_data in rows:
            student = students.get(row_data.get("estudiante_id"), {})
            student_label = f"{student.get('apellidos', '')} {student.get('nombres', '')}".strip() or row_data.get("estudiante_id", "")
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(row_data.get("id_matricula", "")))
            self.table.setItem(row, 1, QTableWidgetItem(student_label))
            self.table.setItem(row, 2, QTableWidgetItem(row_data.get("curso_id", "")))
            self.table.setItem(row, 3, QTableWidgetItem(row_data.get("paralelo_id", "")))
            self.table.setItem(row, 4, QTableWidgetItem(row_data.get("periodo_id", "")))

    def _filter_students(self) -> None:
        query = self.student_filter_input.text().strip().lower()
        self.student_combo.clear()
        for student in self._students_cache:
            label = f"{student.get('apellidos', '')} {student.get('nombres', '')}".strip()
            identification = student.get("identificacion") or ""
            searchable = f"{label} {identification}".lower()
            if query and query not in searchable:
                continue
            display = f"{label} - {identification}" if identification else label
            self.student_combo.addItem(display, student.get("id_estudiante"))

    def refresh_data(self) -> None:
        self.load_combos()
        self.load_enrollments()
