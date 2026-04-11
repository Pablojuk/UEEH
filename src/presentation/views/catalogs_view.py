"""Vista funcional para gestión de catálogos."""

from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.application.services.catalog_service import CatalogService


class CatalogsView(QWidget):
    def __init__(self, catalog_service: CatalogService) -> None:
        super().__init__()
        self.catalog_service = catalog_service
        self.editing_course_id: str | None = None
        self.editing_parallel_id: str | None = None
        self.editing_subject_id: str | None = None
        self.editing_period_id: str | None = None

        root = QVBoxLayout(self)

        title = QLabel("Catálogos")
        title.setObjectName("Title")
        subtitle = QLabel("Gestión de cursos, paralelos, asignaturas y períodos lectivos")
        subtitle.setObjectName("Subtitle")

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_courses_tab(), "Cursos")
        self.tabs.addTab(self._build_parallels_tab(), "Paralelos")
        self.tabs.addTab(self._build_subjects_tab(), "Asignaturas")
        self.tabs.addTab(self._build_periods_tab(), "Períodos")

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(self.tabs, 1)

        self.refresh_all()

    def _build_courses_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)
        self.course_id_input = QLineEdit()
        self.course_name_input = QLineEdit()
        self.course_level_input = QLineEdit()
        form.addRow("ID curso", self.course_id_input)
        form.addRow("Nombre", self.course_name_input)
        form.addRow("Nivel", self.course_level_input)

        actions = QHBoxLayout()
        self.save_course_button = QPushButton("Guardar")
        self.save_course_button.clicked.connect(self.save_course)
        self.delete_course_button = QPushButton("Borrar")
        self.delete_course_button.clicked.connect(self.delete_course)
        actions.addWidget(self.save_course_button)
        actions.addWidget(self.delete_course_button)
        actions.addStretch(1)

        self.courses_table = QTableWidget(0, 3)
        self.courses_table.setHorizontalHeaderLabels(["ID", "Nombre", "Nivel"])
        self.courses_table.horizontalHeader().setStretchLastSection(True)
        self.courses_table.cellClicked.connect(self.select_course)

        layout.addWidget(card)
        layout.addLayout(actions)
        layout.addWidget(self.courses_table, 1)
        return tab

    def _build_parallels_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)
        self.parallel_id_input = QLineEdit()
        self.parallel_name_input = QLineEdit()
        form.addRow("ID paralelo", self.parallel_id_input)
        form.addRow("Nombre", self.parallel_name_input)

        actions = QHBoxLayout()
        self.save_parallel_button = QPushButton("Guardar")
        self.save_parallel_button.clicked.connect(self.save_parallel)
        self.delete_parallel_button = QPushButton("Borrar")
        self.delete_parallel_button.clicked.connect(self.delete_parallel)
        actions.addWidget(self.save_parallel_button)
        actions.addWidget(self.delete_parallel_button)
        actions.addStretch(1)

        self.parallels_table = QTableWidget(0, 2)
        self.parallels_table.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.parallels_table.horizontalHeader().setStretchLastSection(True)
        self.parallels_table.cellClicked.connect(self.select_parallel)

        layout.addWidget(card)
        layout.addLayout(actions)
        layout.addWidget(self.parallels_table, 1)
        return tab

    def _build_subjects_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)
        self.subject_id_input = QLineEdit()
        self.subject_name_input = QLineEdit()
        form.addRow("ID asignatura", self.subject_id_input)
        form.addRow("Nombre", self.subject_name_input)

        actions = QHBoxLayout()
        self.save_subject_button = QPushButton("Guardar")
        self.save_subject_button.clicked.connect(self.save_subject)
        self.delete_subject_button = QPushButton("Borrar")
        self.delete_subject_button.clicked.connect(self.delete_subject)
        actions.addWidget(self.save_subject_button)
        actions.addWidget(self.delete_subject_button)
        actions.addStretch(1)

        self.subjects_table = QTableWidget(0, 2)
        self.subjects_table.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.subjects_table.horizontalHeader().setStretchLastSection(True)
        self.subjects_table.cellClicked.connect(self.select_subject)

        layout.addWidget(card)
        layout.addLayout(actions)
        layout.addWidget(self.subjects_table, 1)
        return tab

    def _build_periods_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)
        self.period_id_input = QLineEdit()
        self.period_start_input = QLineEdit()
        self.period_end_input = QLineEdit()
        form.addRow("ID período", self.period_id_input)
        form.addRow("Año inicio", self.period_start_input)
        form.addRow("Año fin", self.period_end_input)

        actions = QHBoxLayout()
        self.save_period_button = QPushButton("Guardar")
        self.save_period_button.clicked.connect(self.save_period)
        self.delete_period_button = QPushButton("Borrar")
        self.delete_period_button.clicked.connect(self.delete_period)
        actions.addWidget(self.save_period_button)
        actions.addWidget(self.delete_period_button)
        actions.addStretch(1)

        self.periods_table = QTableWidget(0, 3)
        self.periods_table.setHorizontalHeaderLabels(["ID", "Año inicio", "Año fin"])
        self.periods_table.horizontalHeader().setStretchLastSection(True)
        self.periods_table.cellClicked.connect(self.select_period)

        layout.addWidget(card)
        layout.addLayout(actions)
        layout.addWidget(self.periods_table, 1)
        return tab

    def save_course(self) -> None:
        payload = {
            "id_curso": self.course_id_input.text().strip(),
            "nombre": self.course_name_input.text().strip(),
            "nivel": self.course_level_input.text().strip(),
        }
        if not all(payload.values()):
            QMessageBox.warning(self, "Validación", "Complete todos los campos de curso.")
            return
        try:
            if self.editing_course_id:
                self.catalog_service.actualizar_curso(self.editing_course_id, payload)
            else:
                self.catalog_service.crear_curso(payload)
        except sqlite3.IntegrityError as exc:
            QMessageBox.warning(self, "Validación", f"No se pudo guardar curso: {exc}")
            return
        self.editing_course_id = None
        self.course_id_input.clear()
        self.course_name_input.clear()
        self.course_level_input.clear()
        self.course_id_input.setEnabled(True)
        self.courses_table.clearSelection()
        self.refresh_courses()

    def save_parallel(self) -> None:
        payload = {
            "id_paralelo": self.parallel_id_input.text().strip(),
            "nombre": self.parallel_name_input.text().strip(),
        }
        if not all(payload.values()):
            QMessageBox.warning(self, "Validación", "Complete todos los campos de paralelo.")
            return
        try:
            if self.editing_parallel_id:
                self.catalog_service.actualizar_paralelo(self.editing_parallel_id, payload)
            else:
                self.catalog_service.crear_paralelo(payload)
        except sqlite3.IntegrityError as exc:
            QMessageBox.warning(self, "Validación", f"No se pudo guardar paralelo: {exc}")
            return
        self.editing_parallel_id = None
        self.parallel_id_input.clear()
        self.parallel_name_input.clear()
        self.parallel_id_input.setEnabled(True)
        self.parallels_table.clearSelection()
        self.refresh_parallels()

    def save_subject(self) -> None:
        payload = {
            "id_asignatura": self.subject_id_input.text().strip(),
            "nombre": self.subject_name_input.text().strip(),
            "codigo": None,
        }
        if not payload["id_asignatura"] or not payload["nombre"]:
            QMessageBox.warning(self, "Validación", "ID y nombre de asignatura son obligatorios.")
            return
        try:
            if self.editing_subject_id:
                self.catalog_service.actualizar_asignatura(self.editing_subject_id, payload)
            else:
                self.catalog_service.crear_asignatura(payload)
        except sqlite3.IntegrityError as exc:
            QMessageBox.warning(self, "Validación", f"No se pudo guardar asignatura: {exc}")
            return
        self.editing_subject_id = None
        self.subject_id_input.clear()
        self.subject_name_input.clear()
        self.subject_id_input.setEnabled(True)
        self.subjects_table.clearSelection()
        self.refresh_subjects()

    def save_period(self) -> None:
        try:
            payload = {
                "id_periodo": self.period_id_input.text().strip(),
                "anio_inicio": int(self.period_start_input.text().strip()),
                "anio_fin": int(self.period_end_input.text().strip()),
                "fecha_inicio": None,
                "fecha_fin": None,
            }
        except ValueError:
            QMessageBox.warning(self, "Validación", "Año inicio y fin deben ser numéricos.")
            return

        if not payload["id_periodo"]:
            QMessageBox.warning(self, "Validación", "El ID del período es obligatorio.")
            return

        try:
            if self.editing_period_id:
                self.catalog_service.actualizar_periodo_lectivo(self.editing_period_id, payload)
            else:
                self.catalog_service.crear_periodo_lectivo(payload)
        except sqlite3.IntegrityError as exc:
            QMessageBox.warning(self, "Validación", f"No se pudo guardar período: {exc}")
            return
        self.editing_period_id = None
        self.period_id_input.clear()
        self.period_start_input.clear()
        self.period_end_input.clear()
        self.period_id_input.setEnabled(True)
        self.periods_table.clearSelection()
        self.refresh_periods()

    def delete_course(self) -> None:
        if not self.editing_course_id:
            QMessageBox.warning(self, "Validación", "Seleccione un curso de la tabla.")
            return
        if QMessageBox.question(self, "Confirmación", "¿Desea borrar el curso seleccionado?") != QMessageBox.Yes:
            return
        try:
            self.catalog_service.eliminar_curso(self.editing_course_id)
        except sqlite3.IntegrityError as exc:
            QMessageBox.warning(self, "Validación", f"No se pudo borrar curso: {exc}")
            return
        self.editing_course_id = None
        self.course_id_input.clear()
        self.course_name_input.clear()
        self.course_level_input.clear()
        self.course_id_input.setEnabled(True)
        self.courses_table.clearSelection()
        self.refresh_courses()

    def delete_parallel(self) -> None:
        if not self.editing_parallel_id:
            QMessageBox.warning(self, "Validación", "Seleccione un paralelo de la tabla.")
            return
        if QMessageBox.question(self, "Confirmación", "¿Desea borrar el paralelo seleccionado?") != QMessageBox.Yes:
            return
        try:
            self.catalog_service.eliminar_paralelo(self.editing_parallel_id)
        except sqlite3.IntegrityError as exc:
            QMessageBox.warning(self, "Validación", f"No se pudo borrar paralelo: {exc}")
            return
        self.editing_parallel_id = None
        self.parallel_id_input.clear()
        self.parallel_name_input.clear()
        self.parallel_id_input.setEnabled(True)
        self.parallels_table.clearSelection()
        self.refresh_parallels()

    def delete_subject(self) -> None:
        if not self.editing_subject_id:
            QMessageBox.warning(self, "Validación", "Seleccione una asignatura de la tabla.")
            return
        if QMessageBox.question(self, "Confirmación", "¿Desea borrar la asignatura seleccionada?") != QMessageBox.Yes:
            return
        try:
            self.catalog_service.eliminar_asignatura(self.editing_subject_id)
        except sqlite3.IntegrityError as exc:
            QMessageBox.warning(self, "Validación", f"No se pudo borrar asignatura: {exc}")
            return
        self.editing_subject_id = None
        self.subject_id_input.clear()
        self.subject_name_input.clear()
        self.subject_id_input.setEnabled(True)
        self.subjects_table.clearSelection()
        self.refresh_subjects()

    def delete_period(self) -> None:
        if not self.editing_period_id:
            QMessageBox.warning(self, "Validación", "Seleccione un período de la tabla.")
            return
        if QMessageBox.question(self, "Confirmación", "¿Desea borrar el período seleccionado?") != QMessageBox.Yes:
            return
        try:
            self.catalog_service.eliminar_periodo_lectivo(self.editing_period_id)
        except sqlite3.IntegrityError as exc:
            QMessageBox.warning(self, "Validación", f"No se pudo borrar período: {exc}")
            return
        self.editing_period_id = None
        self.period_id_input.clear()
        self.period_start_input.clear()
        self.period_end_input.clear()
        self.period_id_input.setEnabled(True)
        self.periods_table.clearSelection()
        self.refresh_periods()

    def refresh_all(self) -> None:
        self.refresh_courses()
        self.refresh_parallels()
        self.refresh_subjects()
        self.refresh_periods()

    def refresh_courses(self) -> None:
        rows = self.catalog_service.listar_cursos()
        self._fill_table(self.courses_table, rows, ["id_curso", "nombre", "nivel"])

    def refresh_parallels(self) -> None:
        rows = self.catalog_service.listar_paralelos()
        self._fill_table(self.parallels_table, rows, ["id_paralelo", "nombre"])

    def refresh_subjects(self) -> None:
        rows = self.catalog_service.listar_asignaturas()
        self._fill_table(self.subjects_table, rows, ["id_asignatura", "nombre"])

    def refresh_periods(self) -> None:
        rows = self.catalog_service.listar_periodos_lectivos()
        self._fill_table(self.periods_table, rows, ["id_periodo", "anio_inicio", "anio_fin"])

    @staticmethod
    def _fill_table(table: QTableWidget, rows: list[dict], columns: list[str]) -> None:
        table.setRowCount(0)
        for row_data in rows:
            row = table.rowCount()
            table.insertRow(row)
            for column_index, key in enumerate(columns):
                value = row_data.get(key, "")
                table.setItem(row, column_index, QTableWidgetItem(str(value if value is not None else "")))

    def select_course(self, row: int, _column: int) -> None:
        self.editing_course_id = self.courses_table.item(row, 0).text()
        self.course_id_input.setText(self.editing_course_id)
        self.course_id_input.setEnabled(False)
        self.course_name_input.setText(self.courses_table.item(row, 1).text())
        self.course_level_input.setText(self.courses_table.item(row, 2).text())

    def select_parallel(self, row: int, _column: int) -> None:
        self.editing_parallel_id = self.parallels_table.item(row, 0).text()
        self.parallel_id_input.setText(self.editing_parallel_id)
        self.parallel_id_input.setEnabled(False)
        self.parallel_name_input.setText(self.parallels_table.item(row, 1).text())

    def select_subject(self, row: int, _column: int) -> None:
        self.editing_subject_id = self.subjects_table.item(row, 0).text()
        self.subject_id_input.setText(self.editing_subject_id)
        self.subject_id_input.setEnabled(False)
        self.subject_name_input.setText(self.subjects_table.item(row, 1).text())

    def select_period(self, row: int, _column: int) -> None:
        self.editing_period_id = self.periods_table.item(row, 0).text()
        self.period_id_input.setText(self.editing_period_id)
        self.period_id_input.setEnabled(False)
        self.period_start_input.setText(self.periods_table.item(row, 1).text())
        self.period_end_input.setText(self.periods_table.item(row, 2).text())
