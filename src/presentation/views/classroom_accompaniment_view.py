"""Vista de Acompañamiento Integral en el Aula."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.application.services.classroom_accompaniment_service import (
    MAX_ACTIVE_SKILLS,
    ClassroomAccompanimentService,
    RESPONSE_OPTIONS,
)
from src.presentation.app_signals import AppSignals


class SkillConfigDialog(QDialog):
    """Diálogo para mostrar/ocultar habilidades por categoría."""

    def __init__(self, categories: list[dict[str, Any]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurar habilidades")
        self.resize(560, 540)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._max_skills = MAX_ACTIVE_SKILLS

        layout = QVBoxLayout(self)
        info = QLabel("Seleccione las habilidades activas para esta asignación y trimestre.")
        info.setWordWrap(True)
        layout.addWidget(info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        for category in categories:
            frame = QFrame()
            frame.setObjectName("Card")
            frame_layout = QVBoxLayout(frame)
            title = QLabel(category["category"])
            title.setStyleSheet("font-weight: 700;")
            frame_layout.addWidget(title)
            grid = QGridLayout()
            col = 0
            row = 0
            for skill in category["skills"]:
                checkbox = QCheckBox(skill["label"])
                checkbox.setChecked(bool(skill.get("visible", True)))
                checkbox.toggled.connect(self._on_checkbox_toggled)
                self._checkboxes[skill["key"]] = checkbox
                grid.addWidget(checkbox, row, col)
                col += 1
                if col > 1:
                    col = 0
                    row += 1
            frame_layout.addLayout(grid)
            content_layout.addWidget(frame)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_skills(self) -> list[str]:
        return [key for key, checkbox in self._checkboxes.items() if checkbox.isChecked()]

    def _on_checkbox_toggled(self, checked: bool) -> None:
        if not checked:
            return
        selected_count = len(self.selected_skills())
        if selected_count <= self._max_skills:
            return
        checkbox = self.sender()
        if isinstance(checkbox, QCheckBox):
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.blockSignals(False)
        QMessageBox.warning(
            self,
            "Validación",
            f"Solo se pueden seleccionar hasta {self._max_skills} habilidades activas para esta evaluación.",
        )


class ClassroomAccompanimentView(QWidget):
    """Pantalla de registro cualitativo de acompañamiento integral."""

    TRIMESTERS = (
        ("Primer Trimestre", 1),
        ("Segundo Trimestre", 2),
        ("Tercer Trimestre", 3),
    )

    def __init__(self, accompaniment_service: ClassroomAccompanimentService, app_signals: AppSignals | None = None) -> None:
        super().__init__()
        self.accompaniment_service = accompaniment_service
        self.app_signals = app_signals

        self._contexts: list[dict[str, Any]] = []
        self._skill_categories: list[dict[str, Any]] = []
        self._active_skills: list[str] = []
        self._skills_by_key: dict[str, dict[str, Any]] = {}
        self._students: list[dict[str, Any]] = []
        self._responses: dict[str, dict[str, str]] = {}

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        title = QLabel("Acompañamiento Integral en el Aula")
        title.setObjectName("Title")
        subtitle = QLabel("Evaluación cualitativa por estudiante, asignación y trimestre")
        subtitle.setObjectName("Subtitle")

        filter_card = QFrame()
        filter_card.setObjectName("Card")
        filter_row = QHBoxLayout(filter_card)

        self.assignment_combo = QComboBox()
        self.assignment_combo.setMinimumWidth(360)
        self.trimester_combo = QComboBox()
        for label, value in self.TRIMESTERS:
            self.trimester_combo.addItem(label, value)

        self.load_button = QPushButton("Cargar listado")
        self.load_button.clicked.connect(self.load_rows)
        self.save_button = QPushButton("Guardar evaluación")
        self.save_button.clicked.connect(self.save_rows)
        self.configure_skills_button = QPushButton("Configurar habilidades")
        self.configure_skills_button.clicked.connect(self.open_skill_config)

        filter_row.addWidget(QLabel("Asignación"))
        filter_row.addWidget(self.assignment_combo, 1)
        filter_row.addWidget(QLabel("Trimestre"))
        filter_row.addWidget(self.trimester_combo)
        filter_row.addWidget(self.load_button)
        filter_row.addWidget(self.save_button)
        filter_row.addWidget(self.configure_skills_button)

        self.skills_reference_card = QFrame()
        self.skills_reference_card.setObjectName("Card")
        self.skills_reference_layout = QVBoxLayout(self.skills_reference_card)

        self.table = QTableWidget(0, 2)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(filter_card)
        root.addWidget(self.skills_reference_card)
        root.addWidget(self.table, 1)

        self.load_contexts()

    def load_contexts(self, selected_assignment_id: str | None = None) -> None:
        self.assignment_combo.clear()
        self._contexts = self.accompaniment_service.listar_contextos_disponibles()
        if not self._contexts:
            self.assignment_combo.addItem("Sin asignaciones disponibles", None)
            return

        for context in self._contexts:
            self.assignment_combo.addItem(context.get("display", context.get("id_asignacion", "")), context.get("id_asignacion"))

        if selected_assignment_id:
            idx = self.assignment_combo.findData(selected_assignment_id)
            if idx >= 0:
                self.assignment_combo.setCurrentIndex(idx)

    def load_rows(self) -> None:
        assignment_id = self.assignment_combo.currentData()
        trimester_num = self.trimester_combo.currentData()
        if not assignment_id:
            self._clear_table()
            return

        try:
            payload = self.accompaniment_service.cargar_evaluacion(assignment_id, int(trimester_num))
        except ValueError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            self._clear_table()
            return

        self._skill_categories = payload.get("skill_categories", [])
        self._skills_by_key = {
            skill["key"]: skill
            for category in self._skill_categories
            for skill in category.get("skills", [])
        }
        self._active_skills = list(payload.get("active_skills", []))
        self._students = list(payload.get("students", []))
        self._responses = dict(payload.get("responses", {}))
        validation_message = payload.get("validation_message", "")
        if validation_message:
            QMessageBox.warning(self, "Validación", validation_message)

        self._refresh_skills_reference()
        self._fill_table()

    def save_rows(self) -> None:
        assignment_id = self.assignment_combo.currentData()
        trimester_num = self.trimester_combo.currentData()
        if not assignment_id:
            QMessageBox.warning(self, "Validación", "Seleccione una asignación")
            return

        self._collect_responses_from_table()
        ok, message = self.accompaniment_service.guardar_evaluacion(
            assignment_id,
            int(trimester_num),
            self._active_skills,
            self._responses,
        )
        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.load_rows()
            if self.app_signals:
                self.app_signals.data_changed.emit("accompaniment")
        else:
            QMessageBox.warning(self, "Error", message)

    def open_skill_config(self) -> None:
        if not self._skill_categories:
            assignment_id = self.assignment_combo.currentData()
            if assignment_id:
                self.load_rows()
        if not self._skill_categories:
            QMessageBox.information(self, "Información", "Primero cargue una asignación para configurar habilidades")
            return

        dialog = SkillConfigDialog(self._skill_categories, self)
        if dialog.exec() != QDialog.Accepted:
            return

        selected = dialog.selected_skills()
        if not selected:
            QMessageBox.warning(self, "Validación", "Debe dejar al menos una habilidad visible")
            return
        if len(selected) > MAX_ACTIVE_SKILLS:
            QMessageBox.warning(
                self,
                "Validación",
                f"Solo se pueden seleccionar hasta {MAX_ACTIVE_SKILLS} habilidades activas para esta evaluación.",
            )
            return

        selected_set = set(selected)
        for category in self._skill_categories:
            for skill in category["skills"]:
                skill["visible"] = skill["key"] in selected_set

        self._active_skills = [skill["key"] for category in self._skill_categories for skill in category["skills"] if skill["visible"]]
        self._refresh_skills_reference()
        self._fill_table()

    def refresh_data(self) -> None:
        selected_assignment = self.assignment_combo.currentData()
        self.load_contexts(selected_assignment_id=selected_assignment)

    def _fill_table(self) -> None:
        self._clear_table()
        skill_labels = [self._skills_by_key[skill_key]["label"] for skill_key in self._active_skills if skill_key in self._skills_by_key]
        headers = [
            "Código",
            "Nómina",
            *skill_labels,
            "Total Siempre",
            "Total Frecuentemente",
            "Total Ocasionalmente",
            "Total Nunca",
            "Puntaje total",
            "Valoración final",
        ]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(self._students))

        for row_idx, student in enumerate(self._students):
            student_id = student["student_id"]
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(student.get("code") or "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(student.get("name", "")))

            row_values = self._responses.get(student_id, {})
            for col_offset, skill_key in enumerate(self._active_skills):
                combo = QComboBox()
                combo.addItem("", "")
                for option in RESPONSE_OPTIONS:
                    combo.addItem(option, option)
                value = row_values.get(skill_key, "")
                idx = combo.findData(value)
                combo.setCurrentIndex(idx if idx >= 0 else 0)
                combo.currentIndexChanged.connect(lambda _=0, sid=student_id, sk=skill_key, c=combo: self._on_skill_changed(sid, sk, c))
                self.table.setCellWidget(row_idx, 2 + col_offset, combo)

            self._render_result_cells(row_idx, student_id)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _render_result_cells(self, row_idx: int, student_id: str) -> None:
        result = self.accompaniment_service.calcular_resultado_estudiante(
            self._responses.get(student_id, {}),
            self._active_skills,
        )
        base_col = 2 + len(self._active_skills)
        self.table.setItem(row_idx, base_col, QTableWidgetItem(str(result["total_siempre"])))
        self.table.setItem(row_idx, base_col + 1, QTableWidgetItem(str(result["total_frecuentemente"])))
        self.table.setItem(row_idx, base_col + 2, QTableWidgetItem(str(result["total_ocasionalmente"])))
        self.table.setItem(row_idx, base_col + 3, QTableWidgetItem(str(result["total_nunca"])))
        self.table.setItem(
            row_idx,
            base_col + 4,
            QTableWidgetItem("" if result.get("puntaje_total_ponderado") is None else str(result.get("puntaje_total_ponderado"))),
        )
        self.table.setItem(row_idx, base_col + 5, QTableWidgetItem(result["valoracion_final"]))

        for col in range(base_col, base_col + 6):
            item = self.table.item(row_idx, col)
            if item:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def _on_skill_changed(self, student_id: str, skill_key: str, combo: QComboBox) -> None:
        value = str(combo.currentData() or "")
        self._responses.setdefault(student_id, {})[skill_key] = value

        row_idx = self._student_row_index(student_id)
        if row_idx >= 0:
            self._render_result_cells(row_idx, student_id)

    def _student_row_index(self, student_id: str) -> int:
        for idx, student in enumerate(self._students):
            if student["student_id"] == student_id:
                return idx
        return -1

    def _collect_responses_from_table(self) -> None:
        for row_idx, student in enumerate(self._students):
            sid = student["student_id"]
            self._responses.setdefault(sid, {})
            for col_offset, skill_key in enumerate(self._active_skills):
                combo = self.table.cellWidget(row_idx, 2 + col_offset)
                if isinstance(combo, QComboBox):
                    self._responses[sid][skill_key] = str(combo.currentData() or "")

    def _clear_table(self) -> None:
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    def _refresh_skills_reference(self) -> None:
        while self.skills_reference_layout.count():
            item = self.skills_reference_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        title = QLabel("Habilidades activas para la evaluación actual")
        title.setStyleSheet("font-weight: 700;")
        self.skills_reference_layout.addWidget(title)

        for category in self._skill_categories:
            labels = [skill["label"] for skill in category.get("skills", []) if skill.get("visible", True)]
            text = "• " + " | ".join(labels) if labels else "• (Sin habilidades activas en esta categoría)"
            label = QLabel(f"{category['category']}: {text}")
            label.setWordWrap(True)
            self.skills_reference_layout.addWidget(label)
