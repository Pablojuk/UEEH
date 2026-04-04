"""Vista funcional para gestión de catálogos."""

from __future__ import annotations

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

        save_button = QPushButton("Guardar curso")
        save_button.clicked.connect(self.save_course)

        self.courses_table = QTableWidget(0, 3)
        self.courses_table.setHorizontalHeaderLabels(["ID", "Nombre", "Nivel"])
        self.courses_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(card)
        layout.addWidget(save_button)
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

        save_button = QPushButton("Guardar paralelo")
        save_button.clicked.connect(self.save_parallel)

        self.parallels_table = QTableWidget(0, 2)
        self.parallels_table.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.parallels_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(card)
        layout.addWidget(save_button)
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
        self.subject_code_input = QLineEdit()
        form.addRow("ID asignatura", self.subject_id_input)
        form.addRow("Nombre", self.subject_name_input)
        form.addRow("Código", self.subject_code_input)

        save_button = QPushButton("Guardar asignatura")
        save_button.clicked.connect(self.save_subject)

        self.subjects_table = QTableWidget(0, 3)
        self.subjects_table.setHorizontalHeaderLabels(["ID", "Nombre", "Código"])
        self.subjects_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(card)
        layout.addWidget(save_button)
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

        save_button = QPushButton("Guardar período")
        save_button.clicked.connect(self.save_period)

        self.periods_table = QTableWidget(0, 3)
        self.periods_table.setHorizontalHeaderLabels(["ID", "Año inicio", "Año fin"])
        self.periods_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(card)
        layout.addWidget(save_button)
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
        self.catalog_service.crear_curso(payload)
        self.course_id_input.clear()
        self.course_name_input.clear()
        self.course_level_input.clear()
        self.refresh_courses()

    def save_parallel(self) -> None:
        payload = {
            "id_paralelo": self.parallel_id_input.text().strip(),
            "nombre": self.parallel_name_input.text().strip(),
        }
        if not all(payload.values()):
            QMessageBox.warning(self, "Validación", "Complete todos los campos de paralelo.")
            return
        self.catalog_service.crear_paralelo(payload)
        self.parallel_id_input.clear()
        self.parallel_name_input.clear()
        self.refresh_parallels()

    def save_subject(self) -> None:
        payload = {
            "id_asignatura": self.subject_id_input.text().strip(),
            "nombre": self.subject_name_input.text().strip(),
            "codigo": self.subject_code_input.text().strip() or None,
        }
        if not payload["id_asignatura"] or not payload["nombre"]:
            QMessageBox.warning(self, "Validación", "ID y nombre de asignatura son obligatorios.")
            return
        self.catalog_service.crear_asignatura(payload)
        self.subject_id_input.clear()
        self.subject_name_input.clear()
        self.subject_code_input.clear()
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

        self.catalog_service.crear_periodo_lectivo(payload)
        self.period_id_input.clear()
        self.period_start_input.clear()
        self.period_end_input.clear()
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
        self._fill_table(self.subjects_table, rows, ["id_asignatura", "nombre", "codigo"])

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
