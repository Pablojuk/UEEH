"""Vista especial de evaluación para Orientación Vocacional y Profesional."""

from __future__ import annotations

import unicodedata
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class OrientacionVocacionalView(QWidget):
    RESPONSE_OPTIONS = [("-", None), ("SIEMPRE", 3), ("FRECUENTEMENTE", 2), ("OCASIONALMENTE", 1)]
    COURSE_CONFIG: dict[str, dict[str, Any]] = {
        "8": {
            "title": "INDICADORES DEL EJE DE AUTOCONOCIMIENTO 8° AÑO DE EGB",
            "indicators": [
                "Reconoce sus fortalezas y desafíos",
                "Entiende y habla de sus necesidades...",
                "Reconoce necesidades de otras personas",
                "Se da cuenta cómo su comportamiento afecta a los demás",
                "Aprende de sus errores y mira posibilidades de crecimiento",
            ],
        },
        "9": {
            "title": "INDICADORES EJE DE INFORMACIÓN 9° AÑO EGB",
            "indicators": [
                "Conoce como acceder a información necesaria",
                "Conoce alternativas de opciones de estudios, ocupaciones y planes de carrera",
                "Encuentra la solución a problemas tomando en cuenta otros criterios",
                "Comparte y expresa información de diferentes áreas de conocimiento",
                "Aprende de sus errores y mira posibilidades de crecimiento",
            ],
        },
        "10": {
            "title": "INDICADORES DEL EJE DE TOMA DE DECISIONES 10° EGB",
            "indicators": [
                "Expresa motivación para la toma de decisiones con respecto a su plan de vida",
                "Identifica soluciones alternativas",
                "Identifica la decisión que se debe tomar",
                "Revisa los pros y contra cuando debe tomar una decisión",
                "Expresa seguridad y autonomía en la toma de decisiones",
            ],
        },
    }

    def __init__(self, on_save_payload: Callable[[dict[str, Any]], tuple[bool, str]] | None = None) -> None:
        super().__init__()
        self._on_save_payload = on_save_payload
        self._students: list[dict[str, str]] = []
        self._assignment_id: str | None = None
        self._trimester_num: int | None = None
        self._course_name: str = ""
        self._course_key: str | None = None
        self._saved_by_student: dict[str, dict[str, Any]] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        header_card = QFrame()
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("Orientación Vocacional y Profesional")
        self.course_label = QLabel("")
        self.save_button = QPushButton("Guardar evaluación")
        self.save_button.clicked.connect(self._save_rows)
        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.course_label)
        header_layout.addWidget(self.save_button)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["N°", "Nómina / Estudiante", "Indicador 1", "Indicador 2", "Indicador 3", "Indicador 4", "Indicador 5", "Calificación"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeToContents)
        header.setSectionResizeMode(1, header.Stretch)
        for col in range(2, 7):
            header.setSectionResizeMode(col, header.ResizeToContents)
        header.setSectionResizeMode(7, header.ResizeToContents)

        root.addWidget(header_card)
        root.addWidget(self.table, 1)

    def set_context(self, assignment_id: str | None, trimester_num: int | None, course_name: str) -> None:
        self._assignment_id = assignment_id
        self._trimester_num = trimester_num
        self._course_name = str(course_name or "")
        self._course_key = self.detect_course_key(self._course_name)
        self.course_label.setText(self._course_name)
        self._update_title()

    def set_students(self, students: list[dict[str, str]], saved_rows: list[dict[str, Any]] | None = None) -> None:
        self._students = students
        self._saved_by_student = {str(row.get("estudiante_id") or ""): row for row in (saved_rows or []) if str(row.get("estudiante_id") or "").strip()}
        self._build_table()

    def _update_title(self) -> None:
        if self._course_key in self.COURSE_CONFIG:
            self.title_label.setText(str(self.COURSE_CONFIG[self._course_key]["title"]))
        else:
            self.title_label.setText("Orientación Vocacional y Profesional")

    def _build_table(self) -> None:
        self.table.setRowCount(0)
        indicators = self.COURSE_CONFIG.get(str(self._course_key or ""), {}).get("indicators", [])
        for index, student in enumerate(self._students, start=1):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._set_text_item(row, 0, str(index), editable=False)
            self._set_text_item(row, 1, str(student.get("estudiante") or ""), editable=False)
            saved = self._saved_by_student.get(str(student.get("estudiante_id") or ""))
            saved_responses = saved.get("respuestas") if isinstance(saved, dict) else None
            if not isinstance(saved_responses, list):
                saved_responses = []
            for col in range(5):
                combo = QComboBox()
                combo.setEditable(False)
                for label, value in self.RESPONSE_OPTIONS:
                    combo.addItem(label, value)
                default_value = saved_responses[col] if col < len(saved_responses) else None
                combo_index = combo.findData(default_value)
                combo.setCurrentIndex(combo_index if combo_index >= 0 else 0)
                combo.currentIndexChanged.connect(lambda _=0, r=row: self._recalculate_row(r))
                combo.setToolTip(str(indicators[col]) if col < len(indicators) else "")
                self.table.setCellWidget(row, 2 + col, combo)
            saved_calificacion = str((saved or {}).get("calificacion") or "").strip() if isinstance(saved, dict) else ""
            self._set_text_item(row, 7, saved_calificacion or "-", editable=False)
            self._recalculate_row(row)

    def _set_text_item(self, row: int, col: int, text: str, editable: bool) -> None:
        item = QTableWidgetItem(text)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, col, item)

    def _recalculate_row(self, row: int) -> None:
        values: list[int] = []
        for col in range(2, 7):
            combo = self.table.cellWidget(row, col)
            if not isinstance(combo, QComboBox):
                continue
            value = combo.currentData()
            if value is None:
                self._set_calification(row, "-")
                return
            values.append(int(value))
        if len(values) != 5:
            self._set_calification(row, "-")
            return
        total = sum(values)
        if 14 <= total <= 15:
            grade = "A+"
        elif 10 <= total <= 13:
            grade = "A-"
        else:
            grade = "B+"
        self._set_calification(row, grade)

    def _set_calification(self, row: int, value: str) -> None:
        item = self.table.item(row, 7)
        if item is None:
            self._set_text_item(row, 7, value, editable=False)
            return
        item.setText(value)

    def build_save_payload(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for row in range(self.table.rowCount()):
            student = self._students[row] if row < len(self._students) else {}
            responses: list[int | None] = []
            total: int | None = 0
            for col in range(2, 7):
                combo = self.table.cellWidget(row, col)
                value = combo.currentData() if isinstance(combo, QComboBox) else None
                responses.append(value)
                if value is None:
                    total = None
                elif total is not None:
                    total += int(value)
            calificacion = self.table.item(row, 7).text().strip() if self.table.item(row, 7) else "-"
            rows.append({"estudiante_id": student.get("estudiante_id"), "estudiante": student.get("estudiante"), "respuestas": responses, "puntaje_total": total, "calificacion": calificacion})
        return {"asignacion_id": self._assignment_id, "trimestre_num": self._trimester_num, "curso_clave": self._course_key, "filas": rows}

    def _save_rows(self) -> None:
        payload = self.build_save_payload()
        if not payload["asignacion_id"] or not payload["trimestre_num"]:
            QMessageBox.warning(self, "Validación", "Seleccione una asignación y trimestre.")
            return
        if payload["curso_clave"] not in {"8", "9", "10"}:
            QMessageBox.warning(self, "Validación", "Orientación Vocacional y Profesional solo corresponde a 8vo, 9no y 10mo de EGB.")
            return
        if self._on_save_payload is None:
            QMessageBox.warning(self, "Error", "Servicio de guardado no disponible.")
            return
        ok, message = self._on_save_payload(payload)
        if ok:
            QMessageBox.information(self, "Éxito", message)
        else:
            QMessageBox.warning(self, "Validación", message)

    @staticmethod
    def detect_course_key(course_name: str) -> str | None:
        normalized = OrientacionVocacionalView._normalize_text(course_name)
        tokens = set(normalized.split())
        if any(t in tokens for t in {"8", "8vo", "octavo"}):
            return "8"
        if any(t in tokens for t in {"9", "9no", "noveno"}):
            return "9"
        if any(t in tokens for t in {"10", "10mo", "decimo"}):
            return "10"
        return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFD", str(value or "").strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())
