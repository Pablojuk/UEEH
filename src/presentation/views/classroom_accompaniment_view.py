"""Vista de Acompañamiento Integral en el Aula."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from PySide6.QtCore import QMarginsF, Qt
from PySide6.QtGui import QPageLayout, QPageSize
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
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QGroupBox,
)
from jinja2 import Environment, FileSystemLoader
from openpyxl import Workbook

try:
    from PySide6.QtCore import QEventLoop, QUrl
    from PySide6.QtWebEngineCore import QWebEnginePage
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:  # pragma: no cover
    QUrl = None
    QEventLoop = None
    QWebEnginePage = None
    QWebEngineView = None

from src.application.services.classroom_accompaniment_service import (
    MAX_ACTIVE_SKILLS,
    ClassroomAccompanimentService,
    RESPONSE_OPTIONS,
)
from src.infrastructure.exporters.html_report_renderer import HtmlReportRenderer
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
        self._ultimo_html_vista_previa = ""
        self._firmantes: dict[str, str] = {"docente": "", "rector": ""}

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        self.title_label = QLabel("Acompañamiento Integral en el Aula")
        self.title_label.setObjectName("Title")
        self.subtitle_label = QLabel("Evaluación cualitativa por estudiante, asignación y trimestre")
        self.subtitle_label.setObjectName("Subtitle")

        self.filter_card = QFrame()
        self.filter_card.setObjectName("Card")
        filter_row = QHBoxLayout(self.filter_card)

        self.assignment_combo = QComboBox()
        self.assignment_combo.setMinimumWidth(300)
        self.assignment_combo.currentIndexChanged.connect(self._on_context_filters_changed)
        self.trimester_combo = QComboBox()
        for label, value in self.TRIMESTERS:
            self.trimester_combo.addItem(label, value)
        self.trimester_combo.currentIndexChanged.connect(self._on_context_filters_changed)

        self.load_button = QPushButton("Cargar listado")
        self.load_button.clicked.connect(self.load_rows)
        self.save_button = QPushButton("Guardar evaluación")
        self.save_button.clicked.connect(self.save_rows)
        self.configure_skills_button = QPushButton("Configurar habilidades")
        self.configure_skills_button.clicked.connect(self.open_skill_config)
        self.btn_vista_previa_cual = QPushButton("Vista Previa")
        self.btn_vista_previa_cual.setStyleSheet(
            """
            QPushButton {
                background-color: #1F4E79;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2E75B6; }
            QPushButton:disabled { background-color: #999; }
            """
        )
        self.btn_vista_previa_cual.setEnabled(False)
        self.btn_vista_previa_cual.clicked.connect(self._mostrar_vista_previa_cualitativa)
        self.btn_exportar_pdf_cual = QPushButton("Exportar PDF")
        self.btn_exportar_pdf_cual.setEnabled(False)
        self.btn_exportar_pdf_cual.clicked.connect(self._exportar_vista_previa_pdf)
        self.btn_exportar_excel_cual = QPushButton("Exportar Excel")
        self.btn_exportar_excel_cual.setEnabled(False)
        self.btn_exportar_excel_cual.clicked.connect(self._exportar_excel)

        self.assignment_label = QLabel("Asignación")
        self.trimester_label = QLabel("Trimestre")
        filter_row.addWidget(self.assignment_label)
        filter_row.addWidget(self.assignment_combo, 1)
        filter_row.addWidget(self.trimester_label)
        filter_row.addWidget(self.trimester_combo)
        filter_row.addWidget(self.load_button)
        filter_row.addWidget(self.save_button)
        filter_row.addWidget(self.configure_skills_button)
        filter_row.addWidget(self.btn_vista_previa_cual)
        filter_row.addWidget(self.btn_exportar_pdf_cual)
        filter_row.addWidget(self.btn_exportar_excel_cual)

        self.sign_card = QGroupBox("Firmantes del reporte")
        sign_layout = QHBoxLayout(self.sign_card)
        self.signer_docente_combo = QComboBox()
        self.signer_rector_combo = QComboBox()
        self.signer_docente_combo.currentIndexChanged.connect(self._update_signers)
        self.signer_rector_combo.currentIndexChanged.connect(self._update_signers)
        sign_layout.addWidget(QLabel("Docente"))
        sign_layout.addWidget(self.signer_docente_combo, 1)
        sign_layout.addWidget(QLabel("Rector"))
        sign_layout.addWidget(self.signer_rector_combo, 1)

        self.skills_reference_card = QFrame()
        self.skills_reference_card.setObjectName("Card")
        self.skills_reference_layout = QVBoxLayout(self.skills_reference_card)

        self.table = QTableWidget(0, 2)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self.tabs = QTabWidget()
        eval_tab = QWidget()
        eval_layout = QVBoxLayout(eval_tab)
        eval_layout.setContentsMargins(0, 0, 0, 0)
        eval_layout.addWidget(self.skills_reference_card)
        eval_layout.addWidget(self.table, 1)
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
        preview_layout.addWidget(self.preview_view)
        self.tabs.addTab(preview_tab, "Vista previa")

        root.addWidget(self.title_label)
        root.addWidget(self.subtitle_label)
        root.addWidget(self.filter_card)
        root.addWidget(self.sign_card)
        root.addWidget(self.tabs, 1)

        self.load_contexts()
        self._load_signer_options()

    def set_embedded_mode(self, embedded: bool) -> None:
        self.title_label.setVisible(not embedded)
        self.subtitle_label.setVisible(not embedded)
        self.sign_card.setVisible(not embedded)
        self.assignment_label.setVisible(not embedded)
        self.assignment_combo.setVisible(not embedded)
        self.trimester_label.setVisible(not embedded)
        self.trimester_combo.setVisible(not embedded)
        self.load_button.setVisible(not embedded)

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
            self.btn_vista_previa_cual.setEnabled(False)
            self.btn_exportar_pdf_cual.setEnabled(False)
            self.btn_exportar_excel_cual.setEnabled(False)
            return

        try:
            payload = self.accompaniment_service.cargar_evaluacion(assignment_id, int(trimester_num))
        except ValueError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            self._clear_table()
            self.btn_vista_previa_cual.setEnabled(False)
            self.btn_exportar_pdf_cual.setEnabled(False)
            self.btn_exportar_excel_cual.setEnabled(False)
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
        self.btn_vista_previa_cual.setEnabled(True)
        self.btn_exportar_pdf_cual.setEnabled(True)
        self.btn_exportar_excel_cual.setEnabled(True)
        self._refresh_preview_silent()

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
        self._refresh_preview_silent()

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
        self.btn_vista_previa_cual.setEnabled(False)
        self.btn_exportar_pdf_cual.setEnabled(False)
        self.btn_exportar_excel_cual.setEnabled(False)

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

    def _mostrar_vista_previa_cualitativa(self) -> None:
        try:
            html = self._generar_html_vista_previa()
            self._ultimo_html_vista_previa = html
            self._set_preview_html(html)
            self.tabs.setCurrentIndex(1)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", f"No se pudo generar la vista previa:\n{exc}")

    def _generar_html_vista_previa(self) -> str:
        context = self._construir_contexto_vista_previa()
        return self._renderizar_plantilla_cualitativa(context)

    def _construir_contexto_vista_previa(self) -> dict[str, Any]:
        assignment_id = self.assignment_combo.currentData()
        if not assignment_id:
            raise ValueError("Seleccione una asignación y cargue el listado.")

        contexto = self.accompaniment_service.obtener_contexto(str(assignment_id)) or {}
        if not contexto:
            raise ValueError("No se encontró contexto de la asignación seleccionada.")

        trimestre_actual = int(self.trimester_combo.currentData() or 1)
        trimestre_texto = str(self.trimester_combo.currentText() or f"Trimestre {trimestre_actual}").upper()
        datos_trim_actual = self._get_datos_trimestre(trimestre_actual)
        estudiantes = self._construir_estudiantes_trimestrales(datos_trim_actual)
        stats = self._calcular_stats_cualitativas(datos_trim_actual)

        institucion = self.accompaniment_service.obtener_datos_institucion()
        logo_institucional = HtmlReportRenderer._build_logo_source(institucion.get("logo_path"), "institucional")
        logo_mineduc = HtmlReportRenderer._build_logo_source(institucion.get("logo_ministerio_path"), "ministerio")

        return {
            "docente": self._firmantes.get("docente")
            or f"{contexto.get('docente_apellidos', '')} {contexto.get('docente_nombres', '')}".strip(),
            "curso": contexto.get("curso_nombre") or contexto.get("curso_id", ""),
            "paralelo": contexto.get("paralelo_nombre") or contexto.get("paralelo_id", ""),
            "nivel": contexto.get("curso_nivel") or "",
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "anio_lectivo": contexto.get("periodo_id", ""),
            "trimestre": trimestre_texto,
            "reporte_titulo": f"ACOMPAÑAMIENTO INTEGRAL EN EL AULA - {trimestre_texto} - PERIODO {contexto.get('periodo_id', '')}",
            "rector": self._firmantes.get("rector") or institucion.get("rector", ""),
            "logo_institucion": logo_institucional,
            "logo_ministerio": logo_mineduc,
            "estudiantes": estudiantes,
            "stats": stats,
        }

    def _get_datos_trimestre(self, trimestre: int) -> list[dict[str, str]]:
        assignment_id = self.assignment_combo.currentData()
        if not assignment_id:
            return []
        trimestre_actual = int(self.trimester_combo.currentData() or 1)
        if trimestre == trimestre_actual and self.table.rowCount() > 0:
            return self._leer_datos_desde_tabla_actual()

        payload = self.accompaniment_service.cargar_evaluacion(str(assignment_id), trimestre)
        rows: list[dict[str, str]] = []
        students = payload.get("students", [])
        responses = payload.get("responses", {})
        active_skills = payload.get("active_skills", [])
        for student in students:
            sid = student.get("student_id", "")
            result = self.accompaniment_service.calcular_resultado_estudiante(responses.get(sid, {}), active_skills)
            rows.append(
                {
                    "nombre": student.get("name", ""),
                    "valoracion_final": result.get("valoracion_final", ""),
                }
            )
        return rows

    def _leer_datos_desde_tabla_actual(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        valoracion_col = self._find_column_index("Valoración final")
        if valoracion_col < 0:
            return rows
        for row_idx in range(self.table.rowCount()):
            name_item = self.table.item(row_idx, 1)
            val_item = self.table.item(row_idx, valoracion_col)
            rows.append(
                {
                    "nombre": name_item.text().strip() if name_item else "",
                    "valoracion_final": val_item.text().strip() if val_item else "",
                }
            )
        return rows

    def _construir_estudiantes_trimestrales(self, datos_trimestre: list[dict[str, str]]) -> list[dict[str, str]]:
        estudiantes = []
        for item in sorted(datos_trimestre, key=lambda x: str(x.get("nombre", "")).strip().lower()):
            cual = str(item.get("valoracion_final", "")).strip()
            estudiantes.append(
                {
                    "nombre": str(item.get("nombre", "")).strip(),
                    "cual": cual,
                    "desc": self._obtener_descripcion_cualitativa(cual),
                }
            )
        return estudiantes

    @staticmethod
    def _obtener_descripcion_cualitativa(cual: str) -> str:
        descripciones = {
            "A+": "Supera con excelencia las metas propuestas para las habilidades socioemocionales",
            "A-": "Es excelente el alcance de las metas propuestas para las habilidades socioemocionales",
            "B+": "Es destacado el alcance de las metas propuestas para las habilidades socioemocionales",
            "B-": "Alcanza de las metas propuestas para las habilidades socioemocionales",
            "C+": "En algunas de las habilidades socioemocionales el alcance de las metas propuestas está en progreso",
            "C-": "En la mayoría de las habilidades socioemocionales el alcance de las metas propuestas está en progreso",
            "D+": "En algunas de las habilidades socioemocionales el alcance de las metas propuestas está en inicio",
            "D-": "En la mayoría de las habilidades socioemocionales el alcance de las metas propuestas está en inicio",
            "E+": "Sólo en una de las habilidades socioemocionales se alcanza las metas propuestas",
            "E-": "Requiere acompañamiento individualizado para el desarrollo y fortalecimiento de habilidades socioemocionales.",
        }
        return descripciones.get(str(cual).strip(), "")

    def _calcular_stats_cualitativas(self, estudiantes_trimestre: list[dict[str, str]]) -> dict[str, Any]:
        labels = [("A+", "a_plus"), ("A-", "a_minus"), ("B+", "b_plus"), ("B-", "b_minus"), ("C+", "c_plus"), ("C-", "c_minus"), ("D+", "d_plus"), ("D-", "d_minus"), ("E+", "e_plus"), ("E-", "e_minus")]
        total = len(estudiantes_trimestre)
        counts = {label: 0 for label, _ in labels}
        for row in estudiantes_trimestre:
            cual = str(row.get("valoracion_final", "")).strip()
            if cual in counts:
                counts[cual] += 1

        def pct(value: int) -> str:
            if total == 0:
                return "0,00%"
            return f"{(value * 100 / total):.2f}%".replace(".", ",")

        stats: dict[str, Any] = {}
        for label, key in labels:
            stats[f"{key}_n"] = counts[label]
            stats[f"{key}_p"] = pct(counts[label])
        stats["total_n"] = total
        stats["total_p"] = "100,00%" if total > 0 else "0,00%"
        return stats

    def _find_column_index(self, header_text: str) -> int:
        for col in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(col)
            if item and item.text().strip() == header_text:
                return col
        return -1

    def _renderizar_plantilla_cualitativa(self, context: dict[str, Any]) -> str:
        templates_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "infrastructure",
                "templates",
            )
        )
        env = Environment(loader=FileSystemLoader(templates_dir), autoescape=False)
        template = env.get_template("reporte_cualitativo_anual.html")
        return template.render(**context)

    def _exportar_vista_previa_pdf(self) -> None:
        if QWebEnginePage is None or QEventLoop is None:
            QMessageBox.warning(self, "Exportar PDF", "QWebEngine no está disponible en este entorno.")
            return
        try:
            html = self._generar_html_vista_previa()
            suggested = f"{self._build_export_filename_base()}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", suggested, "PDF (*.pdf)")
            if not file_path:
                return
            if not file_path.lower().endswith(".pdf"):
                file_path = f"{file_path}.pdf"

            page = QWebEnginePage(self)
            loop = QEventLoop(self)
            result = {"ok": False}

            def on_load_finished(ok: bool) -> None:
                if not ok:
                    result["ok"] = False
                    loop.quit()
                    return
                page_layout = QPageLayout(
                    QPageSize(QPageSize.A4),
                    QPageLayout.Portrait,
                    QMarginsF(12, 12, 12, 12),
                    QPageLayout.Millimeter,
                )
                page.printToPdf(file_path, page_layout)

            def on_pdf_done(path: str, success: bool) -> None:
                result["ok"] = success and bool(path)
                loop.quit()

            page.loadFinished.connect(on_load_finished)
            page.pdfPrintingFinished.connect(on_pdf_done)
            page.setHtml(html, QUrl("about:blank"))
            loop.exec()
            if result["ok"]:
                QMessageBox.information(self, "Exportar PDF", f"PDF generado correctamente:\n{file_path}")
            else:
                QMessageBox.warning(self, "Exportar PDF", "No se pudo generar el PDF.")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Exportar PDF", f"Error al exportar PDF:\n{exc}")

    def _exportar_excel(self) -> None:
        assignment_id = self.assignment_combo.currentData()
        if not assignment_id:
            QMessageBox.warning(self, "Exportar Excel", "Seleccione una asignación y cargue el listado.")
            return
        self._collect_responses_from_table()
        suggested = f"{self._build_export_filename_base()}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", suggested, "Excel (*.xlsx)")
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path = f"{file_path}.xlsx"

        headers = ["Nómina"] + [self._skills_by_key[key]["label"] for key in self._active_skills if key in self._skills_by_key]
        wb = Workbook()
        ws = wb.active
        ws.title = "Acom. Inte. Aula."
        ws.append(headers)
        for student in self._students:
            sid = student.get("student_id", "")
            row = [student.get("name", "")]
            skill_values = self._responses.get(sid, {})
            for skill_key in self._active_skills:
                row.append(skill_values.get(skill_key, ""))
            ws.append(row)
        wb.save(file_path)
        QMessageBox.information(self, "Exportar Excel", f"Excel generado correctamente:\n{file_path}")

    def _build_export_filename_base(self) -> str:
        assignment_text = self.assignment_combo.currentText() or "acompanamiento"
        return self._sanitize_filename(assignment_text)

    @staticmethod
    def _sanitize_filename(text: str) -> str:
        import re

        normalized = re.sub(r"[|/\\\\:*?\"<>]+", "_", str(text or "").strip())
        normalized = re.sub(r"\s+", "_", normalized)
        normalized = re.sub(r"_+", "_", normalized)
        normalized = normalized.strip(" ._")
        return normalized or "acompanamiento"

    def _load_signer_options(self) -> None:
        options = self.accompaniment_service.listar_firmantes_disponibles()
        self.signer_docente_combo.clear()
        self.signer_rector_combo.clear()
        self.signer_docente_combo.addItem("Seleccione", "")
        self.signer_rector_combo.addItem("Seleccione", "")
        for name in options:
            self.signer_docente_combo.addItem(name, name)
            self.signer_rector_combo.addItem(name, name)
        self._update_signers()

    def _update_signers(self) -> None:
        self._firmantes = {
            "docente": self.signer_docente_combo.currentData() or "",
            "rector": self.signer_rector_combo.currentData() or "",
        }
        self._refresh_preview_silent()

    def _on_context_filters_changed(self) -> None:
        self.load_rows()

    def _refresh_preview_silent(self) -> None:
        assignment_id = self.assignment_combo.currentData()
        if not assignment_id:
            self._set_preview_html("")
            return
        try:
            html = self._generar_html_vista_previa()
        except Exception:  # noqa: BLE001
            return
        self._ultimo_html_vista_previa = html
        self._set_preview_html(html)

    def _set_preview_html(self, html_content: str) -> None:
        if self._preview_uses_webengine:
            self.preview_view.setHtml(html_content)
        else:
            self.preview_view.setHtml(html_content)


class VistaPreviaCualitativaDialog(QDialog):
    def __init__(self, html_content: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Vista Previa - Reporte Cualitativo Anual")
        self.setMinimumSize(860, 700)
        self.resize(900, 750)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if QWebEngineView is not None and QUrl is not None:
            self.web_view = QWebEngineView()
            self.web_view.setHtml(html_content, QUrl("about:blank"))
            layout.addWidget(self.web_view)
            return

        fallback = QLabel("Vista previa HTML no disponible (QWebEngine no está instalado).")
        fallback.setWordWrap(True)
        layout.addWidget(fallback)
