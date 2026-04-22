"""Vista funcional de matrículas."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
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
        self.bulk_select_button = QPushButton("Selec. Estu.")
        self.bulk_select_button.clicked.connect(self.open_bulk_enrollment_dialog)
        self.save_button = QPushButton("Guardar matrícula")
        self.save_button.clicked.connect(self.save_enrollment)
        self.delete_button = QPushButton("Borrar")
        self.delete_button.clicked.connect(self.delete_enrollment)
        actions.addWidget(self.bulk_select_button)
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

    def open_bulk_enrollment_dialog(self) -> None:
        students = self.student_service.listar_estudiantes()
        courses = self.catalog_service.listar_cursos()
        parallels = self.catalog_service.listar_paralelos()
        periods = self.catalog_service.listar_periodos_lectivos()
        dialog = BulkEnrollmentDialog(
            enrollment_service=self.enrollment_service,
            students=students,
            courses=courses,
            parallels=parallels,
            periods=periods,
            selected_course=self.course_combo.currentData(),
            selected_parallel=self.parallel_combo.currentData(),
            selected_period=self.period_combo.currentData(),
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            self.load_enrollments()
            if self.app_signals:
                self.app_signals.data_changed.emit("enrollments")


class BulkEnrollmentDialog(QDialog):
    def __init__(
        self,
        enrollment_service: EnrollmentService,
        students: list[dict],
        courses: list[dict],
        parallels: list[dict],
        periods: list[dict],
        selected_course: str | None,
        selected_parallel: str | None,
        selected_period: str | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.enrollment_service = enrollment_service
        self._students = students
        self._selected_student_ids: set[str] = set()
        self._is_rendering = False
        self.setWindowTitle("Selección masiva de estudiantes")
        self.resize(860, 560)

        root = QVBoxLayout(self)
        form = QFormLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar estudiante por nombre, identificación o código")
        self.search_input.textChanged.connect(self._render_students)
        self.course_combo = QComboBox()
        self.parallel_combo = QComboBox()
        self.period_combo = QComboBox()

        for row in courses:
            self.course_combo.addItem(row.get("nombre", row.get("id_curso", "")), row.get("id_curso"))
        for row in parallels:
            self.parallel_combo.addItem(row.get("nombre", row.get("id_paralelo", "")), row.get("id_paralelo"))
        for row in periods:
            self.period_combo.addItem(row.get("id_periodo", ""), row.get("id_periodo"))
        self._restore_combo_selection(self.course_combo, selected_course)
        self._restore_combo_selection(self.parallel_combo, selected_parallel)
        self._restore_combo_selection(self.period_combo, selected_period)

        form.addRow("Estudiante", self.search_input)
        form.addRow("Curso", self.course_combo)
        form.addRow("Paralelo", self.parallel_combo)
        form.addRow("Período", self.period_combo)
        root.addLayout(form)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Sel.", "Código", "Estudiante", "Identificación"])
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        buttons = QDialogButtonBox()
        self.save_button = QPushButton("Guardar matrícula")
        self.clear_button = QPushButton("Borrar")
        self.cancel_button = QPushButton("Cerrar")
        self.save_button.clicked.connect(self._save_bulk)
        self.clear_button.clicked.connect(self._clear_selection)
        self.cancel_button.clicked.connect(self.reject)
        buttons.addButton(self.save_button, QDialogButtonBox.AcceptRole)
        buttons.addButton(self.clear_button, QDialogButtonBox.ResetRole)
        buttons.addButton(self.cancel_button, QDialogButtonBox.RejectRole)
        root.addWidget(buttons)

        self._render_students()

    @staticmethod
    def _restore_combo_selection(combo: QComboBox, selected_value: str | None) -> None:
        if not selected_value:
            return
        index = combo.findData(selected_value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _render_students(self) -> None:
        self._is_rendering = True
        query = self.search_input.text().strip().lower()
        filtered = []
        for student in self._students:
            label = f"{student.get('apellidos', '')} {student.get('nombres', '')}".strip()
            identification = student.get("identificacion") or ""
            code = student.get("codigo") or ""
            searchable = f"{label} {identification} {code}".lower()
            if query and query not in searchable:
                continue
            filtered.append(student)

        self.table.setRowCount(0)
        for student in filtered:
            row = self.table.rowCount()
            self.table.insertRow(row)
            check_item = QTableWidgetItem("")
            check_item.setFlags(check_item.flags() | Qt.ItemIsUserCheckable)
            student_id = str(student.get("id_estudiante") or "")
            check_item.setCheckState(Qt.Checked if student_id in self._selected_student_ids else Qt.Unchecked)
            check_item.setData(Qt.UserRole, student_id)
            self.table.setItem(row, 0, check_item)
            self.table.setItem(row, 1, QTableWidgetItem(str(student.get("codigo", ""))))
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(f"{student.get('apellidos', '')} {student.get('nombres', '')}".strip()),
            )
            self.table.setItem(row, 3, QTableWidgetItem(str(student.get("identificacion", ""))))
        self.table.resizeColumnsToContents()
        self._is_rendering = False

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._is_rendering or item.column() != 0:
            return
        student_id = str(item.data(Qt.UserRole) or "").strip()
        if not student_id:
            return
        if item.checkState() == Qt.Checked:
            self._selected_student_ids.add(student_id)
        else:
            self._selected_student_ids.discard(student_id)

    def _selected_students(self) -> list[str]:
        return sorted(self._selected_student_ids)

    def _save_bulk(self) -> None:
        student_ids = self._selected_students()
        if not student_ids:
            QMessageBox.warning(self, "Validación", "Seleccione al menos un estudiante.")
            return
        payload = {
            "curso_id": self.course_combo.currentData(),
            "paralelo_id": self.parallel_combo.currentData(),
            "periodo_id": self.period_combo.currentData(),
        }
        ok, message = self.enrollment_service.crear_matriculas_masivas(student_ids, payload)
        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Validación", message)

    def _clear_selection(self) -> None:
        self._selected_student_ids.clear()
        self.search_input.clear()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked)
