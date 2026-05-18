"""Vista especial de evaluación para la materia Animación a la Lectura."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import unicodedata
from typing import Any, Callable

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from openpyxl import Workbook

from src.infrastructure.exporters.html_report_renderer import HtmlReportRenderer
from src.presentation.widgets.busy_state import busy_button

try:
    from PySide6.QtCore import QEventLoop, QMarginsF, QUrl
    from PySide6.QtWebEngineCore import QWebEnginePage
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:  # pragma: no cover
    QEventLoop = None
    QMarginsF = None
    QUrl = None
    QWebEnginePage = None
    QWebEngineView = None


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
        get_assignment_context: Callable[[str], dict[str, Any] | None] | None = None,
        get_institution_data: Callable[[], dict[str, Any]] | None = None,
        on_save_payload: Callable[[dict[str, Any]], tuple[bool, str]] | None = None,
    ) -> None:
        super().__init__()
        self._list_signers = list_signers
        self._get_assignment_context = get_assignment_context
        self._get_institution_data = get_institution_data
        self._on_save_payload = on_save_payload

        self._students: list[dict[str, str]] = []
        self._saved_rows_by_student: dict[str, dict[str, Any]] = {}
        self._updating_cells = False
        self._assignment_id: str | None = None
        self._trimester_num: int | None = None
        self._header_details: dict[tuple[int, int], tuple[str, str]] = {}
        self._last_preview_html = ""
        self._notes_mode = False
        self._reports_mode = False
        self._indicator_start_col = 2
        self._indicator_count = 0
        self._result_start_col = 2

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        self.report_filter_card = QFrame()
        self.report_filter_card.setObjectName("Card")
        report_filter_row = QHBoxLayout(self.report_filter_card)
        self.report_assignment_combo = QComboBox()
        self.report_assignment_combo.setMinimumWidth(340)
        self.report_trimester_combo = QComboBox()
        self.report_trimester_combo.addItem("Trimestre 1", 1)
        self.report_trimester_combo.addItem("Trimestre 2", 2)
        self.report_trimester_combo.addItem("Trimestre 3", 3)
        report_filter_row.addWidget(QLabel("Asignación"))
        report_filter_row.addWidget(self.report_assignment_combo, 1)
        report_filter_row.addWidget(QLabel("Trimestre"))
        report_filter_row.addWidget(self.report_trimester_combo)

        self.actions_card = QFrame()
        self.actions_card.setObjectName("Card")
        actions_layout = QHBoxLayout(self.actions_card)
        self.save_button = QPushButton("Guardar evaluación")
        self.save_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.save_button, "Guardando...", self._save_rows)
        )
        self.level_combo = QComboBox()
        self.level_combo.addItem("Seleccione nivel", "")
        for label, value in self.LEVEL_OPTIONS:
            self.level_combo.addItem(label, value)
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)
        self.preview_button = QPushButton("Vista Previa")
        self.preview_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.preview_button, "Generando...", self._show_preview)
        )
        self.export_pdf_button = QPushButton("Exportar PDF")
        self.export_pdf_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.export_pdf_button, "Exportando...", self._export_preview_pdf)
        )
        self.export_excel_button = QPushButton("Exportar Excel")
        self.export_excel_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.export_excel_button, "Exportando...", self._export_preview_excel)
        )

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
        self.sign_docente_combo.currentIndexChanged.connect(self._on_signers_changed)
        self.sign_rector_combo.currentIndexChanged.connect(self._on_signers_changed)

        self.tables_container = QWidget()
        self.tables_container.setObjectName("AnimTableShell")
        tables_row = QHBoxLayout(self.tables_container)
        tables_row.setContentsMargins(0, 0, 0, 0)
        tables_row.setSpacing(0)

        self.matrix_table = QTableWidget(0, 0)
        self.matrix_table.setObjectName("AnimMatrixTable")
        self._setup_table(self.matrix_table, editable=True)
        self.matrix_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.matrix_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.matrix_table.setItemDelegate(NotaDelegate(self.matrix_table))
        self.matrix_table.itemChanged.connect(self._on_grade_item_changed)
        self.matrix_table.cellDoubleClicked.connect(self._on_matrix_header_double_clicked)
        self.matrix_table.cellClicked.connect(self._on_matrix_table_cell_clicked)
        tables_row.addWidget(self.matrix_table, 1)
        # Compatibilidad con pruebas/código existente.
        self.left_table = self.matrix_table
        self.center_table = self.matrix_table
        self.right_table = self.matrix_table

        self.tabs = QTabWidget()
        eval_tab = QWidget()
        eval_layout = QVBoxLayout(eval_tab)
        eval_layout.setContentsMargins(0, 0, 0, 0)
        eval_layout.addWidget(self.tables_container, 1)
        self.tabs.addTab(eval_tab, "Evaluación")

        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        if QWebEngineView is not None:
            self.preview_view = QWebEngineView()
            self._preview_uses_webengine = True
        else:
            self.preview_view = QTextBrowser()
            self.preview_view.setOpenExternalLinks(True)
            self._preview_uses_webengine = False
        preview_layout.addWidget(self.preview_view, 1)
        self.tabs.addTab(preview_tab, "Vista previa")

        root.addWidget(self.report_filter_card)
        root.addWidget(self.actions_card)
        root.addWidget(self.sign_card)
        root.addWidget(self.tabs, 1)

        self._load_signers()
        self._apply_styles()

    def _run_with_busy_state(self, button: QPushButton, busy_text: str, callback) -> None:
        with busy_button(button, busy_text):
            callback()

    def set_context(self, assignment_id: str | None, assignment_label: str, trimester_num: int | None, trimester_label: str) -> None:
        self._assignment_id = assignment_id
        self._trimester_num = trimester_num
        self._apply_default_signers_from_context()

    def set_notes_mode(self, enabled: bool = True) -> None:
        """Modo Notas: registro de calificaciones sin controles de reporte."""
        self._notes_mode = enabled
        self._reports_mode = not enabled
        self.save_button.setVisible(True)
        self.level_combo.setVisible(True)
        self.sign_card.setVisible(not enabled)
        self.preview_button.setVisible(not enabled)
        self.export_pdf_button.setVisible(not enabled)
        self.export_excel_button.setVisible(not enabled)
        self.report_filter_card.setVisible(False)
        self.tabs.tabBar().setTabVisible(0, True)
        self.tabs.tabBar().setTabVisible(1, False)
        self.tabs.setCurrentIndex(0)

    def set_reports_mode(self, enabled: bool = True) -> None:
        """Modo Reportes: firmantes + vista previa/exportación."""
        self._reports_mode = enabled
        self._notes_mode = not enabled
        self.save_button.setVisible(not enabled)
        self.level_combo.setVisible(True)
        self.sign_card.setVisible(enabled)
        self.preview_button.setVisible(enabled)
        self.export_pdf_button.setVisible(enabled)
        self.export_excel_button.setVisible(enabled)
        self.report_filter_card.setVisible(enabled)
        self.tabs.tabBar().setTabVisible(0, not enabled)
        self.tabs.tabBar().setTabVisible(1, True)
        if enabled:
            self.tabs.setCurrentIndex(1)

    def configure_report_filters(
        self,
        contexts: list[dict[str, Any]],
        selected_assignment_id: str | None = None,
        selected_trimester: int | None = None,
    ) -> None:
        self.report_assignment_combo.blockSignals(True)
        self.report_assignment_combo.clear()
        for context in contexts:
            self.report_assignment_combo.addItem(
                context.get("display", context.get("id_asignacion", "")),
                str(context.get("id_asignacion") or ""),
            )
        if selected_assignment_id:
            idx = self.report_assignment_combo.findData(str(selected_assignment_id))
            if idx >= 0:
                self.report_assignment_combo.setCurrentIndex(idx)
        self.report_assignment_combo.blockSignals(False)
        if selected_trimester:
            idx = self.report_trimester_combo.findData(int(selected_trimester))
            if idx >= 0:
                self.report_trimester_combo.setCurrentIndex(idx)

    def set_students(self, students: list[dict[str, str]], selected_level: str | None = None) -> None:
        self._students = students
        self._saved_rows_by_student = {
            str(row.get("estudiante_id") or ""): row for row in students if str(row.get("estudiante_id") or "").strip()
        }
        if selected_level:
            idx = self.level_combo.findData(selected_level)
            if idx >= 0 and idx != self.level_combo.currentIndex():
                self.level_combo.setCurrentIndex(idx)
                return
        self._build_tables()
        self._refresh_preview_if_reports_mode()

    def _setup_table(self, table: QTableWidget, editable: bool) -> None:
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        header.setVisible(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(50)
        header.setDefaultSectionSize(100)
        table.setSelectionBehavior(QAbstractItemView.SelectItems)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setAlternatingRowColors(False)
        table.setWordWrap(True)
        if editable:
            table.setEditTriggers(
                QAbstractItemView.SelectedClicked
                | QAbstractItemView.EditKeyPressed
                | QAbstractItemView.AnyKeyPressed
            )
            table.installEventFilter(self)
        else:
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def _on_level_changed(self) -> None:
        self._build_tables()
        self._refresh_preview_if_reports_mode()

    def _refresh_preview_if_reports_mode(self) -> None:
        if not self._reports_mode:
            return
        try:
            html = self._render_preview_html()
        except Exception:  # noqa: BLE001
            html = ""
        self._last_preview_html = html
        self._set_preview_html(html)

    def _build_tables(self) -> None:
        level_key = self.level_combo.currentData()
        criterios = self.DATOS_EVALUACION.get(level_key, []) if level_key else []
        indicator_count = sum(len(c.indicadores) for c in criterios)
        self._indicator_count = indicator_count
        total_rows = 3 + len(self._students)
        self._header_details = {}
        self._indicator_start_col = 2
        self._result_start_col = self._indicator_start_col + indicator_count

        self.matrix_table.clearSpans()

        self.matrix_table.setRowCount(total_rows)
        self.matrix_table.setColumnCount(2 + indicator_count + 3)
        self.matrix_table.setHorizontalHeaderLabels([""] * (2 + indicator_count + 3))

        self._populate_headers(criterios, indicator_count)
        self._populate_students(criterios, indicator_count)
        self._apply_dimensions(criterios, indicator_count)
        self._apply_saved_rows(indicator_count)

    def _apply_saved_rows(self, indicator_count: int) -> None:
        self._updating_cells = True
        self.matrix_table.blockSignals(True)
        try:
            for index, student in enumerate(self._students, start=1):
                row_idx = 2 + index
                saved = self._saved_rows_by_student.get(str(student.get("estudiante_id") or ""))
                if not saved:
                    continue
                notas = saved.get("notas_indicadores") or []
                if isinstance(notas, list):
                    for col in range(min(indicator_count, len(notas))):
                        value = notas[col]
                        if value is None or str(value).strip() == "":
                            continue
                        item = self.matrix_table.item(row_idx, self._indicator_start_col + col)
                        if item is not None:
                            item.setText(str(value))
                has_notes = any(v is not None and str(v).strip() != "" for v in notas) if isinstance(notas, list) else False
                if has_notes and indicator_count > 0:
                    self._recalculate_row(row_idx)
                else:
                    valor = str(saved.get("valor") or "").strip() or "-"
                    cualitativo = str(saved.get("cualitativo") or "").strip() or "-"
                    cualitativo_1 = str(saved.get("cualitativo_1") or "").strip() or "-"
                    self._set_result_values(row_idx, valor, cualitativo, cualitativo_1)
        finally:
            self.matrix_table.blockSignals(False)
            self._updating_cells = False

    def _populate_headers(self, criterios: list[CriterioEvaluacion], indicator_count: int) -> None:
        self._set_header_item(self.matrix_table, 0, 0, "N°", "left")
        self.matrix_table.setSpan(0, 0, 3, 1)
        self._set_header_item(self.matrix_table, 0, 1, "Estudiante", "left")
        self.matrix_table.setSpan(0, 1, 3, 1)

        if indicator_count > 0:
            self._set_header_item(self.matrix_table, 0, self._indicator_start_col, "Criterios e Indicadores de Evaluación", "group")
            self.matrix_table.setSpan(0, self._indicator_start_col, 1, indicator_count)

            col = self._indicator_start_col
            for crit_index, criterio in enumerate(criterios, start=1):
                span = len(criterio.indicadores)
                self._set_header_item(
                    self.matrix_table,
                    1,
                    col,
                    f"Criterio {crit_index}",
                    "criterion",
                    criterio.titulo,
                )
                self._header_details[(1, col)] = ("Criterio", criterio.titulo)
                self.matrix_table.setSpan(1, col, 1, span)
                for ind_index, indicador in enumerate(criterio.indicadores, start=1):
                    self._set_header_item(
                        self.matrix_table,
                        2,
                        col,
                        f"Ind. {ind_index}",
                        "indicator",
                        f"Cr. {crit_index} - {indicador}",
                    )
                    self._header_details[(2, col)] = ("Indicador", indicador)
                    col += 1
        else:
            self._set_header_item(self.matrix_table, 0, self._indicator_start_col, "Seleccione nivel", "group")
            self.matrix_table.setSpan(0, self._indicator_start_col, 3, 1)

        self._set_header_item(self.matrix_table, 0, self._result_start_col, "VALOR\n(Promedio)", "value")
        self.matrix_table.setSpan(0, self._result_start_col, 3, 1)
        self._set_header_item(self.matrix_table, 0, self._result_start_col + 1, "CUALITATIVO", "qual")
        self.matrix_table.setSpan(0, self._result_start_col + 1, 3, 1)
        self._set_header_item(self.matrix_table, 0, self._result_start_col + 2, "CUALITATIVO 1", "qual1")
        self.matrix_table.setSpan(0, self._result_start_col + 2, 3, 1)

    def _populate_students(self, criterios: list[CriterioEvaluacion], indicator_count: int) -> None:
        for index, student in enumerate(self._students, start=1):
            row = 2 + index
            self._set_data_item(self.matrix_table, row, 0, str(index), editable=False)
            self._set_data_item(self.matrix_table, row, 1, student.get("estudiante", ""), editable=False)
            for col in range(indicator_count):
                self._set_data_item(self.matrix_table, row, self._indicator_start_col + col, "", editable=True)
            self._set_data_item(self.matrix_table, row, self._result_start_col, "-", editable=False)
            self._set_data_item(self.matrix_table, row, self._result_start_col + 1, "-", editable=False)
            self._set_data_item(self.matrix_table, row, self._result_start_col + 2, "-", editable=False)

        self._updating_cells = True
        try:
            for row in range(3):
                for col in range(self.matrix_table.columnCount()):
                    if self.matrix_table.item(row, col) is not None:
                        continue
                    role = "group" if self._indicator_start_col <= col < self._result_start_col else "left"
                    if col >= self._result_start_col:
                        role = "value" if col == self._result_start_col else ("qual" if col == self._result_start_col + 1 else "qual1")
                    self._set_header_item(self.matrix_table, row, col, "", role)
        finally:
            self._updating_cells = False

    def _apply_dimensions(self, criterios: list[CriterioEvaluacion], indicator_count: int) -> None:
        self.matrix_table.setColumnWidth(0, 50)
        self.matrix_table.setColumnWidth(1, 300)
        for col in range(indicator_count):
            self.matrix_table.setColumnWidth(self._indicator_start_col + col, 110)
        self.matrix_table.setColumnWidth(self._result_start_col, 110)
        self.matrix_table.setColumnWidth(self._result_start_col + 1, 100)
        self.matrix_table.setColumnWidth(self._result_start_col + 2, 90)

        total_rows = self.matrix_table.rowCount()
        for row in range(total_rows):
            height = 36 if row < 3 else 32
            self.matrix_table.setRowHeight(row, height)

    def _on_matrix_table_cell_clicked(self, row: int, col: int) -> None:
        if row < 3:
            return
        if not (self._indicator_start_col <= col < self._result_start_col):
            return
        item = self.matrix_table.item(row, col)
        if item is None or not (item.flags() & Qt.ItemIsEditable):
            return
        self.matrix_table.editItem(item)

    def _on_matrix_header_double_clicked(self, row: int, col: int) -> None:
        if row not in (1, 2):
            return
        if not (self._indicator_start_col <= col < self._result_start_col):
            return
        resolved = self._resolve_header_origin(row, col)
        if resolved is None:
            return
        title, text = self._header_details.get(resolved, ("", ""))
        if not text:
            return
        QMessageBox.information(self, f"{title} completo", text)

    def _resolve_header_origin(self, row: int, col: int) -> tuple[int, int] | None:
        for origin_col in range(col, self._indicator_start_col - 1, -1):
            item = self.matrix_table.item(row, origin_col)
            if item is None:
                continue
            span = self.matrix_table.columnSpan(row, origin_col)
            if origin_col <= col < origin_col + span:
                return (row, origin_col)
        return None

    def eventFilter(self, obj, event):  # type: ignore[override]
        if obj is self.matrix_table and event.type() == QEvent.KeyPress:
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
                self._paste_from_clipboard()
                return True
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
                self._copy_selected_cells()
                return True
        return super().eventFilter(obj, event)

    def _copy_selected_cells(self) -> None:
        ranges = self.matrix_table.selectedRanges()
        if not ranges:
            return
        selected_range = ranges[0]
        lines: list[str] = []
        for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
            if row < 3:
                continue
            cells: list[str] = []
            left_col = max(selected_range.leftColumn(), self._indicator_start_col)
            right_col = min(selected_range.rightColumn(), self._result_start_col - 1)
            for col in range(left_col, right_col + 1):
                item = self.matrix_table.item(row, col)
                cells.append(item.text() if item else "")
            lines.append("\t".join(cells))
        if lines:
            QApplication.clipboard().setText("\n".join(lines))

    def _paste_from_clipboard(self) -> None:
        text = QApplication.clipboard().text()
        if not text.strip():
            return
        start_row = self.matrix_table.currentRow()
        start_col = self.matrix_table.currentColumn()
        if start_row < 3 or start_col < self._indicator_start_col or start_col >= self._result_start_col:
            return

        rows = [line.split("\t") for line in text.splitlines() if line.strip()]
        changed_rows: set[int] = set()
        self._updating_cells = True
        try:
            for row_offset, values in enumerate(rows):
                target_row = start_row + row_offset
                if target_row >= self.matrix_table.rowCount():
                    break
                if target_row < 3:
                    continue
                for col_offset, value in enumerate(values):
                    target_col = start_col + col_offset
                    if target_col >= self._result_start_col:
                        break
                    item = self.matrix_table.item(target_row, target_col)
                    if item is None or not (item.flags() & Qt.ItemIsEditable):
                        continue
                    item.setText(value.strip())
                    changed_rows.add(target_row)
        finally:
            self._updating_cells = False

        for row in sorted(changed_rows):
            self._recalculate_row(row)

    def _on_grade_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_cells:
            return
        row = item.row()
        if row < 3:
            return
        self._recalculate_row(row)

    def _recalculate_row(self, row: int) -> None:
        if self._indicator_count == 0:
            return

        values: list[float] = []
        invalid_found = False

        self._updating_cells = True
        try:
            for col in range(self._indicator_start_col, self._result_start_col):
                cell = self.matrix_table.item(row, col)
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
                current_tip = self.matrix_table.item(row, self._result_start_col).toolTip() if self.matrix_table.item(row, self._result_start_col) else ""
                if msg not in current_tip:
                    self.matrix_table.item(row, self._result_start_col).setToolTip(msg)
            else:
                self.matrix_table.item(row, self._result_start_col).setToolTip("")
        finally:
            self._updating_cells = False

    def _set_result_values(self, row: int, promedio: str, cualitativo: str, cualitativo_1: str) -> None:
        value_item = self.matrix_table.item(row, self._result_start_col)
        qual_item = self.matrix_table.item(row, self._result_start_col + 1)
        qual1_item = self.matrix_table.item(row, self._result_start_col + 2)
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
        indicadores_total = self._indicator_count
        result_rows: list[dict[str, Any]] = []
        has_invalid = False

        for idx, student in enumerate(self._students, start=1):
            row = 2 + idx
            notas: list[float | None] = []
            for col in range(indicadores_total):
                item = self.matrix_table.item(row, self._indicator_start_col + col)
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

            promedio = self.matrix_table.item(row, self._result_start_col).text() if self.matrix_table.item(row, self._result_start_col) else "-"
            cualitativo = self.matrix_table.item(row, self._result_start_col + 1).text() if self.matrix_table.item(row, self._result_start_col + 1) else "-"
            cualitativo_1 = self.matrix_table.item(row, self._result_start_col + 2).text() if self.matrix_table.item(row, self._result_start_col + 2) else "-"
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

    def _build_preview_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for index, student in enumerate(self._students, start=1):
            row_idx = 2 + index
            student_name = student.get("estudiante", "")
            value_item = self.matrix_table.item(row_idx, self._result_start_col)
            qual_item = self.matrix_table.item(row_idx, self._result_start_col + 1)
            qual1_item = self.matrix_table.item(row_idx, self._result_start_col + 2)
            valor = value_item.text().strip() if value_item else ""
            cualitativo = qual_item.text().strip() if qual_item else ""
            cualitativo_1 = qual1_item.text().strip() if qual1_item else ""
            if not valor or valor == "-":
                valor = str(student.get("valor") or "").strip()
            if not cualitativo or cualitativo == "-":
                cualitativo = str(student.get("cualitativo") or "").strip()
            if not cualitativo_1 or cualitativo_1 == "-":
                cualitativo_1 = str(student.get("cualitativo_1") or "").strip()
            rows.append(
                {
                    "nro": str(index),
                    "nomina": student_name,
                    "valor": "" if valor == "-" else valor,
                    "cualitativo": "" if cualitativo == "-" else cualitativo,
                    "cualitativo_1": "" if cualitativo_1 == "-" else cualitativo_1,
                    "descripcion": self._descripcion_por_cualitativo_1(cualitativo_1),
                }
            )
        return rows

    @staticmethod
    def _descripcion_por_cualitativo_1(cualitativo_1: str) -> str:
        descriptions = {
            "A": "Gusto por la lectura avanzado",
            "B": "Gusto por la lectura en desarrollo intermedio",
            "C": "Gusto lector progresivo",
            "D": "Gusto lector exploratorio",
            "E": "Gusto por la lectura obstaculizado",
        }
        key = str(cualitativo_1 or "").strip().upper()
        return descriptions.get(key, "Sin información")

    def _build_preview_context(self) -> dict[str, Any]:
        if not self._assignment_id:
            raise ValueError("Seleccione una asignación.")
        if not self._trimester_num:
            raise ValueError("Seleccione un trimestre.")

        assignment_context = self._get_assignment_context(str(self._assignment_id)) if self._get_assignment_context else {}
        assignment_context = assignment_context or {}
        institution_data = self._get_institution_data() if self._get_institution_data else {}
        institution_data = institution_data or {}

        docente_default = f"{assignment_context.get('docente_apellidos', '')} {assignment_context.get('docente_nombres', '')}".strip()
        trimestre_label = f"TRIMESTRE {self._trimester_num}"
        level_label = str(self.level_combo.currentText() or "").strip()

        logo_institucional = HtmlReportRenderer._build_logo_source(institution_data.get("logo_path"), "institucional")
        logo_mineduc = HtmlReportRenderer._build_logo_source(institution_data.get("logo_ministerio_path"), "ministerio")

        return {
            "docente": self.sign_docente_combo.currentText().strip() or docente_default,
            "curso": assignment_context.get("curso_nombre") or assignment_context.get("curso_id", ""),
            "paralelo": assignment_context.get("paralelo_nombre") or assignment_context.get("paralelo_id", ""),
            "nivel": level_label or assignment_context.get("curso_nivel", ""),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "anio_lectivo": assignment_context.get("periodo_id", ""),
            "trimestre": trimestre_label,
            "reporte_titulo": f"ANIMACIÓN A LA LECTURA - {trimestre_label}",
            "rector": self.sign_rector_combo.currentText().strip() or institution_data.get("rector", ""),
            "logo_institucion": logo_institucional,
            "logo_ministerio": logo_mineduc,
            "estudiantes": self._build_preview_rows(),
            "stats": self._build_stats_summary(),
        }

    def _build_stats_summary(self) -> dict[str, Any]:
        rows = self._build_preview_rows()
        total = len(rows)
        counts = {key: 0 for key in ("A", "B", "C", "D", "E")}
        for row in rows:
            key = str(row.get("cualitativo_1") or "").strip().upper()
            if key in counts:
                counts[key] += 1

        def pct(value: int) -> str:
            if total == 0:
                return "0,00%"
            return f"{(value * 100 / total):.2f}%".replace(".", ",")

        return {
            "rows": [{"escala": key, "numero": counts[key], "porcentaje": pct(counts[key])} for key in ("A", "B", "C", "D", "E")],
            "total_n": total,
            "total_p": "100,00%" if total > 0 else "0,00%",
        }

    def _render_preview_html(self) -> str:
        context = self._build_preview_context()
        return HtmlReportRenderer().render_animacion_lectura(context, self._build_preview_rows())

    def _show_preview(self) -> None:
        try:
            html = self._render_preview_html()
            self._last_preview_html = html
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Vista Previa", f"No se pudo generar la vista previa:\n{exc}")
            return
        self._set_preview_html(html)
        self.tabs.setCurrentIndex(1)

    def _export_preview_pdf(self) -> None:
        try:
            html = self._render_preview_html()
            self._last_preview_html = html
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Exportar PDF", f"No se pudo generar la vista previa:\n{exc}")
            return

        suggested = f"{self._build_export_filename_base()}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", suggested, "PDF (*.pdf)")
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path = f"{file_path}.pdf"

        if QWebEnginePage is not None and QEventLoop is not None and QPageLayout is not None and QPageSize is not None and QMarginsF is not None and QUrl is not None:
            page = QWebEnginePage(self)
            loop = QEventLoop(self)
            result = {"ok": False}

            def on_load_finished(ok: bool) -> None:
                if not ok:
                    loop.quit()
                    return
                page_layout = QPageLayout(
                    QPageSize(QPageSize.A4),
                    QPageLayout.Portrait,
                    QMarginsF(12, 12, 12, 12),
                    QPageLayout.Millimeter,
                )
                page.printToPdf(file_path, page_layout)

            def on_pdf_done(_path: str, success: bool) -> None:
                result["ok"] = success
                loop.quit()

            page.loadFinished.connect(on_load_finished)
            page.pdfPrintingFinished.connect(on_pdf_done)
            page.setHtml(html, QUrl("about:blank"))
            loop.exec()
            if result["ok"]:
                QMessageBox.information(self, "Exportar PDF", f"PDF generado correctamente:\n{file_path}")
            else:
                QMessageBox.warning(self, "Exportar PDF", "No se pudo generar el PDF.")
            return

        document = QTextDocument()
        document.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        document.print_(printer)
        QMessageBox.information(self, "Exportar PDF", f"PDF generado correctamente:\n{file_path}")

    def _export_preview_excel(self) -> None:
        rows = self._build_preview_rows()
        stats = self._build_stats_summary()
        suggested = f"{self._build_export_filename_base()}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", suggested, "Excel (*.xlsx)")
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path = f"{file_path}.xlsx"

        wb = Workbook()
        ws = wb.active
        ws.title = "Animación Lectura"
        headers = ["N°", "Nómina de Estudiantes", "Valor", "Cualitativo", "Cualitativo 1", "Descripción"]
        ws.append(headers)
        for row in rows:
            ws.append(
                [
                    row["nro"],
                    row["nomina"],
                    row["valor"],
                    row["cualitativo"],
                    row["cualitativo_1"],
                    row["descripcion"],
                ]
            )
        ws.append([])
        ws.append(["ESCALA CUALITATIVA", "N°", "%"])
        for stat in stats["rows"]:
            ws.append([stat["escala"], stat["numero"], stat["porcentaje"]])
        ws.append(["TOTAL ESTUDIANTES", stats["total_n"], stats["total_p"]])
        wb.save(file_path)
        QMessageBox.information(self, "Exportar Excel", f"Excel generado correctamente:\n{file_path}")

    def _set_preview_html(self, html_content: str) -> None:
        if self._preview_uses_webengine:
            self.preview_view.setHtml(html_content, QUrl("about:blank"))
        else:
            self.preview_view.setHtml(html_content)

    def _on_signers_changed(self) -> None:
        self._refresh_preview_if_reports_mode()

    def _build_export_filename_base(self) -> str:
        assignment_text = str(self.report_assignment_combo.currentText() or "").strip()
        if not assignment_text:
            assignment_text = f"animacion_lectura_{self._assignment_id or 'reporte'}"
        return self._sanitize_filename(f"{assignment_text}_{self._report_period_suffix()}")

    def _report_period_suffix(self) -> str:
        if self._trimester_num:
            return f"Tri_{int(self._trimester_num)}"
        return "Anual"

    @staticmethod
    def _sanitize_filename(text: str) -> str:
        import re

        normalized = unicodedata.normalize("NFD", str(text or "").strip())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        normalized = re.sub(r"[|/\\:*?\"<>]+", "_", normalized)
        normalized = re.sub(r"\s+", "_", normalized)
        normalized = re.sub(r"_+", "_", normalized)
        normalized = normalized.strip(" ._")
        return normalized or "reporte_animacion_lectura"


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
        if self._result_start_col <= col <= self._result_start_col + 2:
            if col == self._result_start_col:
                item.setBackground(QColor("#ECFDF5"))
            elif col == self._result_start_col + 1:
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
        self._apply_default_signers_from_context()

    def _apply_default_signers_from_context(self) -> None:
        assignment_context = self._get_assignment_context(str(self._assignment_id or "")) if self._get_assignment_context else {}
        assignment_context = assignment_context or {}
        docente_default = f"{assignment_context.get('docente_apellidos', '')} {assignment_context.get('docente_nombres', '')}".strip()
        self._select_combo_by_name_parts(self.sign_docente_combo, docente_default, force=True)
        institution = self._get_institution_data() if self._get_institution_data else {}
        institution = institution or {}
        self._select_combo_by_name_parts(
            self.sign_rector_combo,
            str(institution.get("rector") or ""),
            force=not bool(self.sign_rector_combo.currentData()),
        )

    @staticmethod
    def _select_combo_by_name_parts(combo: QComboBox, full_name: str, *, force: bool = False) -> None:
        if combo.currentData() and not force:
            return
        normalized_target = AnimacionLecturaView._normalize_text(full_name)
        if not normalized_target:
            return
        target_parts = set(normalized_target.split())
        for index in range(combo.count()):
            option = AnimacionLecturaView._normalize_text(str(combo.itemData(index) or combo.itemText(index)))
            if option and target_parts.issubset(set(option.split())):
                combo.setCurrentIndex(index)
                return

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFD", str(value or "").strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())

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
            QWidget#AnimTableShell {
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
            QTableWidget#AnimMatrixTable {
                border: none;
                background: transparent;
            }
            """
        )
