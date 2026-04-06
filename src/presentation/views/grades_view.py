"""Vista funcional para registro de notas por trimestre."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.application.services.grade_registration_service import GradeRegistrationService
from src.presentation.app_signals import AppSignals


class GradesView(QWidget):
    SUMMATIVE_COLUMNS = [
        ("proyecto", "Proyecto"),
        ("evaluacion", "Evaluación"),
        ("refuerzo", "Refuerzo"),
        ("mejora_sumativa", "Mejora Sumativa"),
        ("promedio_formativo", "Promedio Formativo"),
        ("promedio_sumativo", "Promedio Sumativo"),
        ("nota_trimestral", "Nota Trimestral"),
    ]

    def __init__(self, grade_registration_service: GradeRegistrationService, app_signals: AppSignals | None = None) -> None:
        super().__init__()
        self.grade_registration_service = grade_registration_service
        self.app_signals = app_signals
        self._contextos: list[dict] = []
        self._fila_meta: list[dict] = []
        self._numero_actividades = 3
        self._table_columns: list[tuple[str, str]] = []

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        title = QLabel("Notas")
        title.setObjectName("Title")
        subtitle = QLabel("Registro de notas por asignación y trimestre")
        subtitle.setObjectName("Subtitle")

        filter_card = QFrame()
        filter_card.setObjectName("Card")
        filter_row = QHBoxLayout(filter_card)

        self.assignment_combo = QComboBox()
        self.assignment_combo.setMinimumWidth(420)
        self.trimester_combo = QComboBox()
        self.trimester_combo.addItem("Trimestre 1", 1)
        self.trimester_combo.addItem("Trimestre 2", 2)
        self.trimester_combo.addItem("Trimestre 3", 3)

        self.activities_count_input = QSpinBox()
        self.activities_count_input.setRange(1, 20)
        self.activities_count_input.setValue(3)

        self.generate_activities_button = QPushButton("Generar actividades")
        self.generate_activities_button.clicked.connect(self.generate_activities)

        self.load_button = QPushButton("Cargar estudiantes")
        self.load_button.clicked.connect(self.load_rows)
        self.recalc_button = QPushButton("Recalcular")
        self.recalc_button.clicked.connect(self.recalculate_rows)
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_rows)

        filter_row.addWidget(QLabel("Asignación"))
        filter_row.addWidget(self.assignment_combo, 1)
        filter_row.addWidget(QLabel("Trimestre"))
        filter_row.addWidget(self.trimester_combo)
        filter_row.addWidget(QLabel("N° actividades"))
        filter_row.addWidget(self.activities_count_input)
        filter_row.addWidget(self.generate_activities_button)
        filter_row.addWidget(self.load_button)
        filter_row.addWidget(self.recalc_button)
        filter_row.addWidget(self.save_button)

        self.table = QTableWidget(0, 1)
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(filter_card)
        root.addWidget(self.table, 1)

        self.load_contexts()

    def load_contexts(self) -> None:
        self.assignment_combo.clear()
        self._contextos = self.grade_registration_service.listar_contextos_disponibles()

        if not self._contextos:
            self.assignment_combo.addItem("Sin asignaciones disponibles", None)
            return

        for row in self._contextos:
            self.assignment_combo.addItem(row.get("display", row.get("id_asignacion", "")), row.get("id_asignacion"))

    def generate_activities(self) -> None:
        asignacion_id = self.assignment_combo.currentData()
        trimestre = self.trimester_combo.currentData()
        if not asignacion_id:
            QMessageBox.warning(self, "Validación", "Seleccione una asignación")
            return
        numero = int(self.activities_count_input.value())
        ok, message = self.grade_registration_service.configurar_numero_actividades(asignacion_id, int(trimestre), numero)
        if ok:
            QMessageBox.information(self, "Éxito", message)
            self._numero_actividades = numero
            self._setup_columns()
        else:
            QMessageBox.warning(self, "Validación", message)

    def load_rows(self) -> None:
        asignacion_id = self.assignment_combo.currentData()
        trimestre = self.trimester_combo.currentData()
        if not asignacion_id:
            self._clear_table()
            return

        self._numero_actividades = self.grade_registration_service.obtener_numero_actividades(asignacion_id, int(trimestre))
        self.activities_count_input.setValue(self._numero_actividades)
        try:
            filas = self.grade_registration_service.cargar_registro(asignacion_id, int(trimestre))
        except ValueError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            self._clear_table()
            return

        self._fill_table(filas)

    def recalculate_rows(self) -> None:
        filas = self._collect_rows_from_table()
        recalculadas = []
        try:
            for fila in filas:
                recalculadas.append(self.grade_registration_service.recalcular_fila(fila, self._numero_actividades))
        except ValueError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return

        self._fill_table(recalculadas)

    def save_rows(self) -> None:
        asignacion_id = self.assignment_combo.currentData()
        trimestre = self.trimester_combo.currentData()
        if not asignacion_id:
            QMessageBox.warning(self, "Validación", "Seleccione una asignación")
            return

        filas = self._collect_rows_from_table()
        try:
            ok, message = self.grade_registration_service.guardar_registros(asignacion_id, int(trimestre), filas)
        except ValueError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return

        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.load_rows()
            if self.app_signals:
                self.app_signals.data_changed.emit("grades")
        else:
            QMessageBox.warning(self, "Error", message)

    def _setup_columns(self) -> None:
        self._table_columns = [("estudiante", "Estudiante")]
        for idx in range(1, self._numero_actividades + 1):
            self._table_columns.append((f"actividad_{idx}", f"Actividad {idx}"))
            self._table_columns.append((f"mejora_{idx}", f"Mejora {idx}"))
        self._table_columns.extend(self.SUMMATIVE_COLUMNS)
        self.table.setColumnCount(len(self._table_columns))
        self.table.setHorizontalHeaderLabels([title for _, title in self._table_columns])

    def _fill_table(self, rows: list[dict]) -> None:
        self._clear_table()
        self._setup_columns()
        self._fila_meta = rows
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, (field, _) in enumerate(self._table_columns):
                value = row_data.get(field)
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                if field in {"estudiante", "promedio_formativo", "promedio_sumativo", "nota_trimestral"}:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

    def _collect_rows_from_table(self) -> list[dict]:
        rows: list[dict] = []
        for row_idx in range(self.table.rowCount()):
            meta = self._fila_meta[row_idx] if row_idx < len(self._fila_meta) else {}
            row_data = dict(meta)
            for col, (field, _) in enumerate(self._table_columns):
                item = self.table.item(row_idx, col)
                text = item.text().strip() if item else ""
                row_data[field] = text if text != "" else None
            rows.append(row_data)
        return rows

    def _clear_table(self) -> None:
        self.table.setRowCount(0)
        self._fila_meta = []

    def refresh_data(self) -> None:
        self.load_contexts()
