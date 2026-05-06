from __future__ import annotations

from datetime import date
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QMessageBox, QDateEdit, QTextEdit
from PySide6.QtCore import QDate

from src.application.services.attendance_service import AttendanceService


class AttendanceView(QWidget):
    def __init__(self, attendance_service: AttendanceService) -> None:
        super().__init__()
        self.service = attendance_service
        self.assignments = []
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
        self.month_combo = QComboBox(); [self.month_combo.addItem(m, i+1) for i,m in enumerate(["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"])]; self.month_combo.setCurrentIndex(date.today().month-1); self.month_combo.currentIndexChanged.connect(self._reload_sheet)
        self.year_combo = QComboBox(); [self.year_combo.addItem(str(y), y) for y in range(date.today().year-1, date.today().year+2)]; self.year_combo.setCurrentText(str(date.today().year)); self.year_combo.currentIndexChanged.connect(self._reload_sheet)
        self.search = QLineEdit(); self.search.setPlaceholderText("Buscar estudiante"); self.search.textChanged.connect(self._filter_rows)
        self.btn_p = QPushButton("Marcar todo visible P"); self.btn_p.clicked.connect(lambda: self._bulk_set("P"))
        self.btn_a = QPushButton("Marcar todo visible A"); self.btn_a.clicked.connect(lambda: self._bulk_set("A"))
        self.btn_f = QPushButton("Marcar todo visible F"); self.btn_f.clicked.connect(lambda: self._bulk_set("F"))
        self.btn_c = QPushButton("Limpiar sábana"); self.btn_c.clicked.connect(lambda: self._bulk_set(""))
        self.btn_save = QPushButton("Guardar asistencia"); self.btn_save.clicked.connect(self._save)
        for wid in (QLabel("Asignación"), self.assignment_combo, QLabel("Mes"), self.month_combo, QLabel("Año"), self.year_combo, self.search, self.btn_p, self.btn_a, self.btn_f, self.btn_c, self.btn_save): top.addWidget(wid)
        l.addLayout(top)
        self.stats = QLabel("Estudiantes: 0 | P:0 | A:0 | F:0 | J:0")
        l.addWidget(self.stats)
        self.table = QTableWidget(0, 22)
        self.table.setHorizontalHeaderLabels(["N°", "Nómina"] + [f"D{i+1}" for i in range(20)])
        self.table.itemChanged.connect(lambda *_: self._update_stats())
        l.addWidget(self.table)
        return w

    def _build_just_tab(self) -> QWidget:
        w = QWidget(); l = QVBoxLayout(w); row = QHBoxLayout()
        self.just_assignment = QComboBox(); self.just_student = QComboBox(); self.just_date = QDateEdit(); self.just_date.setCalendarPopup(True); self.just_date.setDate(QDate.currentDate())
        self.just_reason = QComboBox(); [self.just_reason.addItem(x) for x in ["Certificado médico","Calamidad doméstica","Representante justifica","Actividad institucional","Otro"]]
        self.just_obs = QTextEdit(); self.just_obs.setMaximumHeight(60)
        btn = QPushButton("Guardar justificación"); btn.clicked.connect(self._save_justification)
        for wdg in (QLabel("Asignación"), self.just_assignment, QLabel("Estudiante"), self.just_student, QLabel("Fecha"), self.just_date, QLabel("Motivo"), self.just_reason, btn): row.addWidget(wdg)
        l.addLayout(row); l.addWidget(self.just_obs); return w

    def refresh_data(self) -> None:
        self.assignments = self.service.list_assignments()
        for combo in (self.assignment_combo, self.just_assignment):
            combo.blockSignals(True); combo.clear()
            for a in self.assignments:
                label = f"{a['asignatura']} | {a['curso']}-{a['paralelo']} | {a['periodo_id']}"
                combo.addItem(label, a['id_asignacion'])
            combo.blockSignals(False)
        self._reload_sheet(); self._load_students_for_just()
        self.just_assignment.currentIndexChanged.connect(self._load_students_for_just)

    def _load_students_for_just(self) -> None:
        aid = self.just_assignment.currentData(); self.just_student.clear()
        if not aid: return
        for s in self.service.list_students_for_assignment(aid): self.just_student.addItem(s['estudiante'], s['id_estudiante'])

    def _reload_sheet(self) -> None:
        aid = self.assignment_combo.currentData()
        if not aid: return
        month, year = int(self.month_combo.currentData()), int(self.year_combo.currentData())
        students = self.service.list_students_for_assignment(aid)
        values = self.service.load_month_sheet(aid, year, month)
        days = self.service.weekdays_for_month(year, month)
        self._days = days
        self.table.blockSignals(True); self.table.setRowCount(len(students))
        for i,s in enumerate(students):
            self.table.setItem(i,0,QTableWidgetItem(str(s.get('numero_lista') or i+1))); self.table.setItem(i,1,QTableWidgetItem(s['estudiante']))
            for d_idx,d in enumerate(days):
                key=(s['id_estudiante'], d.isoformat()); self.table.setItem(i,2+d_idx,QTableWidgetItem(values.get(key, "")))
            self.table.setVerticalHeaderItem(i,QTableWidgetItem(s['id_estudiante']))
        self.table.blockSignals(False); self._update_stats()

    def _bulk_set(self, value: str) -> None:
        for r in range(self.table.rowCount()):
            if self.table.isRowHidden(r):
                continue
            for c in range(2, 2+len(getattr(self, '_days', []))):
                self.table.item(r,c).setText(value)
        self._update_stats()

    def _filter_rows(self, text: str) -> None:
        text = text.lower().strip()
        for r in range(self.table.rowCount()):
            name = (self.table.item(r,1).text() if self.table.item(r,1) else '').lower()
            self.table.setRowHidden(r, text not in name)

    def _update_stats(self) -> None:
        p=a=f=j=0
        for r in range(self.table.rowCount()):
            if self.table.isRowHidden(r): continue
            for c in range(2, 2+len(getattr(self, '_days', []))):
                t=(self.table.item(r,c).text() if self.table.item(r,c) else '').strip().upper()
                p += t=='P'; a += t=='A'; f += t=='F'; j += t=='J'
        self.stats.setText(f"Estudiantes: {self.table.rowCount()} | P:{p} | A:{a} | F:{f} | J:{j}")

    def _save(self) -> None:
        aid = self.assignment_combo.currentData(); records=[]
        for r in range(self.table.rowCount()):
            sid = self.table.verticalHeaderItem(r).text()
            for d_idx,d in enumerate(getattr(self,'_days',[])):
                v=(self.table.item(r,2+d_idx).text() if self.table.item(r,2+d_idx) else '').strip().upper()
                if v not in {'','P','A','F','J'}: continue
                records.append({'student_id':sid,'date':d.isoformat(),'status':v})
        self.service.save_attendance(aid, records)
        QMessageBox.information(self, "Asistencias", "Asistencia guardada")

    def _save_justification(self) -> None:
        aid=self.just_assignment.currentData(); sid=self.just_student.currentData()
        self.service.save_justification(aid,sid,self.just_date.date().toString('yyyy-MM-dd'),self.just_reason.currentText(),self.just_obs.toPlainText().strip())
        QMessageBox.information(self,"Justificaciones","Justificación guardada")
