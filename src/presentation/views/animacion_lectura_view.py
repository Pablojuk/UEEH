"""Vista especial de evaluación para la materia Animación a la Lectura."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class CriterioEvaluacion:
    titulo: str
    indicadores: list[str]


class NotaDelegate(QStyledItemDelegate):
    """Restringe la edición de notas entre 0 y 10."""

    def createEditor(self, parent, option, index):  # type: ignore[override]
        editor = QDoubleSpinBox(parent)
        editor.setRange(0.0, 10.0)
        editor.setDecimals(2)
        editor.setSingleStep(0.1)
        editor.setButtonSymbols(QDoubleSpinBox.NoButtons)
        editor.setFrame(False)
        return editor


class AnimacionLecturaView(QWidget):
    LEVEL_OPTIONS = [
        ("Básica Elemental", "elemental"),
        ("Básica Media", "media"),
        ("Básica Superior", "superior"),
    ]

    DATOS_EVALUACION: dict[str, list[CriterioEvaluacion]] = {
        "elemental": [
            CriterioEvaluacion(
                titulo="Diversidad de géneros literarios y comprensión durante/poslectura.",
                indicadores=[
                    "Lee y escucha diversos géneros literarios durante los espacios de animación lectora.",
                    "Durante y después de la lectura pone en práctica habilidades para comprender ideas principales y secundarias.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Relación de la información con su cotidianidad.",
                indicadores=[
                    "Es capaz de relacionar la información leída con su experiencia personal y el entorno cotidiano.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Identificación del significado de conceptos y vocabulario.",
                indicadores=[
                    "Utiliza el contexto y otros recursos para identificar el significado de palabras, conceptos y expresiones.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Participación en ejercicios de lectura y construcción de gusto lector.",
                indicadores=[
                    "Participa activamente en ejercicios de lectura.",
                    "Es capaz de empezar a construir un gusto personal al elegir textos de su interés.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Expresión oral y escrita de opiniones sobre textos.",
                indicadores=[
                    "Es capaz de expresar de forma oral sus opiniones sobre lo leído.",
                    "Es capaz de expresar de forma escrita sus opiniones sobre lo leído.",
                ],
            ),
        ],
        "media": [
            CriterioEvaluacion(
                titulo="Expresión de emociones y sentimientos en torno a la lectura.",
                indicadores=[
                    "Muestra seguridad al expresar sus emociones y sentimientos durante actividades lectoras.",
                    "Demuestra empatía y comprensión hacia sus pares.",
                    "Evidencia en comentarios conexión emocional con los textos.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Lectura fluida, comprensión y expresividad.",
                indicadores=[
                    "Lee con fluidez y entonación adecuada.",
                    "Demuestra comprensión y la expresa durante la lectura en voz alta.",
                    "Relaciona el lenguaje verbal y no verbal a través de la lectura.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Reconocimiento y expresión de opiniones sobre la narrativa.",
                indicadores=[
                    "Reconoce y expresa su opinión sobre el punto de vista del autor.",
                    "Desarrolla la conciencia narrativa y la capacidad de organizar sucesos.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Conocimientos lingüísticos y estrategias cognitivas.",
                indicadores=[
                    "Aplica sus conocimientos lingüísticos para comprender el contenido literal.",
                    "Aplica sus conocimientos lingüísticos para generar inferencias.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Gusto personal, selección activa y recomendación de textos.",
                indicadores=[
                    "Refleja un gusto personal y una selección activa de textos.",
                    "Lee en distintos momentos, lugares y formatos.",
                    "Es capaz de recordar las lecturas que más le gustaron.",
                    "Es capaz de recomendar textos a sus compañeras y compañeros.",
                ],
            ),
        ],
        "superior": [
            CriterioEvaluacion(
                titulo="Desarrollo de preferencias, gustos e intereses lectores.",
                indicadores=[
                    "Conoce y es capaz de describir sus propias preferencias lectoras.",
                    "Aplica criterios para seleccionar textos para el ocio.",
                    "Aplica criterios para seleccionar textos para la investigación.",
                    "Aplica criterios para seleccionar textos para la reflexión.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Uso de la lectura para ampliar conocimiento.",
                indicadores=[
                    "Utiliza la lectura para conocer cualquier temática de interés.",
                    "Utiliza la lectura para satisfacer necesidades de conocimiento académico.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Desempeño en comprensión lectora literal, inferencial y crítica.",
                indicadores=[
                    "Demuestra mejora en interpretación literal.",
                    "Demuestra mejora en interpretación inferencial.",
                    "Demuestra mejora en el desarrollo de una postura crítica.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Participación en escritura y expresión oral sobre problemáticas.",
                indicadores=[
                    "Participa en escritura creativa para problemáticas personales.",
                    "Participa en escritura creativa para problemáticas de su comunidad.",
                    "Participa en expresión oral para problemáticas personales.",
                    "Participa en expresión oral para problemáticas de su comunidad.",
                ],
            ),
            CriterioEvaluacion(
                titulo="Interés, comprensión integral e interpretación personal del texto.",
                indicadores=[
                    "Demuestra interés por el texto mediante preguntas o comentarios.",
                    "Logra una comprensión integral de lo leído.",
                    "Demuestra el desarrollo de una interpretación personal.",
                    "Fortalece su frecuencia de lectura.",
                ],
            ),
        ],
    }

    def __init__(
        self,
        list_signers: Callable[[], list[str]] | None = None,
        on_save_payload: Callable[[dict[str, Any]], tuple[bool, str]] | None = None,
    ) -> None:
        super().__init__()
        self._list_signers = list_signers
        self._on_save_payload = on_save_payload

        self._students: list[dict[str, str]] = []
        self._syncing_scroll = False
        self._updating_cells = False
        self._assignment_id: str | None = None
        self._trimester_num: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        self.context_card = QFrame()
        self.context_card.setObjectName("Card")
        context_layout = QHBoxLayout(self.context_card)
        self.assignment_value = QLabel("-")
        self.trimester_value = QLabel("-")
        context_layout.addWidget(QLabel("Asignación"))
        context_layout.addWidget(self.assignment_value, 1)
        context_layout.addWidget(QLabel("Trimestre"))
        context_layout.addWidget(self.trimester_value)

        self.actions_card = QFrame()
        self.actions_card.setObjectName("Card")
        actions_layout = QHBoxLayout(self.actions_card)
        self.save_button = QPushButton("Guardar evaluación")
        self.save_button.clicked.connect(self._save_rows)
        self.level_combo = QComboBox()
        self.level_combo.addItem("Seleccione nivel", "")
        for label, value in self.LEVEL_OPTIONS:
            self.level_combo.addItem(label, value)
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)
        self.preview_button = QPushButton("Vista Previa")
        self.preview_button.clicked.connect(lambda: self._show_placeholder("Vista Previa"))
        self.export_pdf_button = QPushButton("Exportar PDF")
        self.export_pdf_button.clicked.connect(lambda: self._show_placeholder("Exportar PDF"))
        self.export_excel_button = QPushButton("Exportar Excel")
        self.export_excel_button.clicked.connect(lambda: self._show_placeholder("Exportar Excel"))

        actions_layout.addWidget(self.save_button)
        actions_layout.addWidget(self.level_combo)
        actions_layout.addWidget(self.preview_button)
        actions_layout.addWidget(self.export_pdf_button)
        actions_layout.addWidget(self.export_excel_button)
        actions_layout.addStretch(1)

        self.sign_card = QGroupBox("Firmantes del reporte")
        sign_layout = QHBoxLayout(self.sign_card)
        self.sign_docente_combo = QComboBox()
        self.sign_rector_combo = QComboBox()
        sign_layout.addWidget(QLabel("Docente"))
        sign_layout.addWidget(self.sign_docente_combo, 1)
        sign_layout.addWidget(QLabel("Rector"))
        sign_layout.addWidget(self.sign_rector_combo, 1)

        tables_row = QHBoxLayout()
        tables_row.setSpacing(0)

        self.left_table = QTableWidget(0, 2)
        self.center_table = QTableWidget(0, 0)
        self.right_table = QTableWidget(0, 3)

        self._setup_table(self.left_table, editable=False)
        self._setup_table(self.center_table, editable=True)
        self._setup_table(self.right_table, editable=False)

        self.left_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.right_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.center_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.center_table.setItemDelegate(NotaDelegate(self.center_table))
        self.center_table.itemChanged.connect(self._on_grade_item_changed)

        tables_row.addWidget(self.left_table)
        tables_row.addWidget(self.center_table, 1)
        tables_row.addWidget(self.right_table)

        root.addWidget(self.context_card)
        root.addWidget(self.actions_card)
        root.addWidget(self.sign_card)
        root.addLayout(tables_row, 1)

        self._connect_scrollbars()
        self._load_signers()
        self._apply_styles()

    def set_context(self, assignment_id: str | None, assignment_label: str, trimester_num: int | None, trimester_label: str) -> None:
        self._assignment_id = assignment_id
        self._trimester_num = trimester_num
        self.assignment_value.setText(assignment_label or "-")
        self.trimester_value.setText(trimester_label or "-")

    def set_students(self, students: list[dict[str, str]]) -> None:
        self._students = students
        self._build_tables()

    def _setup_table(self, table: QTableWidget, editable: bool) -> None:
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectItems)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setAlternatingRowColors(False)
        table.setWordWrap(True)
        table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed if editable else QAbstractItemView.NoEditTriggers)

    def _connect_scrollbars(self) -> None:
        for table in (self.left_table, self.center_table, self.right_table):
            table.verticalScrollBar().valueChanged.connect(self._sync_vertical_scroll)

    def _sync_vertical_scroll(self, value: int) -> None:
        if self._syncing_scroll:
            return
        self._syncing_scroll = True
        try:
            sender = self.sender()
            for table in (self.left_table, self.center_table, self.right_table):
                bar = table.verticalScrollBar()
                if bar is not sender:
                    bar.setValue(value)
        finally:
            self._syncing_scroll = False

    def _on_level_changed(self) -> None:
        self._build_tables()

    def _build_tables(self) -> None:
        level_key = self.level_combo.currentData()
        criterios = self.DATOS_EVALUACION.get(level_key, []) if level_key else []
        indicator_count = sum(len(c.indicadores) for c in criterios)
        total_rows = 3 + len(self._students)

        self.left_table.clearSpans()
        self.center_table.clearSpans()
        self.right_table.clearSpans()

        self.left_table.setRowCount(total_rows)
        self.left_table.setColumnCount(2)
        self.center_table.setRowCount(total_rows)
        self.center_table.setColumnCount(indicator_count)
        self.right_table.setRowCount(total_rows)
        self.right_table.setColumnCount(3)

        self._populate_headers(criterios, indicator_count)
        self._populate_students(criterios, indicator_count)
        self._apply_dimensions(criterios, indicator_count)

    def _populate_headers(self, criterios: list[CriterioEvaluacion], indicator_count: int) -> None:
        self._set_header_item(self.left_table, 0, 0, "N°", "left")
        self.left_table.setSpan(0, 0, 3, 1)
        self._set_header_item(self.left_table, 0, 1, "Estudiante", "left")
        self.left_table.setSpan(0, 1, 3, 1)

        if indicator_count > 0:
            self._set_header_item(self.center_table, 0, 0, "Criterios e Indicadores de Evaluación", "group")
            self.center_table.setSpan(0, 0, 1, indicator_count)

            col = 0
            for crit_index, criterio in enumerate(criterios, start=1):
                span = len(criterio.indicadores)
                self._set_header_item(
                    self.center_table,
                    1,
                    col,
                    f"Criterio {crit_index}",
                    "criterion",
                    criterio.titulo,
                )
                self.center_table.setSpan(1, col, 1, span)
                for ind_index, indicador in enumerate(criterio.indicadores, start=1):
                    self._set_header_item(
                        self.center_table,
                        2,
                        col,
                        f"Ind. {ind_index}",
                        "indicator",
                        f"Cr. {crit_index} - {indicador}",
                    )
                    col += 1
        else:
            self._set_header_item(self.center_table, 0, 0, "Seleccione nivel", "group")
            self.center_table.setSpan(0, 0, 3, 1)

        self._set_header_item(self.right_table, 0, 0, "VALOR\n(Promedio)", "value")
        self.right_table.setSpan(0, 0, 3, 1)
        self._set_header_item(self.right_table, 0, 1, "CUALITATIVO", "qual")
        self.right_table.setSpan(0, 1, 3, 1)
        self._set_header_item(self.right_table, 0, 2, "CUALITATIVO 1", "qual1")
        self.right_table.setSpan(0, 2, 3, 1)

    def _populate_students(self, criterios: list[CriterioEvaluacion], indicator_count: int) -> None:
        for index, student in enumerate(self._students, start=1):
            row = 2 + index
            self._set_data_item(self.left_table, row, 0, str(index), editable=False)
            self._set_data_item(self.left_table, row, 1, student.get("estudiante", ""), editable=False)
            for col in range(indicator_count):
                self._set_data_item(self.center_table, row, col, "", editable=True)
            self._set_data_item(self.right_table, row, 0, "-", editable=False)
            self._set_data_item(self.right_table, row, 1, "-", editable=False)
            self._set_data_item(self.right_table, row, 2, "-", editable=False)

        self._updating_cells = True
        try:
            for row in range(3):
                for col in range(self.right_table.columnCount()):
                    if self.right_table.item(row, col) is None:
                        self._set_header_item(self.right_table, row, col, "", "value")
        finally:
            self._updating_cells = False

    def _apply_dimensions(self, criterios: list[CriterioEvaluacion], indicator_count: int) -> None:
        self.left_table.setColumnWidth(0, 40)
        self.left_table.setColumnWidth(1, 280)
        for col in range(indicator_count):
            self.center_table.setColumnWidth(col, 110)
        self.right_table.setColumnWidth(0, 110)
        self.right_table.setColumnWidth(1, 100)
        self.right_table.setColumnWidth(2, 90)

        total_rows = self.left_table.rowCount()
        for row in range(total_rows):
            height = 36 if row < 3 else 32
            self.left_table.setRowHeight(row, height)
            self.center_table.setRowHeight(row, height)
            self.right_table.setRowHeight(row, height)

    def _on_grade_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_cells:
            return
        row = item.row()
        if row < 3:
            return
        self._recalculate_row(row)

    def _recalculate_row(self, row: int) -> None:
        if self.center_table.columnCount() == 0:
            return

        values: list[float] = []
        invalid_found = False

        self._updating_cells = True
        try:
            for col in range(self.center_table.columnCount()):
                cell = self.center_table.item(row, col)
                if cell is None:
                    continue
                text = cell.text().strip().replace(",", ".")
                if not text:
                    cell.setBackground(QColor("#FFFFFF"))
                    continue
                try:
                    value = float(text)
                except ValueError:
                    invalid_found = True
                    cell.setBackground(QColor("#FEE2E2"))
                    cell.setToolTip("Ingrese una nota numérica entre 0 y 10")
                    continue

                if value < 0 or value > 10:
                    invalid_found = True
                    cell.setBackground(QColor("#FEE2E2"))
                    cell.setToolTip("La nota debe estar entre 0 y 10")
                    continue

                values.append(value)
                cell.setBackground(QColor("#FFFFFF"))
                cell.setToolTip("")

            if not values:
                self._set_result_values(row, "-", "-", "-")
                return

            promedio = sum(values) / len(values)
            cualitativo = self._to_cualitativo(promedio)
            cualitativo_1 = cualitativo[0]
            self._set_result_values(row, f"{promedio:.2f}", cualitativo, cualitativo_1)

            if invalid_found:
                msg = "Existen notas inválidas en esta fila; no se incluirán en el promedio ni en el guardado."
                current_tip = self.right_table.item(row, 0).toolTip() if self.right_table.item(row, 0) else ""
                if msg not in current_tip:
                    self.right_table.item(row, 0).setToolTip(msg)
            else:
                self.right_table.item(row, 0).setToolTip("")
        finally:
            self._updating_cells = False

    def _set_result_values(self, row: int, promedio: str, cualitativo: str, cualitativo_1: str) -> None:
        value_item = self.right_table.item(row, 0)
        qual_item = self.right_table.item(row, 1)
        qual1_item = self.right_table.item(row, 2)
        if value_item is None or qual_item is None or qual1_item is None:
            return

        value_item.setText(promedio)
        qual_item.setText(cualitativo)
        qual1_item.setText(cualitativo_1)

        color = QColor("#1F2937")
        if cualitativo_1 in {"A", "B"}:
            color = QColor("#047857")
        elif cualitativo_1 == "C":
            color = QColor("#1D4ED8")
        elif cualitativo_1 in {"D", "E"}:
            color = QColor("#B91C1C")

        for item in (value_item, qual_item, qual1_item):
            item.setForeground(color)

    def _to_cualitativo(self, promedio: float) -> str:
        rounded = round(promedio)
        if rounded >= 10:
            return "A+"
        if rounded == 9:
            return "A-"
        if rounded == 8:
            return "B+"
        if rounded == 7:
            return "B-"
        if rounded == 6:
            return "C+"
        if rounded == 5:
            return "C-"
        if rounded == 4:
            return "D+"
        if rounded == 3:
            return "D-"
        if rounded == 2:
            return "E+"
        return "E-"

    def build_save_payload(self) -> dict[str, Any]:
        level_key = self.level_combo.currentData()
        indicadores_total = self.center_table.columnCount()
        result_rows: list[dict[str, Any]] = []
        has_invalid = False

        for idx, student in enumerate(self._students, start=1):
            row = 2 + idx
            notas: list[float | None] = []
            for col in range(indicadores_total):
                item = self.center_table.item(row, col)
                text = item.text().strip().replace(",", ".") if item else ""
                if not text:
                    notas.append(None)
                    continue
                try:
                    value = float(text)
                except ValueError:
                    notas.append(None)
                    has_invalid = True
                    continue
                if value < 0 or value > 10:
                    notas.append(None)
                    has_invalid = True
                    continue
                notas.append(value)

            promedio = self.right_table.item(row, 0).text() if self.right_table.item(row, 0) else "-"
            cualitativo = self.right_table.item(row, 1).text() if self.right_table.item(row, 1) else "-"
            cualitativo_1 = self.right_table.item(row, 2).text() if self.right_table.item(row, 2) else "-"
            result_rows.append(
                {
                    "estudiante_id": student.get("estudiante_id"),
                    "estudiante": student.get("estudiante"),
                    "notas_indicadores": notas,
                    "promedio": None if promedio == "-" else float(promedio),
                    "cualitativo": None if cualitativo == "-" else cualitativo,
                    "cualitativo_1": None if cualitativo_1 == "-" else cualitativo_1,
                }
            )

        return {
            "asignacion_id": self._assignment_id,
            "trimestre_num": self._trimester_num,
            "nivel": level_key,
            "firmantes": {
                "docente": self.sign_docente_combo.currentText().strip(),
                "rector": self.sign_rector_combo.currentText().strip(),
            },
            "filas": result_rows,
            "has_invalid_notes": has_invalid,
        }

    def _save_rows(self) -> None:
        payload = self.build_save_payload()
        if not payload["asignacion_id"] or not payload["trimestre_num"]:
            QMessageBox.warning(self, "Validación", "Seleccione una asignación y trimestre.")
            return
        if not payload["nivel"]:
            QMessageBox.warning(self, "Validación", "Seleccione un nivel educativo.")
            return
        if payload["has_invalid_notes"]:
            QMessageBox.warning(self, "Validación", "Existen notas inválidas (fuera de 0-10). Corrija antes de guardar.")
            return

        if self._on_save_payload is None:
            QMessageBox.information(
                self,
                "Pendiente",
                "La persistencia de Animación a la Lectura está preparada en payload, pero aún no existe el caso de uso en aplicación.",
            )
            return

        ok, message = self._on_save_payload(payload)
        if ok:
            QMessageBox.information(self, "Éxito", message)
        else:
            QMessageBox.warning(self, "Error", message)

    def _show_placeholder(self, action_name: str) -> None:
        QMessageBox.information(
            self,
            "Pendiente",
            f"{action_name} para Animación a la Lectura está preparado para integración con el servicio de reportes.",
        )

    def _set_header_item(
        self,
        table: QTableWidget,
        row: int,
        col: int,
        text: str,
        role: str,
        tooltip: str = "",
    ) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        if tooltip:
            item.setToolTip(tooltip)

        if role == "group":
            item.setBackground(QColor("#1D4ED8"))
            item.setForeground(QColor("#FFFFFF"))
        elif role == "criterion":
            item.setBackground(QColor("#EFF6FF"))
            item.setForeground(QColor("#1E3A8A"))
        elif role == "indicator":
            item.setBackground(QColor("#FFFFFF"))
            item.setForeground(QColor("#334155"))
        elif role == "left":
            item.setBackground(QColor("#E2E8F0"))
            item.setForeground(QColor("#334155"))
        elif role == "value":
            item.setBackground(QColor("#D1FAE5"))
            item.setForeground(QColor("#065F46"))
        elif role == "qual":
            item.setBackground(QColor("#DBEAFE"))
            item.setForeground(QColor("#1E40AF"))
        elif role == "qual1":
            item.setBackground(QColor("#E0E7FF"))
            item.setForeground(QColor("#3730A3"))

        table.setItem(row, col, item)

    def _set_data_item(self, table: QTableWidget, row: int, col: int, text: str, editable: bool) -> None:
        item = QTableWidgetItem(text)
        flags = item.flags()
        if not editable:
            flags = flags & ~Qt.ItemIsEditable
        item.setFlags(flags)
        item.setTextAlignment(Qt.AlignCenter if col != 1 else Qt.AlignLeft | Qt.AlignVCenter)
        if table is self.right_table:
            if col == 0:
                item.setBackground(QColor("#ECFDF5"))
            elif col == 1:
                item.setBackground(QColor("#EFF6FF"))
            else:
                item.setBackground(QColor("#EEF2FF"))
        table.setItem(row, col, item)

    def _load_signers(self) -> None:
        self.sign_docente_combo.clear()
        self.sign_rector_combo.clear()
        self.sign_docente_combo.addItem("", "")
        self.sign_rector_combo.addItem("", "")
        if self._list_signers is None:
            return
        for signer in self._list_signers():
            self.sign_docente_combo.addItem(signer, signer)
            self.sign_rector_combo.addItem(signer, signer)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QGroupBox {
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: 600;
                background: #FFFFFF;
            }
            QGroupBox::title {
                left: 10px;
                padding: 0 4px;
            }
            QPushButton {
                background-color: #1F4E79;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2E75B6;
            }
            QComboBox {
                min-width: 160px;
                padding: 5px 8px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background: #FFFFFF;
            }
            QTableWidget {
                border: 1px solid #CBD5E1;
                background: #FFFFFF;
                gridline-color: #E2E8F0;
                font-size: 12px;
            }
            """
        )
