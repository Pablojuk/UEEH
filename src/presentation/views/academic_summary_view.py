"""Vista de resumen académico anual y supletorio."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.application.services.academic_summary_service import AcademicSummaryService
from src.application.services.report_export_service import ReportExportService


class AcademicSummaryView(QWidget):
    TABLE_COLUMNS = [
        ("estudiante", "Estudiante"),
        ("trimestre_1", "Trimestre 1"),
        ("trimestre_2", "Trimestre 2"),
        ("trimestre_3", "Trimestre 3"),
        ("promedio_final", "Promedio Final"),
        ("cualitativo", "Cualitativo"),
        ("observacion", "Observación"),
        ("supletorio", "Supletorio"),
        ("nota_definitiva", "Nota Definitiva"),
    ]

    EDITABLE_COLUMNS = {"supletorio"}

    def __init__(
        self,
        academic_summary_service: AcademicSummaryService,
        report_export_service: ReportExportService | None = None,
    ) -> None:
        super().__init__()
        self.academic_summary_service = academic_summary_service
        self.report_export_service = report_export_service
        self._rows_meta: list[dict] = []

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
        self.assignment_combo.setMinimumWidth(380)
        self.load_button = QPushButton("Cargar resumen")
        self.load_button.clicked.connect(self.load_summary)
        self.recalc_button = QPushButton("Recalcular")
        self.recalc_button.clicked.connect(self.recalculate_rows)
        self.save_button = QPushButton("Guardar supletorio")
        self.save_button.clicked.connect(self.save_rows)
        self.export_pdf_button = QPushButton("Exportar PDF")
        self.export_pdf_button.clicked.connect(self.export_pdf)
        self.export_excel_button = QPushButton("Exportar Excel")
        self.export_excel_button.clicked.connect(self.export_excel)

        filter_row.addWidget(QLabel("Asignación"))
        filter_row.addWidget(self.assignment_combo, 1)
        filter_row.addWidget(self.load_button)
        filter_row.addWidget(self.recalc_button)
        filter_row.addWidget(self.save_button)
        filter_row.addWidget(self.export_pdf_button)
        filter_row.addWidget(self.export_excel_button)

        self.table = QTableWidget(0, len(self.TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels([label for _, label in self.TABLE_COLUMNS])
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(filter_card)
        root.addWidget(self.table, 1)

        self.load_contexts()

    def load_contexts(self) -> None:
        self.assignment_combo.clear()
        contexts = self.academic_summary_service.listar_contextos_disponibles()
        if not contexts:
            self.assignment_combo.addItem("Sin asignaciones disponibles", None)
            return

        for row in contexts:
            self.assignment_combo.addItem(row.get("display", row.get("id_asignacion", "")), row.get("id_asignacion"))

    def load_summary(self) -> None:
        asignacion_id = self.assignment_combo.currentData()
        if not asignacion_id:
            self._fill_table([])
            return

        rows = self.academic_summary_service.obtener_resumen_por_asignacion(asignacion_id)
        self._fill_table(rows)

    def recalculate_rows(self) -> None:
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

        default_name = f"reporte_{asignacion_id}.{ 'pdf' if kind == 'pdf' else 'xlsx' }"
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte",
            default_name,
            "PDF (*.pdf)" if kind == "pdf" else "Excel (*.xlsx)",
        )
        if not selected_path:
            return

        if kind == "pdf":
            ok, message = self.report_export_service.exportar_resumen_pdf(asignacion_id, selected_path)
        else:
            ok, message = self.report_export_service.exportar_resumen_excel(asignacion_id, selected_path)

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
            for col, (field, _) in enumerate(self.TABLE_COLUMNS):
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
            for col, (field, _) in enumerate(self.TABLE_COLUMNS):
                item = self.table.item(row_idx, col)
                text = item.text().strip() if item else ""
                row_data[field] = text if text != "" else None
            rows.append(row_data)
        return rows
