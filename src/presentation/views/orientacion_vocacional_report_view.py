"""Vista de reportes para Orientación Vocacional y Profesional."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from PySide6.QtCore import QUrl
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
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
from openpyxl import Workbook

from src.infrastructure.exporters.html_report_renderer import HtmlReportRenderer
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:  # noqa: BLE001
    QWebEngineView = None


class OrientacionVocacionalReportView(QWidget):
    def __init__(
        self,
        list_signers: Callable[[], list[str]] | None = None,
        get_assignment_context: Callable[[str], dict[str, Any] | None] | None = None,
        get_institution_data: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        super().__init__()
        self._list_signers = list_signers
        self._get_assignment_context = get_assignment_context
        self._get_institution_data = get_institution_data
        self._assignment_id: str | None = None
        self._trimester_num: int | None = None
        self._students: list[dict[str, Any]] = []
        self._last_preview_html = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        self.report_filter_card = QFrame()
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
        actions_layout = QHBoxLayout(self.actions_card)
        self.preview_button = QPushButton("Vista Previa")
        self.preview_button.clicked.connect(self._show_preview)
        self.export_pdf_button = QPushButton("Exportar PDF")
        self.export_pdf_button.clicked.connect(self._export_preview_pdf)
        self.export_excel_button = QPushButton("Exportar Excel")
        self.export_excel_button.clicked.connect(self._export_preview_excel)
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

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["N°", "Nómina de Estudiantes", "Cualitativo", "Descripción"])

        self.tabs = QTabWidget()
        eval_tab = QWidget()
        eval_layout = QVBoxLayout(eval_tab)
        eval_layout.setContentsMargins(0, 0, 0, 0)
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
        preview_layout.addWidget(self.preview_view, 1)
        self.tabs.addTab(preview_tab, "Vista previa")

        root.addWidget(self.report_filter_card)
        root.addWidget(self.actions_card)
        root.addWidget(self.sign_card)
        root.addWidget(self.tabs, 1)

        self._load_signers()

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

    def set_context(self, assignment_id: str | None, trimester_num: int | None) -> None:
        self._assignment_id = assignment_id
        self._trimester_num = trimester_num

    def set_students(self, students: list[dict[str, Any]]) -> None:
        self._students = students
        self.table.setRowCount(len(students))
        for index, student in enumerate(students, start=1):
            self.table.setItem(index - 1, 0, QTableWidgetItem(str(index)))
            self.table.setItem(index - 1, 1, QTableWidgetItem(str(student.get("estudiante") or "")))
            calificacion = str(student.get("calificacion") or "").strip()
            self.table.setItem(index - 1, 2, QTableWidgetItem(calificacion))
            self.table.setItem(index - 1, 3, QTableWidgetItem(self._descripcion_por_cualitativo(calificacion)))
        self._refresh_preview()

    @staticmethod
    def _descripcion_por_cualitativo(cualitativo: str) -> str:
        mapping = {"A+": "Siempre", "A-": "Frecuentemente", "B+": "Ocasionalmente"}
        return mapping.get(str(cualitativo or "").strip().upper(), "Sin información")

    def _build_preview_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for index, student in enumerate(self._students, start=1):
            calificacion = str(student.get("calificacion") or "").strip()
            rows.append(
                {
                    "nro": str(index),
                    "nomina": str(student.get("estudiante") or ""),
                    "cualitativo": calificacion,
                    "descripcion": self._descripcion_por_cualitativo(calificacion),
                }
            )
        return rows

    def _build_stats_summary(self) -> dict[str, Any]:
        rows = self._build_preview_rows()
        total = len(rows)
        counts = {"A+": 0, "A-": 0, "B+": 0}
        for row in rows:
            key = str(row.get("cualitativo") or "").strip().upper()
            if key in counts:
                counts[key] += 1

        def pct(value: int) -> str:
            if total == 0:
                return "0,00%"
            return f"{(value * 100 / total):.2f}%".replace(".", ",")

        return {
            "rows": [{"escala": key, "numero": counts[key], "porcentaje": pct(counts[key])} for key in ("A+", "A-", "B+")],
            "total_n": total,
            "total_p": "100,00%" if total > 0 else "0,00%",
        }

    def _build_preview_context(self) -> dict[str, Any]:
        if not self._assignment_id or not self._trimester_num:
            raise ValueError("Seleccione una asignación y trimestre.")
        assignment_context = self._get_assignment_context(str(self._assignment_id)) if self._get_assignment_context else {}
        assignment_context = assignment_context or {}
        institution_data = self._get_institution_data() if self._get_institution_data else {}
        institution_data = institution_data or {}
        docente_default = f"{assignment_context.get('docente_apellidos', '')} {assignment_context.get('docente_nombres', '')}".strip()
        trimestre_label = f"TRIMESTRE {self._trimester_num}"
        return {
            "docente": self.sign_docente_combo.currentText().strip() or docente_default,
            "curso": assignment_context.get("curso_nombre") or assignment_context.get("curso_id", ""),
            "paralelo": assignment_context.get("paralelo_nombre") or assignment_context.get("paralelo_id", ""),
            "nivel": assignment_context.get("curso_nivel", ""),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "anio_lectivo": assignment_context.get("periodo_id", ""),
            "trimestre": trimestre_label,
            "reporte_titulo": f"ORIENTACIÓN VOCACIONAL Y PROFESIONAL - {trimestre_label}",
            "rector": self.sign_rector_combo.currentText().strip() or institution_data.get("rector", ""),
            "logo_institucion": HtmlReportRenderer._build_logo_source(institution_data.get("logo_path"), "institucional"),
            "logo_ministerio": HtmlReportRenderer._build_logo_source(institution_data.get("logo_ministerio_path"), "ministerio"),
            "stats": self._build_stats_summary(),
        }

    def _render_preview_html(self) -> str:
        context = self._build_preview_context()
        return HtmlReportRenderer().render_orientacion_vocacional(context, self._build_preview_rows())

    def _refresh_preview(self) -> None:
        try:
            html = self._render_preview_html()
        except Exception:  # noqa: BLE001
            html = ""
        self._last_preview_html = html
        self._set_preview_html(html)

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
        html = self._last_preview_html or self._render_preview_html()
        suggested = f"orientacion_vocacional_{self._assignment_id or 'reporte'}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", suggested, "PDF (*.pdf)")
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path = f"{file_path}.pdf"

        document = QTextDocument()
        document.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        document.print(printer)
        QMessageBox.information(self, "Exportar PDF", f"PDF generado correctamente:\n{file_path}")

    def _export_preview_excel(self) -> None:
        rows = self._build_preview_rows()
        stats = self._build_stats_summary()
        suggested = f"orientacion_vocacional_{self._assignment_id or 'reporte'}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", suggested, "Excel (*.xlsx)")
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path = f"{file_path}.xlsx"

        wb = Workbook()
        ws = wb.active
        ws.title = "Orientación Vocacional"
        ws.append(["N°", "Nómina de Estudiantes", "Cualitativo", "Descripción"])
        for row in rows:
            ws.append([row["nro"], row["nomina"], row["cualitativo"], row["descripcion"]])
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
