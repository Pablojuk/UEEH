"""Vista funcional para registro de notas por trimestre."""

from __future__ import annotations
import unicodedata
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate, QEvent, Qt
from PySide6.QtGui import QColor, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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

if TYPE_CHECKING:
    from src.application.services.classroom_accompaniment_service import ClassroomAccompanimentService
    from src.presentation.views.animacion_lectura_view import AnimacionLecturaView
    from src.presentation.views.classroom_accompaniment_view import ClassroomAccompanimentView
    from src.presentation.views.orientacion_vocacional_view import OrientacionVocacionalView


class GradesView(QWidget):
    SUMMATIVE_COLUMNS = [
        ("proyecto", "Proyecto Interdisciplinar"),
        ("evaluacion", "Evaluación Trimestral"),
        ("promedio_evaluacion_sumativa", "Promedio Evaluación Sumativa"),
        ("refuerzo", "Calificación Refuerzo Pedagógico"),
        ("mejora_sumativa", "Evaluación de Mejora"),
        ("promedio_con_mejora_sumativa", "Promedio con Mejora Evaluación Sumativa"),
        ("promedio_formativo", "Promedio Evaluación Formativa"),
        ("promedio_formativo_70", "Promedio Evaluación Formativa 70%"),
        ("promedio_sumativo_30", "Promedio Evaluación Sumativa 30%"),
        ("nota_trimestral", "Promedio Trimestral"),
        ("cualitativo", "Cualitativo"),
        ("cualitativo_adicional", "Equivalencia"),
    ]
    SUMMATIVE_COLUMNS_EGB_BASICA = [
        ("proyecto", "Proyecto Interdisciplinar"),
        ("evaluacion", "Evaluación Trimestral"),
        ("nota_trimestral", "Promedio Trimestral"),
        ("cualitativo", "Cualitativo"),
        ("cualitativo_adicional", "Equivalencia"),
    ]

    ACCOMPANIMENT_SUBJECT_NAME = "acompañamiento integral en el aula"
    BEHAVIOR_SUBJECT_NAME = "comportamiento"
    ANIMATION_READING_SUBJECT_NAME = "animacion a la lectura"
    VOCATIONAL_ORIENTATION_SUBJECT_NAME = "orientacion vocacional y profesional"

    def __init__(
        self,
        grade_registration_service: GradeRegistrationService,
        app_signals: AppSignals | None = None,
        classroom_accompaniment_service: "ClassroomAccompanimentService | None" = None,
    ) -> None:
        super().__init__()
        self.grade_registration_service = grade_registration_service
        self.app_signals = app_signals
        self.classroom_accompaniment_service = classroom_accompaniment_service
        self._contextos: list[dict] = []
        self._fila_meta: list[dict] = []
        self._numero_actividades = 3
        self._table_columns: list[tuple[str, str]] = []
        self._activity_name_inputs: dict[int, str] = {}
        self._activity_group_columns: list[tuple[int, int, int]] = []
        self._accompaniment_mode = False
        self._animation_reading_mode = False
        self._vocational_orientation_mode = False
        self._switching_mode = False
        self._egb_basic_mode = False
        self._updating_calculations = False

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        title = QLabel("Notas")
        title.setObjectName("Title")
        subtitle = QLabel("Registro de notas por asignación y trimestre")
        subtitle.setObjectName("Subtitle")

        self.filter_card = QFrame()
        self.filter_card.setObjectName("Card")
        filter_row = QHBoxLayout(self.filter_card)

        self.assignment_combo = QComboBox()
        self.assignment_combo.setMinimumWidth(350)
        self.assignment_combo.currentIndexChanged.connect(self._on_assignment_or_trimester_changed)
        self.trimester_combo = QComboBox()
        self.trimester_combo.addItem("Trimestre 1", 1)
        self.trimester_combo.addItem("Trimestre 2", 2)
        self.trimester_combo.addItem("Trimestre 3", 3)
        self.trimester_combo.currentIndexChanged.connect(self._on_assignment_or_trimester_changed)

        self.activities_count_input = QSpinBox()
        self.activities_count_input.setRange(1, 20)
        self.activities_count_input.setValue(3)
        self.activities_count_input.setMinimumWidth(90)

        self.generate_activities_button = QPushButton("Generar actividades")
        self.generate_activities_button.clicked.connect(self.generate_activities)

        self.load_button = QPushButton("Cargar estudiantes")
        self.load_button.clicked.connect(self.load_rows)
        self.recalc_button = QPushButton("Recalcular")
        self.recalc_button.clicked.connect(self.recalculate_rows)
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_rows)

        self.activities_count_label = QLabel("N° actividades")

        filter_row.addWidget(QLabel("Asignación"))
        filter_row.addWidget(self.assignment_combo, 1)
        filter_row.addWidget(QLabel("Trimestre"))
        filter_row.addWidget(self.trimester_combo)
        filter_row.addWidget(self.activities_count_label)
        filter_row.addWidget(self.activities_count_input)
        filter_row.addWidget(self.generate_activities_button)
        filter_row.addWidget(self.load_button)
        filter_row.addWidget(self.recalc_button)
        filter_row.addWidget(self.save_button)

        self.table = QTableWidget(0, 1)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(60)
        self.table.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setWordWrap(False)
        self.table.setStyleSheet(
            """
            QTableWidget::item:selected {
                background-color: #F8F8FF;
                color: #1f2937;
            }
            """
        )
        self.table.installEventFilter(self)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.copy_shortcut = QShortcut("Ctrl+C", self.table)
        self.copy_shortcut.activated.connect(self._copy_selected_cells)
        self.paste_shortcut = QShortcut("Ctrl+V", self.table)
        self.paste_shortcut.activated.connect(self._paste_from_clipboard)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(self.filter_card)
        root.addWidget(self.table, 1)
        self.accompaniment_view: "ClassroomAccompanimentView | None" = None
        self.animation_reading_view: "AnimacionLecturaView | None" = None
        self.vocational_orientation_view: "OrientacionVocacionalView | None" = None
        if self.classroom_accompaniment_service is not None:
            from src.presentation.views.classroom_accompaniment_view import ClassroomAccompanimentView
            from src.presentation.views.animacion_lectura_view import AnimacionLecturaView
            from src.presentation.views.orientacion_vocacional_view import OrientacionVocacionalView

            self.accompaniment_view = ClassroomAccompanimentView(
                accompaniment_service=self.classroom_accompaniment_service,
                app_signals=self.app_signals,
            )
            self.accompaniment_view.set_embedded_mode(True)
            self.accompaniment_view.set_notes_mode(True)
            self.accompaniment_view.hide()
            root.addWidget(self.accompaniment_view, 1)
            self.animation_reading_view = AnimacionLecturaView(
                list_signers=self.classroom_accompaniment_service.listar_firmantes_disponibles,
                get_assignment_context=self.classroom_accompaniment_service.obtener_contexto,
                get_institution_data=self.classroom_accompaniment_service.obtener_datos_institucion,
                on_save_payload=self._save_animation_reading_payload,
            )
            self.animation_reading_view.set_notes_mode(True)
            self.animation_reading_view.level_combo.currentIndexChanged.connect(self._on_animation_level_changed)
            self.animation_reading_view.hide()
            root.addWidget(self.animation_reading_view, 1)
            self.vocational_orientation_view = OrientacionVocacionalView(
                on_save_payload=self._save_vocational_orientation_payload
            )
            self.vocational_orientation_view.hide()
            root.addWidget(self.vocational_orientation_view, 1)

        self.load_contexts()

    def load_contexts(self, selected_assignment_id: str | None = None) -> None:
        self.assignment_combo.clear()
        self._contextos = self.grade_registration_service.listar_contextos_disponibles()

        if not self._contextos:
            self.assignment_combo.addItem("Sin asignaciones disponibles", None)
            return

        for row in self._contextos:
            self.assignment_combo.addItem(row.get("display", row.get("id_asignacion", "")), row.get("id_asignacion"))
        if selected_assignment_id:
            idx = self.assignment_combo.findData(selected_assignment_id)
            if idx >= 0:
                self.assignment_combo.setCurrentIndex(idx)
        self._toggle_mode_by_assignment()

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
            self._build_activity_metadata_inputs()
            self._save_activity_metadata()
            self._save_activity_names()
            self.load_rows()
        else:
            QMessageBox.warning(self, "Validación", message)

    def load_rows(self) -> None:
        asignacion_id = self.assignment_combo.currentData()
        trimestre = self.trimester_combo.currentData()
        if not asignacion_id:
            self._clear_table()
            return

        config = self.grade_registration_service.obtener_configuracion_actividades(asignacion_id, int(trimestre))
        self._numero_actividades = int(config.get("numero_actividades", 3))
        self.activities_count_input.setValue(self._numero_actividades)
        self._activity_name_inputs = {
            idx + 1: str(item.get("nombre", "")).strip()
            for idx, item in enumerate(config.get("metadata", []))
            if isinstance(item, dict)
        }
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
                recalculadas.append(
                    self.grade_registration_service.recalcular_fila(
                        fila,
                        self._numero_actividades,
                        usar_logica_basica=self._egb_basic_mode,
                    )
                )
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
        self._save_activity_names()
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
        self._activity_group_columns = []
        for idx in range(1, self._numero_actividades + 1):
            col_act = len(self._table_columns)
            self._table_columns.append((f"actividad_{idx}", f"Actividad {idx}"))
            col_ref = len(self._table_columns)
            self._table_columns.append((f"mejora_{idx}", f"Refuerzo {idx}"))
            self._activity_group_columns.append((idx, col_act, col_ref))
            self._table_columns.append((f"promedio_{idx}", f"Promedio {idx}"))
        self._table_columns.extend(self.SUMMATIVE_COLUMNS_EGB_BASICA if self._egb_basic_mode else self.SUMMATIVE_COLUMNS)
        self.table.setColumnCount(len(self._table_columns))
        self.table.setHorizontalHeaderLabels([self._format_header_label(title) for _, title in self._table_columns])

    def _fill_table(self, rows: list[dict]) -> None:
        self._clear_table()
        self._setup_columns()
        self._insert_activity_name_row()
        self._fila_meta = rows
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, (field, _) in enumerate(self._table_columns):
                value = row_data.get(field)
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                if field.startswith("promedio_") or field in {"estudiante", "nota_trimestral", "cualitativo", "cualitativo_adicional"}:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self._apply_item_colors(item, field, value)
                self.table.setItem(row, col, item)
        self._apply_column_resize_policy()

    def _collect_rows_from_table(self) -> list[dict]:
        rows: list[dict] = []
        for row_idx in range(1, self.table.rowCount()):
            meta_idx = row_idx - 1
            meta = self._fila_meta[meta_idx] if meta_idx < len(self._fila_meta) else {}
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
        self._build_activity_metadata_inputs()

    def _build_activity_metadata_inputs(self) -> None:
        """Compatibilidad con versiones antiguas de GradesView.

        La UI actual usa nombres de actividad en la fila superior combinada de la tabla,
        por lo que ya no existe un panel separado de metadatos.
        Este método se conserva como no-op para evitar AttributeError si queda una
        llamada obsoleta en entornos que aún cargan código previo.
        """
        return

    def refresh_data(self) -> None:
        selected_assignment_id = self.assignment_combo.currentData()
        self.load_contexts(selected_assignment_id=selected_assignment_id)
        if self.accompaniment_view is not None:
            self.accompaniment_view.refresh_data()

    @staticmethod
    def _format_header_label(title: str) -> str:
        words = title.split()
        if len(words) <= 2:
            return title
        split_index = len(words) // 2
        return f"{' '.join(words[:split_index])}\n{' '.join(words[split_index:])}"

    @staticmethod
    def _is_numeric_field(field: str) -> bool:
        return (
            field.startswith("actividad_")
            or field.startswith("mejora_")
            or field.startswith("promedio_")
            or field in {"proyecto", "evaluacion", "refuerzo", "mejora_sumativa", "nota_trimestral"}
        )

    def _apply_item_colors(self, item: QTableWidgetItem, field: str, value: object) -> None:
        if field.startswith("promedio_") or field in {"promedio_evaluacion_sumativa", "promedio_formativo", "promedio_formativo_70", "promedio_sumativo_30", "nota_trimestral"}:
            item.setBackground(QColor("#B7E6A7"))
        if field in {"cualitativo", "cualitativo_adicional"}:
            item.setBackground(QColor("#FFE6FF"))

        try:
            numeric_value = float(value) if value is not None and str(value).strip() != "" else None
        except (TypeError, ValueError):
            numeric_value = None
        if field in {"promedio_formativo_70", "promedio_sumativo_30"}:
            item.setForeground(QColor("#000000"))
            return
        if numeric_value is not None and numeric_value < 7:
            item.setForeground(QColor("#FF0000"))

    def eventFilter(self, obj, event):  # type: ignore[override]
        if obj is self.table and event.type() == QEvent.KeyPress:
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
                self._copy_selected_cells()
                return True
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
                self._paste_from_clipboard()
                return True
        return super().eventFilter(obj, event)

    def _copy_selected_cells(self) -> None:
        ranges = self.table.selectedRanges()
        if not ranges:
            return
        selected_range = ranges[0]
        lines: list[str] = []
        for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
            cells: list[str] = []
            for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                item = self.table.item(row, col)
                cells.append(item.text() if item else "")
            lines.append("\t".join(cells))
        QApplication.clipboard().setText("\n".join(lines))

    def _paste_from_clipboard(self) -> None:
        text = QApplication.clipboard().text()
        if not text.strip():
            return
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        if current_row < 0 or current_col < 0:
            return
        if current_row == 0:
            return

        touched_rows: set[int] = set()
        rows = [line.split("\t") for line in text.splitlines()]
        for row_offset, values in enumerate(rows):
            target_row = current_row + row_offset
            if target_row >= self.table.rowCount():
                break
            for col_offset, value in enumerate(values):
                target_col = current_col + col_offset
                if target_col >= self.table.columnCount():
                    break
                item = self.table.item(target_row, target_col)
                if item is None:
                    item = QTableWidgetItem("")
                    self.table.setItem(target_row, target_col, item)
                if item.flags() & Qt.ItemIsEditable:
                    field = self._table_columns[target_col][0] if target_col < len(self._table_columns) else ""
                    item.setText(self._normalize_clipboard_value(value, field))
                    touched_rows.add(target_row)
        self._recalculate_rows_in_table(sorted(touched_rows))

    def _on_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_calculations:
            return
        row = item.row()
        if row <= 0 or row >= self.table.rowCount():
            return
        if item.column() >= len(self._table_columns):
            return
        field = self._table_columns[item.column()][0]
        if field in {"estudiante", "cualitativo", "cualitativo_adicional"}:
            return
        self._recalculate_rows_in_table([row])

    def _recalculate_rows_in_table(self, rows: list[int]) -> None:
        valid_rows = [r for r in rows if 1 <= r < self.table.rowCount()]
        if not valid_rows:
            return
        self._updating_calculations = True
        try:
            row_data = self._collect_rows_from_table()
            for row in valid_rows:
                idx = row - 1
                recalculada = self.grade_registration_service.recalcular_fila(
                    row_data[idx],
                    self._numero_actividades,
                    usar_logica_basica=self._egb_basic_mode,
                )
                for col, (field, _) in enumerate(self._table_columns):
                    value = recalculada.get(field)
                    text = "" if value is None else str(value)
                    item = self.table.item(row, col)
                    if item is None:
                        item = QTableWidgetItem("")
                        self.table.setItem(row, col, item)
                    item.setText(text)
                    if field.startswith("promedio_") or field in {"estudiante", "nota_trimestral", "cualitativo", "cualitativo_adicional"}:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self._apply_item_colors(item, field, value)
        finally:
            self._updating_calculations = False

    def _normalize_clipboard_value(self, value: str, field: str) -> str:
        text = str(value).strip()
        if not text:
            return ""
        if not self._is_numeric_field(field):
            return text

        normalized = text.replace(",", ".")
        try:
            number = float(normalized)
        except ValueError:
            return text
        formatted = f"{number:.2f}".rstrip("0").rstrip(".")
        return formatted

    def _insert_activity_name_row(self) -> None:
        self.table.insertRow(0)
        header_bg = QColor("#EAF2FF")
        for col in range(self.table.columnCount()):
            item = QTableWidgetItem("")
            item.setBackground(header_bg)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(0, col, item)
        for activity_idx, col_act, col_ref in self._activity_group_columns:
            self.table.setSpan(0, col_act, 1, 2)
            name_value = self._activity_name_inputs.get(activity_idx, "")
            text = name_value or f"Nombre actividad {activity_idx}"
            name_item = QTableWidgetItem(text)
            name_item.setBackground(header_bg)
            self.table.setItem(0, col_act, name_item)

    def _read_activity_names_from_header(self) -> dict[int, str]:
        names: dict[int, str] = {}
        if self.table.rowCount() == 0:
            return names
        for activity_idx, col_act, _ in self._activity_group_columns:
            item = self.table.item(0, col_act)
            text = item.text().strip() if item else ""
            if text.lower().startswith("nombre actividad "):
                text = ""
            names[activity_idx] = text
        return names

    def _save_activity_names(self) -> None:
        asignacion_id = self.assignment_combo.currentData()
        trimestre = self.trimester_combo.currentData()
        if not asignacion_id or not trimestre:
            return
        self._activity_name_inputs = self._read_activity_names_from_header()
        metadata = [
            {
                "nombre": self._activity_name_inputs.get(idx, ""),
                "fecha_actividad": "",
                "fecha_refuerzo": "",
            }
            for idx in range(1, self._numero_actividades + 1)
        ]
        self.grade_registration_service.guardar_configuracion_actividades(
            str(asignacion_id),
            int(trimestre),
            metadata,
        )

    def _apply_column_resize_policy(self) -> None:
        self.table.resizeColumnToContents(0)
        self.table.setColumnWidth(0, max(self.table.columnWidth(0), 220))
        for _, col_act, col_ref in self._activity_group_columns:
            self.table.setColumnWidth(col_act, max(90, self.table.columnWidth(col_act)))
            self.table.setColumnWidth(col_ref, max(90, self.table.columnWidth(col_ref)))

    def _on_assignment_or_trimester_changed(self) -> None:
        if self._switching_mode:
            return
        self._toggle_mode_by_assignment()

    def _toggle_mode_by_assignment(self) -> None:
        if self._switching_mode:
            return
        self._switching_mode = True
        try:
            selected_assignment = self.assignment_combo.currentData()
            assignment = next((row for row in self._contextos if row.get("id_asignacion") == selected_assignment), None)
            subject_name = self._normalize_subject_name(str((assignment or {}).get("asignatura_nombre") or ""))
            use_accompaniment = (
                self.accompaniment_view is not None and subject_name in {
                    self._normalize_subject_name(self.ACCOMPANIMENT_SUBJECT_NAME),
                    self._normalize_subject_name(self.BEHAVIOR_SUBJECT_NAME),
                }
            )
            use_animation_reading = (
                self.animation_reading_view is not None
                and subject_name == self._normalize_subject_name(self.ANIMATION_READING_SUBJECT_NAME)
            )
            use_vocational_orientation = (
                self.vocational_orientation_view is not None
                and self._is_vocational_orientation_subject(subject_name)
            )
            if use_animation_reading:
                self._show_animation_reading_view()
                self._sync_animation_reading_view()
            elif use_vocational_orientation:
                self._show_vocational_orientation_view()
                self._sync_vocational_orientation_view()
            elif use_accompaniment:
                self._show_accompaniment_view()
                if self.accompaniment_view is not None:
                    variant = (
                        "behavior"
                        if subject_name == self._normalize_subject_name(self.BEHAVIOR_SUBJECT_NAME)
                        else "accompaniment"
                    )
                    self.accompaniment_view.set_evaluation_variant(variant)
                self._sync_accompaniment_view()
            else:
                self._show_quantitative_view()
                self._egb_basic_mode = bool(
                    selected_assignment
                    and self.grade_registration_service.usar_logica_cuantitativa_basica(str(selected_assignment))
                )
                self.load_rows()
        finally:
            self._switching_mode = False

    def _show_quantitative_view(self) -> None:
        self._accompaniment_mode = False
        self._animation_reading_mode = False
        self._vocational_orientation_mode = False
        for w in (self.activities_count_label, self.activities_count_input, self.generate_activities_button, self.save_button):
            w.setVisible(True)
        self.load_button.setVisible(False)
        self.recalc_button.setVisible(False)
        self.table.setVisible(True)
        if self.accompaniment_view is not None:
            self.accompaniment_view.setVisible(False)
        if self.animation_reading_view is not None:
            self.animation_reading_view.setVisible(False)
        if self.vocational_orientation_view is not None:
            self.vocational_orientation_view.setVisible(False)

    def _show_accompaniment_view(self) -> None:
        self._accompaniment_mode = True
        self._animation_reading_mode = False
        self._vocational_orientation_mode = False
        for w in (
            self.activities_count_label,
            self.activities_count_input,
            self.generate_activities_button,
            self.load_button,
            self.recalc_button,
            self.save_button,
        ):
            w.setVisible(False)
        self.table.setVisible(False)
        if self.accompaniment_view is not None:
            self.accompaniment_view.setVisible(True)
        if self.animation_reading_view is not None:
            self.animation_reading_view.setVisible(False)
        if self.vocational_orientation_view is not None:
            self.vocational_orientation_view.setVisible(False)

    def _show_animation_reading_view(self) -> None:
        self._accompaniment_mode = False
        self._animation_reading_mode = True
        self._vocational_orientation_mode = False
        for w in (
            self.activities_count_label,
            self.activities_count_input,
            self.generate_activities_button,
            self.load_button,
            self.recalc_button,
            self.save_button,
        ):
            w.setVisible(False)
        self.table.setVisible(False)
        if self.accompaniment_view is not None:
            self.accompaniment_view.setVisible(False)
        if self.animation_reading_view is not None:
            self.animation_reading_view.setVisible(True)
        if self.vocational_orientation_view is not None:
            self.vocational_orientation_view.setVisible(False)

    def _show_vocational_orientation_view(self) -> None:
        self._accompaniment_mode = False
        self._animation_reading_mode = False
        self._vocational_orientation_mode = True
        for w in (
            self.activities_count_label,
            self.activities_count_input,
            self.generate_activities_button,
            self.load_button,
            self.recalc_button,
            self.save_button,
        ):
            w.setVisible(False)
        self.table.setVisible(False)
        if self.accompaniment_view is not None:
            self.accompaniment_view.setVisible(False)
        if self.animation_reading_view is not None:
            self.animation_reading_view.setVisible(False)
        if self.vocational_orientation_view is not None:
            self.vocational_orientation_view.setVisible(True)

    def _sync_accompaniment_view(self) -> None:
        if self.accompaniment_view is None:
            return
        assignment_id = self.assignment_combo.currentData()
        trimester = self.trimester_combo.currentData()
        if assignment_id:
            idx = self.accompaniment_view.assignment_combo.findData(assignment_id)
            if idx >= 0:
                self.accompaniment_view.assignment_combo.setCurrentIndex(idx)
        if trimester:
            idx = self.accompaniment_view.trimester_combo.findData(int(trimester))
            if idx >= 0:
                self.accompaniment_view.trimester_combo.setCurrentIndex(idx)
        self.accompaniment_view.load_rows()

    def _sync_animation_reading_view(self) -> None:
        if self.animation_reading_view is None:
            return
        assignment_id = self.assignment_combo.currentData()
        trimester = self.trimester_combo.currentData()
        assignment_label = self.assignment_combo.currentText()
        trimester_label = self.trimester_combo.currentText()
        self.animation_reading_view.set_context(
            assignment_id=str(assignment_id) if assignment_id else None,
            assignment_label=assignment_label,
            trimester_num=int(trimester) if trimester is not None else None,
            trimester_label=trimester_label,
        )
        students: list[dict[str, str]] = []
        selected_level: str | None = None
        if self.animation_reading_view.level_combo.currentData():
            selected_level = str(self.animation_reading_view.level_combo.currentData())

        if assignment_id and trimester:
            try:
                rows = self.grade_registration_service.obtener_animacion_lectura_evaluacion(
                    str(assignment_id),
                    int(trimester),
                    nivel=selected_level,
                )
                if rows:
                    detected_level = str(rows[0].get("nivel") or "") if rows else None
                    selected_level = selected_level or detected_level
                    students = [
                        {
                            "estudiante_id": str(row.get("estudiante_id") or ""),
                            "estudiante": str(row.get("estudiante") or ""),
                            "notas_indicadores": row.get("notas_indicadores") or [],
                            "valor": row.get("valor"),
                            "cualitativo": str(row.get("cualitativo") or ""),
                            "cualitativo_1": str(row.get("cualitativo_1") or ""),
                        }
                        for row in rows
                    ]
                else:
                    fallback_rows = self.grade_registration_service.cargar_registro(str(assignment_id), int(trimester))
                    students = [
                        {
                            "estudiante_id": str(row.get("estudiante_id") or ""),
                            "estudiante": str(row.get("estudiante") or ""),
                        }
                        for row in fallback_rows
                    ]
            except ValueError:
                students = []
        self.animation_reading_view.set_students(students, selected_level=selected_level)

    def _save_animation_reading_payload(self, payload: dict) -> tuple[bool, str]:
        ok, message = self.grade_registration_service.guardar_animacion_lectura_evaluacion(payload)
        if ok and self.app_signals:
            self.app_signals.data_changed.emit("grades")
        return ok, message

    def _on_animation_level_changed(self) -> None:
        if not self._animation_reading_mode or self._switching_mode:
            return
        self._sync_animation_reading_view()

    def _sync_vocational_orientation_view(self) -> None:
        if self.vocational_orientation_view is None:
            return
        assignment_id = self.assignment_combo.currentData()
        trimester = self.trimester_combo.currentData()
        assignment = next((row for row in self._contextos if row.get("id_asignacion") == assignment_id), None)
        course_name = str((assignment or {}).get("curso_nombre") or "")
        self.vocational_orientation_view.set_context(
            assignment_id=str(assignment_id) if assignment_id else None,
            trimester_num=int(trimester) if trimester is not None else None,
            course_name=course_name,
        )

        if assignment_id and trimester:
            valid_course, course_key, _ = self.grade_registration_service.validar_curso_orientacion_vocacional(str(assignment_id))
            if not valid_course or course_key is None:
                QMessageBox.warning(
                    self,
                    "Validación",
                    "Orientación Vocacional y Profesional solo corresponde a 8vo, 9no y 10mo de EGB.",
                )
                self.vocational_orientation_view.set_students([])
                return

            saved_rows = self.grade_registration_service.obtener_orientacion_vocacional_evaluacion(
                str(assignment_id),
                int(trimester),
            )
            if saved_rows:
                students = [
                    {
                        "estudiante_id": str(row.get("estudiante_id") or ""),
                        "estudiante": str(row.get("estudiante") or ""),
                    }
                    for row in saved_rows
                ]
            else:
                students = [
                    {
                        "estudiante_id": str(row.get("estudiante_id") or ""),
                        "estudiante": str(row.get("estudiante") or ""),
                    }
                    for row in self.grade_registration_service.cargar_registro(str(assignment_id), int(trimester))
                ]
            self.vocational_orientation_view.set_students(students, saved_rows=saved_rows)
            return
        self.vocational_orientation_view.set_students([])

    def _save_vocational_orientation_payload(self, payload: dict) -> tuple[bool, str]:
        ok, message = self.grade_registration_service.guardar_orientacion_vocacional_evaluacion(payload)
        if ok and self.app_signals:
            self.app_signals.data_changed.emit("grades")
        return ok, message

    @staticmethod
    def _normalize_subject_name(value: str) -> str:
        normalized = unicodedata.normalize("NFD", value.strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())

    def _is_vocational_orientation_subject(self, normalized_subject_name: str) -> bool:
        if normalized_subject_name == self._normalize_subject_name(self.VOCATIONAL_ORIENTATION_SUBJECT_NAME):
            return True
        return normalized_subject_name in {
            "orientacion vocacional profesional",
        }
