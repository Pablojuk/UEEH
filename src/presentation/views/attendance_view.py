from __future__ import annotations

from datetime import date
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
)

from src.application.services.attendance_service import AttendanceService


class AttendanceView(QWidget):
    STATUS = ["P", "A", "F", "J"]

    def __init__(self, attendance_service: AttendanceService) -> None:
        super().__init__()
        self.service = attendance_service
        self.assignments: list[dict] = []
        self._days = []
        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)
        self.tabs.addTab(self._build_month_sheet_tab(), "Sábana mensual")
        self.tabs.addTab(self._build_just_tab(), "Justificaciones")
        self.tabs.addTab(self._placeholder("Informe trimestral (en desarrollo)"), "Informe trimestral")
        self.tabs.addTab(self._placeholder("Informe anual (en desarrollo)"), "Informe anual")
        self.tabs.addTab(self._placeholder("Configuración (en desarrollo)"), "Configuración")
        self.refresh_data()

    def _placeholder(self, text: str) -> QWidget:
        w = QWidget(); l = QVBoxLayout(w); l.addWidget(QLabel(text)); l.addStretch(1); return w

    def _build_month_sheet_tab(self) -> QWidget:
        w = QWidget(); l = QVBoxLayout(w)
        top = QHBoxLayout()
        self.assignment_combo = QComboBox(); self.assignment_combo.currentIndexChanged.connect(self._reload_sheet)
        self.month_combo = QComboBox(); [self.month_combo.addItem(m, i + 1) for i, m in enumerate(["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"])]; self.month_combo.setCurrentIndex(date.today().month - 1); self.month_combo.currentIndexChanged.connect(self._reload_sheet)
        self.year_combo = QComboBox(); [self.year_combo.addItem(str(y), y) for y in range(2026, 2036)]; self.year_combo.setCurrentText(str(max(2026, min(2035, date.today().year)))); self.year_combo.currentIndexChanged.connect(self._reload_sheet)
        self.search = QLineEdit(); self.search.setPlaceholderText("Buscar estudiante"); self.search.textChanged.connect(self._filter_rows)
        self.btn_just = QPushButton("Justificaciones"); self.btn_just.clicked.connect(self._open_just_modal)
        self.btn_c = QPushButton("Limpiar sábana"); self.btn_c.clicked.connect(self._reset_visible_to_p)
        self.btn_save = QPushButton("Guardar asistencia"); self.btn_save.clicked.connect(self._save)
        for wid in (QLabel("Asignación"), self.assignment_combo, QLabel("Mes"), self.month_combo, QLabel("Año"), self.year_combo, self.search, self.btn_just, self.btn_c, self.btn_save): top.addWidget(wid)
        l.addLayout(top)
        self.stats = QLabel("Estudiantes: 0 | Presentes: 0 | Atrasos: 0 | Faltas: 0 | Justificadas: 0")
        l.addWidget(self.stats)
        self.table = QTableWidget(0, 6)
        l.addWidget(self.table)
        return w

    def _build_just_tab(self) -> QWidget:
        w = QWidget(); l = QVBoxLayout(w); row = QHBoxLayout()
        self.just_assignment = QComboBox(); self.just_student = QComboBox(); self.just_date = QDateEdit(); self.just_date.setCalendarPopup(True); self.just_date.setDate(QDate.currentDate())
        self.just_reason = QComboBox(); [self.just_reason.addItem(x) for x in ["Certificado médico", "Calamidad doméstica", "Representante justifica", "Actividad institucional", "Otro"]]
        self.just_obs = QTextEdit(); self.just_obs.setMaximumHeight(60)
        btn = QPushButton("Guardar justificación"); btn.clicked.connect(self._save_justification)
        for wdg in (QLabel("Asignación"), self.just_assignment, QLabel("Estudiante"), self.just_student, QLabel("Fecha"), self.just_date, QLabel("Motivo"), self.just_reason, btn): row.addWidget(wdg)
        l.addLayout(row); l.addWidget(self.just_obs); return w

    def refresh_data(self) -> None:
        self.assignments = self.service.list_assignments()
        for combo in (self.assignment_combo, self.just_assignment):
            combo.blockSignals(True); combo.clear()
            for a in self.assignments:
                combo.addItem(f"{a['asignatura']} | {a['curso']}-{a['paralelo']} | {a['periodo_id']}", a['id_asignacion'])
            combo.blockSignals(False)
        self.just_assignment.currentIndexChanged.connect(self._load_students_for_just)
        self._load_students_for_just()
        self._reload_sheet()

    def _load_students_for_just(self) -> None:
        aid = self.just_assignment.currentData(); self.just_student.clear()
        if not aid: return
        for s in self.service.list_students_for_assignment(aid): self.just_student.addItem(s['estudiante'], s['id_estudiante'])

    def _build_status_combo(self, value: str = "P") -> QComboBox:
        c = QComboBox(); c.addItems(self.STATUS); c.setCurrentText(value if value in self.STATUS else "P"); c.currentIndexChanged.connect(self._update_stats); return c

    def _reload_sheet(self) -> None:
        aid = self.assignment_combo.currentData()
        if not aid: return
        month, year = int(self.month_combo.currentData()), int(self.year_combo.currentData())
        students = self.service.list_students_for_assignment(aid)
        values = self.service.load_month_sheet(aid, year, month)
        self._days = self.service.weekdays_for_month(year, month)

        headers = ["N°", "Nómina"] + [f"{d.day:02d} {['Lunes','Martes','Miércoles','Jueves','Viernes'][d.weekday()]}" for d in self._days] + ["P", "A", "F", "J"]
        self.table.clear(); self.table.setColumnCount(len(headers)); self.table.setHorizontalHeaderLabels(headers); self.table.setRowCount(len(students))
        self.table.setColumnWidth(1, 260)

        for i, s in enumerate(students):
            n = QTableWidgetItem(str(s.get('numero_lista') or i + 1)); name = QTableWidgetItem(s['estudiante']); name.setData(256, s['id_estudiante'])
            self.table.setItem(i, 0, n); self.table.setItem(i, 1, name)
            for d_idx, d in enumerate(self._days):
                key = (s['id_estudiante'], d.isoformat()); val = values.get(key, "P") or "P"
                self.table.setCellWidget(i, 2 + d_idx, self._build_status_combo(val))
            for off in range(4): self.table.setItem(i, 2 + len(self._days) + off, QTableWidgetItem("0"))
        self._update_stats()

    def _filter_rows(self, text: str) -> None:
        text = text.lower().strip()
        for r in range(self.table.rowCount()):
            name = (self.table.item(r, 1).text() if self.table.item(r, 1) else "").lower()
            self.table.setRowHidden(r, text not in name)
        self._update_stats()

    def _row_counts(self, r: int) -> dict[str, int]:
        cnt = {k: 0 for k in self.STATUS}
        for c in range(2, 2 + len(self._days)):
            w = self.table.cellWidget(r, c)
            v = w.currentText() if isinstance(w, QComboBox) else "P"
            if v in cnt: cnt[v] += 1
        return cnt

    def _update_stats(self) -> None:
        total = {k: 0 for k in self.STATUS}
        for r in range(self.table.rowCount()):
            cnt = self._row_counts(r)
            for idx, k in enumerate(self.STATUS): self.table.item(r, 2 + len(self._days) + idx).setText(str(cnt[k]))
            if self.table.isRowHidden(r):
                continue
            for k in self.STATUS: total[k] += cnt[k]
        self.stats.setText(f"Estudiantes: {self.table.rowCount()} | Presentes: {total['P']} | Atrasos: {total['A']} | Faltas: {total['F']} | Justificadas: {total['J']}")

    def _reset_visible_to_p(self) -> None:
        for r in range(self.table.rowCount()):
            if self.table.isRowHidden(r):
                continue
            for c in range(2, 2 + len(self._days)):
                w = self.table.cellWidget(r, c)
                if isinstance(w, QComboBox): w.setCurrentText("P")
        self._update_stats()

    def _save(self) -> None:
        aid = self.assignment_combo.currentData(); records = []
        for r in range(self.table.rowCount()):
            sid = self.table.item(r, 1).data(256)
            for d_idx, d in enumerate(self._days):
                w = self.table.cellWidget(r, 2 + d_idx); v = w.currentText() if isinstance(w, QComboBox) else "P"
                records.append({"student_id": sid, "date": d.isoformat(), "status": v})
        self.service.save_attendance(aid, records)
        QMessageBox.information(self, "Asistencias", "Asistencia guardada")

    def _open_just_modal(self) -> None:
        aid = self.assignment_combo.currentData()
        if not aid:
            return
        dlg = QDialog(self); dlg.setWindowTitle("Registrar justificación de asistencia"); dlg.resize(500, 360)
        form = QFormLayout(dlg)
        student = QComboBox();
        for s in self.service.list_students_for_assignment(aid): student.addItem(s['estudiante'], s['id_estudiante'])
        fdate = QDateEdit(); fdate.setCalendarPopup(True); fdate.setDate(QDate.currentDate())
        reason = QComboBox(); [reason.addItem(x) for x in ["Certificado médico", "Calamidad doméstica", "Representante justifica", "Actividad institucional", "Otro"]]
        obs = QTextEdit();
        actions = QHBoxLayout(); bsave = QPushButton("Guardar justificación"); bcancel = QPushButton("Cancelar"); actions.addWidget(bsave); actions.addWidget(bcancel)
        form.addRow("Estudiante", student); form.addRow("Fecha", fdate); form.addRow("Motivo", reason); form.addRow("Observación", obs); form.addRow(actions)
        bcancel.clicked.connect(dlg.reject)

        def on_save() -> None:
            self.service.save_justification(aid, student.currentData(), fdate.date().toString('yyyy-MM-dd'), reason.currentText(), obs.toPlainText().strip())
            self._reload_sheet()
            target = fdate.date().toString('yyyy-MM-dd')
            for i, d in enumerate(self._days):
                if d.isoformat() == target:
                    for r in range(self.table.rowCount()):
                        if self.table.item(r, 1).data(256) == student.currentData():
                            w = self.table.cellWidget(r, 2 + i)
                            if isinstance(w, QComboBox): w.setCurrentText('J')
                    break
            self._update_stats(); dlg.accept()

        bsave.clicked.connect(on_save)
        dlg.exec()

    def _save_justification(self) -> None:
        aid = self.just_assignment.currentData(); sid = self.just_student.currentData()
        self.service.save_justification(aid, sid, self.just_date.date().toString('yyyy-MM-dd'), self.just_reason.currentText(), self.just_obs.toPlainText().strip())
        QMessageBox.information(self, "Justificaciones", "Justificación guardada")
