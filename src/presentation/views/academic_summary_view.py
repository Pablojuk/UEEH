"""Vista de resumen académico anual y supletorio."""

from __future__ import annotations

import re
import unicodedata

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:  # noqa: BLE001
    QWebEngineView = None

from src.application.services.academic_summary_service import AcademicSummaryService
from src.application.services.report_export_service import ReportExportService
from src.presentation.widgets.busy_state import busy_button


class AcademicSummaryView(QWidget):
    ANNUAL_COLUMNS = [
        ("numero_lista", "N°"),
        ("estudiante", "Nómina"),
        ("trimestre_1", "T1 Calificación"),
        ("equivalencia_t1", "Cualitativa T1"),
        ("trimestre_2", "T2 Calificación"),
        ("equivalencia_t2", "Cualitativa T2"),
        ("trimestre_3", "T3 Calificación"),
        ("equivalencia_t3", "Cualitativa T3"),
        ("promedio", "Promedio"),
        ("cualitativa_anual", "Cualitativa"),
        ("supletorio", "Supletorio"),
        ("promedio_final", "Promedio Final"),
        ("observacion", "Observación"),
    ]

    TRIMESTRAL_COLUMNS = [
        ("estudiante", "Nómina"),
        ("aportes_calificacion", "Aportes/Insumos Calificación"),
        ("aportes_70", "Aportes/Insumos 70%"),
        ("sumativas_calificacion", "Evaluaciones sumativas Calificación"),
        ("sumativas_30", "Evaluaciones sumativas 30%"),
        ("promedio_final", "Promedio Final"),
        ("cualitativa", "Cualitativa"),
        ("equivalencia", "Equivalencia"),
        ("observacion", "Observación"),
    ]

    EDITABLE_COLUMNS = {"supletorio"}
    SPECIAL_SUBJECTS = {
        "orientacion vocacional y profesional",
        "comportamiento",
        "acompanamiento integral en el aula",
        "animacion a la lectura",
    }
    SIMPLIFIED_COURSES = {
        "2do de egb",
        "2do egb",
        "segundo de egb",
        "segundo egb",
        "3ro de egb",
        "3ro egb",
        "tercero de egb",
        "tercero egb",
        "4to de egb",
        "4to egb",
        "cuarto de egb",
        "cuarto egb",
    }

    def __init__(
        self,
        academic_summary_service: AcademicSummaryService,
        report_export_service: ReportExportService | None = None,
    ) -> None:
        super().__init__()
        self.academic_summary_service = academic_summary_service
        self.report_export_service = report_export_service
        self._rows_meta: list[dict] = []
        self._contexts_by_id: dict[str, dict] = {}
        self._table_columns = list(self.ANNUAL_COLUMNS)
        self._firmantes: dict[str, str] = {
            "docente": "",
            "coordinador_area": "",
            "rector": "",
            "tutor_curso": "",
        }
        self._suppress_auto_refresh = False
        self._simplified_mode = False

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        title = QLabel("Resumen Académico")
        title.setObjectName("Title")
        subtitle = QLabel("Consolidado anual, supletorio y exportación por asignación")
        subtitle.setObjectName("Subtitle")

        filter_card = QFrame()
        filter_card.setObjectName("Card")
        filter_row = QHBoxLayout(filter_card)

        self.assignment_combo = QComboBox()
        self.assignment_combo.setMinimumWidth(0)
        self.assignment_combo.currentIndexChanged.connect(self._on_filters_changed)
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItem("Anual", ("anual", None))
        self.report_type_combo.addItem("Primer Trimestre", ("trimestral", 1))
        self.report_type_combo.addItem("Segundo Trimestre", ("trimestral", 2))
        self.report_type_combo.addItem("Tercer Trimestre", ("trimestral", 3))
        self.report_type_combo.currentIndexChanged.connect(self._on_report_type_changed)
        self.load_button = QPushButton("Cargar resumen")
        self.load_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.load_button, "Cargando...", self.load_summary)
        )
        self.recalc_button = QPushButton("Recalcular")
        self.recalc_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.recalc_button, "Procesando...", self.recalculate_rows)
        )
        self.save_button = QPushButton("Guardar supletorio")
        self.save_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.save_button, "Guardando...", self.save_rows)
        )
        self.preview_button = QPushButton("Vista previa")
        self.preview_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.preview_button, "Generando...", self.show_preview)
        )
        self.export_pdf_button = QPushButton("Exportar PDF")
        self.export_pdf_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.export_pdf_button, "Exportando...", self.export_pdf)
        )
        self.export_excel_button = QPushButton("Exportar Excel")
        self.export_excel_button.clicked.connect(
            lambda _checked=False: self._run_with_busy_state(self.export_excel_button, "Exportando...", self.export_excel)
        )

        filter_row.addWidget(QLabel("Asignación"))
        filter_row.addWidget(self.assignment_combo, 1)
        filter_row.addWidget(QLabel("Tipo de informe"))
        filter_row.addWidget(self.report_type_combo)
        filter_row.addWidget(self.load_button)
        filter_row.addWidget(self.recalc_button)
        filter_row.addWidget(self.save_button)
        filter_row.addWidget(self.preview_button)
        filter_row.addWidget(self.export_pdf_button)
        filter_row.addWidget(self.export_excel_button)

        sign_card = QGroupBox("Firmantes del reporte")
        sign_layout = QHBoxLayout(sign_card)
        self.signer_docente_combo = QComboBox()
        self.signer_coordinador_combo = QComboBox()
        self.signer_rector_combo = QComboBox()
        self.signer_tutor_combo = QComboBox()
        self.signer_docente_combo.currentIndexChanged.connect(self._update_signers)
        self.signer_coordinador_combo.currentIndexChanged.connect(self._update_signers)
        self.signer_rector_combo.currentIndexChanged.connect(self._update_signers)
        self.signer_tutor_combo.currentIndexChanged.connect(self._update_signers)

        sign_layout.addWidget(QLabel("Docente"))
        sign_layout.addWidget(self.signer_docente_combo, 1)
        sign_layout.addWidget(QLabel("Coordinador de Área"))
        sign_layout.addWidget(self.signer_coordinador_combo, 1)
        sign_layout.addWidget(QLabel("Rector"))
        sign_layout.addWidget(self.signer_rector_combo, 1)
        sign_layout.addWidget(QLabel("Tutor de Curso"))
        sign_layout.addWidget(self.signer_tutor_combo, 1)

        self.table = QTableWidget(0, len(self._table_columns))
        self.table.setHorizontalHeaderLabels([label for _, label in self._table_columns])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.installEventFilter(self)
        self.copy_shortcut = QShortcut("Ctrl+C", self.table)
        self.copy_shortcut.activated.connect(self._copy_selected_cells)

        self.tabs = QTabWidget()
        resumen_tab = QWidget()
        resumen_layout = QVBoxLayout(resumen_tab)
        resumen_layout.setContentsMargins(0, 0, 0, 0)
        resumen_layout.addWidget(self.table)
        self.tabs.addTab(resumen_tab, "Resumen")

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
        preview_layout.addWidget(self.preview_view)
        self.tabs.addTab(preview_tab, "Vista previa")
        self.btn_toggle_filas = QPushButton("🙈 Ocultar Filas Vacías")
        self.btn_toggle_filas.setCheckable(True)
        self.btn_toggle_filas.setChecked(False)
        self.btn_toggle_filas.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_filas.setFixedHeight(28)
        self.btn_toggle_filas.setStyleSheet(
            """
            QPushButton {
                background-color: #5b7fa6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0 12px;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: #2e5f8a;
            }
            QPushButton:hover {
                background-color: #4a6d94;
            }
            """
        )
        self.btn_toggle_filas.clicked.connect(self._toggle_filas_vacias)
        self.tabs.setCornerWidget(self.btn_toggle_filas, Qt.TopRightCorner)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(filter_card)
        root.addWidget(sign_card)
        root.addWidget(self.tabs, 1)

        self.load_contexts()
        self._load_signer_options()
        self._on_report_type_changed()

    def _run_with_busy_state(self, button: QPushButton, busy_text: str, callback) -> None:
        with busy_button(button, busy_text):
            callback()

    def load_contexts(self, selected_assignment_id: str | None = None) -> None:
        self.assignment_combo.clear()
        contexts = self.academic_summary_service.listar_contextos_disponibles()
        self._contexts_by_id = {str(row.get("id_asignacion")): row for row in contexts if row.get("id_asignacion")}
        if not contexts:
            self.assignment_combo.addItem("Sin asignaciones disponibles", None)
            return

        for row in contexts:
            self.assignment_combo.addItem(row.get("display", row.get("id_asignacion", "")), row.get("id_asignacion"))
        if selected_assignment_id:
            idx = self.assignment_combo.findData(selected_assignment_id)
            if idx >= 0:
                self.assignment_combo.setCurrentIndex(idx)

    def load_summary(self) -> None:
        asignacion_id = self.assignment_combo.currentData()
        if not asignacion_id:
            self._fill_table([])
            self._refresh_preview_silent()
            return

        report_type, trimestre_num = self.report_type_combo.currentData()
        if report_type == "trimestral":
            rows = self.academic_summary_service.obtener_reporte_trimestral(asignacion_id, int(trimestre_num))
        else:
            rows = self.academic_summary_service.obtener_reporte_anual(asignacion_id)
        self._fill_table(rows)
        self._refresh_preview_silent()

    def recalculate_rows(self) -> None:
        report_type, _ = self.report_type_combo.currentData()
        if report_type == "trimestral":
            self.load_summary()
            return
        rows = self._collect_rows_from_table()
        try:
            recalculated = self.academic_summary_service.recalcular_resumenes(rows)
        except ValueError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return

        self._fill_table(recalculated)

    def save_rows(self) -> None:
        asignacion_id = self.assignment_combo.currentData()
        if not asignacion_id:
            QMessageBox.warning(self, "Validación", "Seleccione una asignación")
            return

        report_type, _ = self.report_type_combo.currentData()
        if report_type != "anual":
            QMessageBox.information(self, "Información", "El supletorio solo aplica al reporte anual.")
            return
        rows = self._collect_rows_from_table()
        try:
            ok, message = self.academic_summary_service.guardar_supletorios(asignacion_id, rows)
        except ValueError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return

        if ok:
            QMessageBox.information(self, "Éxito", message)
            self.load_summary()
        else:
            QMessageBox.warning(self, "Error", message)

    def show_preview(self) -> None:
        if self.report_export_service is None:
            QMessageBox.warning(self, "Error", "Servicio de exportación no disponible")
            return

        asignacion_id = self.assignment_combo.currentData()
        if not asignacion_id:
            QMessageBox.warning(self, "Validación", "Seleccione una asignación")
            return

        report_type, trimestre_num = self.report_type_combo.currentData()
        try:
            html_report = self.report_export_service.generar_resumen_html(
                asignacion_id,
                report_type=report_type,
                trimestre_num=trimestre_num,
                firmantes=self._firmantes,
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Error", f"No se pudo generar la vista previa: {exc}")
            return

        self._set_preview_html(html_report)
        self.tabs.setCurrentIndex(1)

    def export_pdf(self) -> None:
        self._export("pdf")

    def export_excel(self) -> None:
        self._export("excel")

    def _export(self, kind: str) -> None:
        if self.report_export_service is None:
            QMessageBox.warning(self, "Error", "Servicio de exportación no disponible")
            return

        asignacion_id = self.assignment_combo.currentData()
        if not asignacion_id:
            QMessageBox.warning(self, "Validación", "Seleccione una asignación")
            return

        assignment_text = self.assignment_combo.currentText() or str(asignacion_id)
        safe_base = self._sanitize_filename(assignment_text)
        report_type, trimestre_num = self.report_type_combo.currentData()
        period_suffix = self._report_period_suffix(report_type, trimestre_num)
        default_name = f"{safe_base}_{period_suffix}.{ 'pdf' if kind == 'pdf' else 'xlsx' }"
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte",
            default_name,
            "PDF (*.pdf)" if kind == "pdf" else "Excel (*.xlsx)",
        )
        if not selected_path:
            return

        ocultar_filas_vacias = self.btn_toggle_filas.isChecked()
        if kind == "pdf":
            ok, message = self.report_export_service.exportar_resumen_pdf(
                asignacion_id,
                selected_path,
                report_type=report_type,
                trimestre_num=trimestre_num,
                firmantes=self._firmantes,
                ocultar_filas_vacias=ocultar_filas_vacias,
            )
        else:
            ok, message = self.report_export_service.exportar_resumen_excel(
                asignacion_id,
                selected_path,
                report_type=report_type,
                trimestre_num=trimestre_num,
                firmantes=self._firmantes,
                ocultar_filas_vacias=ocultar_filas_vacias,
            )

        if ok:
            QMessageBox.information(self, "Éxito", message)
        else:
            QMessageBox.warning(self, "Error", message)

    def _fill_table(self, rows: list[dict]) -> None:
        self.table.setRowCount(0)
        self._rows_meta = rows

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, (field, _) in enumerate(self._table_columns):
                value = row_data.get(field)
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                if field not in self.EDITABLE_COLUMNS:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

    def _collect_rows_from_table(self) -> list[dict]:
        rows: list[dict] = []
        for row_idx in range(self.table.rowCount()):
            meta = self._rows_meta[row_idx] if row_idx < len(self._rows_meta) else {}
            row_data = dict(meta)
            for col, (field, _) in enumerate(self._table_columns):
                item = self.table.item(row_idx, col)
                text = item.text().strip() if item else ""
                row_data[field] = text if text != "" else None
            rows.append(row_data)
        return rows

    def _on_report_type_changed(self) -> None:
        report_type, _ = self.report_type_combo.currentData()
        if report_type == "trimestral":
            self._table_columns = list(self.TRIMESTRAL_COLUMNS)
            self.save_button.setEnabled(False)
        else:
            self._table_columns = list(self.ANNUAL_COLUMNS)
            self.save_button.setEnabled(True)
        self.table.setColumnCount(len(self._table_columns))
        self.table.setHorizontalHeaderLabels([label for _, label in self._table_columns])
        self.table.setRowCount(0)
        self._rows_meta = []
        self._apply_summary_mode_visibility()
        self._on_filters_changed()

    def _set_preview_html(self, html_content: str) -> None:
        self.btn_toggle_filas.setChecked(False)
        self.btn_toggle_filas.setText("🙈 Ocultar Filas Vacías")
        if self._preview_uses_webengine:
            self.preview_view.setHtml(html_content)
        else:
            self.preview_view.setHtml(html_content)

    def _toggle_filas_vacias(self, checked: bool) -> None:
        if checked:
            self.btn_toggle_filas.setText("👁 Mostrar Filas Vacías")
            js_code = """
                (function() {
                    function isEmptyCell(cell) {
                        if (!cell) { return true; }
                        var text = (cell.textContent || '').replace(/\\u00A0/g, '').trim();
                        var raw = (cell.innerHTML || '').trim().toLowerCase();
                        return text === '' || text === '—' || raw === '&nbsp;' || raw === '';
                    }
                    var rows = document.querySelectorAll('table.principal tbody tr');
                    rows.forEach(function(row) {
                        var celdaNombre = row.cells[1];
                        if (isEmptyCell(celdaNombre)) {
                            row.style.display = 'none';
                        }
                    });
                })();
            """
        else:
            self.btn_toggle_filas.setText("🙈 Ocultar Filas Vacías")
            js_code = """
                (function() {
                    var rows = document.querySelectorAll('table.principal tbody tr');
                    rows.forEach(function(row) {
                        row.style.display = '';
                    });
                })();
            """

        if self._preview_uses_webengine and hasattr(self.preview_view, "page"):
            self.preview_view.page().runJavaScript(js_code)

    def _load_signer_options(self, selected_signers: dict[str, str] | None = None) -> None:
        options = self.academic_summary_service.listar_firmantes_disponibles()
        combos = [
            self.signer_docente_combo,
            self.signer_coordinador_combo,
            self.signer_rector_combo,
            self.signer_tutor_combo,
        ]
        for combo in combos:
            combo.clear()
            combo.addItem("Seleccione", "")
            for row in options:
                combo.addItem(row.get("firma", ""), row.get("firma", ""))
        if selected_signers:
            mapping = [
                (self.signer_docente_combo, selected_signers.get("docente", "")),
                (self.signer_coordinador_combo, selected_signers.get("coordinador_area", "")),
                (self.signer_rector_combo, selected_signers.get("rector", "")),
                (self.signer_tutor_combo, selected_signers.get("tutor_curso", "")),
            ]
            for combo, value in mapping:
                idx = combo.findData(value)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
        self._update_signers()

    def refresh_data(self) -> None:
        selected_assignment_id = self.assignment_combo.currentData()
        selected_signers = {
            "docente": self.signer_docente_combo.currentData() or "",
            "coordinador_area": self.signer_coordinador_combo.currentData() or "",
            "rector": self.signer_rector_combo.currentData() or "",
            "tutor_curso": self.signer_tutor_combo.currentData() or "",
        }
        self.load_contexts(selected_assignment_id=selected_assignment_id)
        self._load_signer_options(selected_signers=selected_signers)

    def _update_signers(self) -> None:
        self._firmantes = {
            "docente": self.signer_docente_combo.currentData() or "",
            "coordinador_area": self.signer_coordinador_combo.currentData() or "",
            "rector": self.signer_rector_combo.currentData() or "",
            "tutor_curso": self.signer_tutor_combo.currentData() or "",
        }
        self._refresh_preview_silent()

    def _on_filters_changed(self) -> None:
        self._apply_summary_mode_visibility()
        if self._suppress_auto_refresh:
            return
        self.load_summary()

    def _apply_summary_mode_visibility(self) -> None:
        simplified = self._should_use_simplified_mode()
        self._simplified_mode = simplified
        self.load_button.setVisible(not simplified)
        self.recalc_button.setVisible(not simplified)
        self.save_button.setVisible(not simplified)
        resumen_index = self.tabs.indexOf(self.table.parentWidget())
        if resumen_index >= 0:
            self.tabs.setTabVisible(resumen_index, not simplified)
        if simplified:
            self.tabs.setCurrentIndex(1)

    def _should_use_simplified_mode(self) -> bool:
        asignacion_id = str(self.assignment_combo.currentData() or "")
        if not asignacion_id:
            return False
        context = self._contexts_by_id.get(asignacion_id, {})
        subject = self._normalize_text(str(context.get("asignatura_nombre") or ""))
        if subject in self.SPECIAL_SUBJECTS:
            return False
        course_name = self._normalize_text(str(context.get("curso_nombre") or ""))
        return any(alias in course_name for alias in self.SIMPLIFIED_COURSES)

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFD", str(value or "").strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())

    def _refresh_preview_silent(self) -> None:
        if self.report_export_service is None:
            return
        asignacion_id = self.assignment_combo.currentData()
        if not asignacion_id:
            self._set_preview_html("")
            return
        report_type, trimestre_num = self.report_type_combo.currentData()
        try:
            html_report = self.report_export_service.generar_resumen_html(
                asignacion_id,
                report_type=report_type,
                trimestre_num=trimestre_num,
                firmantes=self._firmantes,
            )
        except Exception:  # noqa: BLE001
            return
        self._set_preview_html(html_report)

    def eventFilter(self, obj, event):  # type: ignore[override]
        if obj is self.table and event.type() == QEvent.KeyPress:
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
                self._copy_selected_cells()
                return True
        return super().eventFilter(obj, event)

    def _copy_selected_cells(self) -> None:
        ranges = self.table.selectedRanges()
        if not ranges:
            return
        selected_range = ranges[0]
        lines: list[str] = []
        for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
            values: list[str] = []
            for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                item = self.table.item(row, col)
                values.append(item.text() if item else "")
            lines.append("\t".join(values))
        QApplication.clipboard().setText("\n".join(lines))

    @staticmethod
    def _report_period_suffix(report_type: str, trimestre_num: int | None) -> str:
        if report_type == "trimestral" and trimestre_num:
            return f"Tri_{int(trimestre_num)}"
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
        return normalized or "reporte"
