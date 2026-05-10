from __future__ import annotations
from datetime import date
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,QDateEdit,QFileDialog,QGroupBox,QHBoxLayout,QLabel,QLineEdit,QMessageBox,
    QPushButton,QTabWidget,QTableWidget,QTableWidgetItem,QTextBrowser,QVBoxLayout,QWidget
)
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None

from src.application.services.attendance_service import AttendanceService
from src.infrastructure.exporters.attendance_report_renderer import AttendanceReportRenderer
from src.infrastructure.exporters.attendance_excel_exporter import AttendanceExcelExporter
from src.infrastructure.exporters.pdf_report_exporter import PdfReportExporter

class AttendanceView(QWidget):
    STATUS=["P","A","F","J"]
    def __init__(self, attendance_service: AttendanceService)->None:
        super().__init__(); self.service=attendance_service
        self.renderer=AttendanceReportRenderer(); self.excel_exporter=AttendanceExcelExporter(); self.pdf_exporter=PdfReportExporter()
        self.assignments=[]; self._days=[]; self._quarterly_data=None
        self._attendance_firmantes={"docente":"","rector":""}
        root=QVBoxLayout(self); self.tabs=QTabWidget(); root.addWidget(self.tabs)
        self.tabs.addTab(self._build_month_sheet_tab(),"Sábana mensual")
        self.tabs.addTab(self._build_quarterly_report_tab(),"Informe trimestral")
        self.tabs.addTab(self._placeholder("Informe anual (en desarrollo)"),"Informe anual")
        self.refresh_data()
    def _placeholder(self,text:str)->QWidget:
        w=QWidget();l=QVBoxLayout(w);l.addWidget(QLabel(text));l.addStretch(1);return w
    def _build_month_sheet_tab(self)->QWidget:
        w=QWidget();l=QVBoxLayout(w);top=QHBoxLayout()
        self.assignment_combo=QComboBox(); self.assignment_combo.currentIndexChanged.connect(self._reload_sheet)
        self.month_combo=QComboBox(); [self.month_combo.addItem(m,i+1) for i,m in enumerate(["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"])]; self.month_combo.setCurrentIndex(date.today().month-1); self.month_combo.currentIndexChanged.connect(self._reload_sheet)
        self.year_combo=QComboBox(); [self.year_combo.addItem(str(y),y) for y in range(2026,2036)]; self.year_combo.setCurrentText(str(max(2026,min(2035,date.today().year)))); self.year_combo.currentIndexChanged.connect(self._reload_sheet)
        self.search=QLineEdit(); self.search.setPlaceholderText("Buscar estudiante"); self.search.textChanged.connect(self._filter_rows)
        self.btn_c=QPushButton("Limpiar sábana"); self.btn_c.clicked.connect(self._reset_visible_to_p)
        self.btn_save=QPushButton("Guardar asistencia"); self.btn_save.clicked.connect(self._save)
        for wid in (QLabel("Asignación"),self.assignment_combo,QLabel("Mes"),self.month_combo,QLabel("Año"),self.year_combo,self.search,self.btn_c,self.btn_save): top.addWidget(wid)
        l.addLayout(top); self.stats=QLabel("Estudiantes: 0 | Presentes: 0 | Atrasos: 0 | Faltas: 0 | Justificadas: 0"); l.addWidget(self.stats)
        self.table=QTableWidget(0,6); l.addWidget(self.table); return w
    def _build_quarterly_report_tab(self)->QWidget:
        w=QWidget(); l=QVBoxLayout(w)
        top=QHBoxLayout(); self.q_assignment=QComboBox(); self.q_assignment.currentIndexChanged.connect(self._on_quarterly_assignment_changed)
        self.q_trimester=QComboBox(); self.q_trimester.addItems(["Primer Trimestre","Segundo Trimestre","Tercer Trimestre"])
        self.q_from=QDateEdit(); self.q_from.setCalendarPopup(True); self.q_from.setDate(QDate.currentDate().addMonths(-3))
        self.q_to=QDateEdit(); self.q_to.setCalendarPopup(True); self.q_to.setDate(QDate.currentDate())
        self.q_btn_preview=QPushButton("Generar vista previa"); self.q_btn_preview.clicked.connect(self._generate_quarterly_preview)
        self.q_btn_pdf=QPushButton("Exportar PDF"); self.q_btn_pdf.clicked.connect(self._export_quarterly_pdf)
        self.q_btn_xlsx=QPushButton("Exportar Excel"); self.q_btn_xlsx.clicked.connect(self._export_quarterly_excel)
        for wid in (QLabel("Asignación"),self.q_assignment,QLabel("Trimestre"),self.q_trimester,QLabel("Fecha desde"),self.q_from,QLabel("Fecha hasta"),self.q_to,self.q_btn_preview,self.q_btn_pdf,self.q_btn_xlsx): top.addWidget(wid)
        l.addLayout(top)
        sign=QGroupBox("Firmantes del reporte"); sign_l=QHBoxLayout(sign)
        self.signer_docente_combo=QComboBox(); self.signer_rector_combo=QComboBox()
        self.signer_docente_combo.currentIndexChanged.connect(self._update_signers)
        self.signer_rector_combo.currentIndexChanged.connect(self._update_signers)
        sign_l.addWidget(QLabel("Docente")); sign_l.addWidget(self.signer_docente_combo,1)
        sign_l.addWidget(QLabel("Rector")); sign_l.addWidget(self.signer_rector_combo,1); l.addWidget(sign)
        if QWebEngineView is not None:
            self.attendance_preview_view=QWebEngineView(); self._attendance_preview_uses_webengine=True
        else:
            self.attendance_preview_view=QTextBrowser(); self.attendance_preview_view.setOpenExternalLinks(True); self._attendance_preview_uses_webengine=False
        l.addWidget(self.attendance_preview_view,1)
        return w
    def _set_attendance_preview_html(self, html_content: str) -> None:
        self.attendance_preview_view.setHtml(html_content)
    def refresh_data(self)->None:
        self.assignments=self.service.list_assignments()
        for combo in (self.assignment_combo,self.q_assignment):
            combo.blockSignals(True); combo.clear()
            for a in self.assignments: combo.addItem(f"{a['asignatura']} | {a['curso']}-{a['paralelo']} | {a['periodo_id']}",a['id_asignacion'])
            combo.blockSignals(False)
        self._reload_sheet(); self._on_quarterly_assignment_changed()
    def _on_quarterly_assignment_changed(self)->None:
        aid=self.q_assignment.currentData(); opts=self.service.list_quarterly_signer_options(aid)
        self.signer_docente_combo.blockSignals(True); self.signer_rector_combo.blockSignals(True)
        self.signer_docente_combo.clear(); self.signer_rector_combo.clear()
        for v in opts.get('docente',[]): self.signer_docente_combo.addItem(v,v)
        for v in opts.get('rector',[]): self.signer_rector_combo.addItem(v,v)
        self.signer_docente_combo.blockSignals(False); self.signer_rector_combo.blockSignals(False); self._update_signers()
    def _update_signers(self)->None:
        self._attendance_firmantes['docente']=self.signer_docente_combo.currentData() or self.signer_docente_combo.currentText().strip()
        self._attendance_firmantes['rector']=self.signer_rector_combo.currentData() or self.signer_rector_combo.currentText().strip()
    def _build_status_combo(self, value='P')->QComboBox:
        c=QComboBox(); c.addItems(self.STATUS); c.setCurrentText(value if value in self.STATUS else 'P'); c.currentIndexChanged.connect(self._update_stats); return c
    def _reload_sheet(self)->None:
        aid=self.assignment_combo.currentData();
        if not aid: return
        month,year=int(self.month_combo.currentData()),int(self.year_combo.currentData())
        students=self.service.list_students_for_assignment(aid); values=self.service.load_month_sheet(aid,year,month); self._days=self.service.weekdays_for_month(year,month)
        headers=["N°","Nómina"]+[f"{d.day:02d} {['Lunes','Martes','Miércoles','Jueves','Viernes'][d.weekday()]}" for d in self._days]+["P","A","F","J"]
        self.table.clear(); self.table.setColumnCount(len(headers)); self.table.setHorizontalHeaderLabels(headers); self.table.setRowCount(len(students)); self.table.setColumnWidth(1,260)
        for i,s in enumerate(students):
            self.table.setItem(i,0,QTableWidgetItem(str(s.get('numero_lista') or i+1))); nm=QTableWidgetItem(s['estudiante']); nm.setData(256,s['id_estudiante']); self.table.setItem(i,1,nm)
            for d_idx,d in enumerate(self._days): self.table.setCellWidget(i,2+d_idx,self._build_status_combo(values.get((s['id_estudiante'],d.isoformat()),'P') or 'P'))
            for off in range(4): self.table.setItem(i,2+len(self._days)+off,QTableWidgetItem('0'))
        self._update_stats()
    def _filter_rows(self,text:str)->None:
        text=text.lower().strip()
        for r in range(self.table.rowCount()): self.table.setRowHidden(r,text not in ((self.table.item(r,1).text() if self.table.item(r,1) else '').lower()))
        self._update_stats()
    def _row_counts(self,r:int)->dict[str,int]:
        cnt={k:0 for k in self.STATUS}
        for c in range(2,2+len(self._days)):
            w=self.table.cellWidget(r,c); v=w.currentText() if isinstance(w,QComboBox) else 'P'
            if v in cnt: cnt[v]+=1
        return cnt
    def _update_stats(self)->None:
        total={k:0 for k in self.STATUS}
        for r in range(self.table.rowCount()):
            cnt=self._row_counts(r)
            for idx,k in enumerate(self.STATUS): self.table.item(r,2+len(self._days)+idx).setText(str(cnt[k]))
            if not self.table.isRowHidden(r):
                for k in self.STATUS: total[k]+=cnt[k]
        self.stats.setText(f"Estudiantes: {self.table.rowCount()} | Presentes: {total['P']} | Atrasos: {total['A']} | Faltas: {total['F']} | Justificadas: {total['J']}")
    def _reset_visible_to_p(self)->None:
        for r in range(self.table.rowCount()):
            if self.table.isRowHidden(r): continue
            for c in range(2,2+len(self._days)):
                w=self.table.cellWidget(r,c)
                if isinstance(w,QComboBox): w.setCurrentText('P')
        self._update_stats()
    def _save(self)->None:
        aid=self.assignment_combo.currentData(); records=[]
        for r in range(self.table.rowCount()):
            sid=self.table.item(r,1).data(256)
            for d_idx,d in enumerate(self._days):
                w=self.table.cellWidget(r,2+d_idx); v=w.currentText() if isinstance(w,QComboBox) else 'P'
                records.append({'student_id':sid,'date':d.isoformat(),'status':v})
        self.service.save_attendance(aid,records); QMessageBox.information(self,'Asistencias','Asistencia guardada')
    def _generate_quarterly_preview(self)->None:
        aid=self.q_assignment.currentData()
        if not aid: return QMessageBox.warning(self,'Informe trimestral','Seleccione una asignación')
        if self.q_from.date()>self.q_to.date(): return QMessageBox.warning(self,'Informe trimestral','Fecha desde no puede ser mayor que fecha hasta')
        data=self.service.build_quarterly_attendance_report(aid,self.q_from.date().toString('yyyy-MM-dd'),self.q_to.date().toString('yyyy-MM-dd'))
        ctx=data['context']; ctx['trimestre']=self.q_trimester.currentText(); ctx['periodo']=f"{self.q_from.date().toString('dd/MM/yyyy')} al {self.q_to.date().toString('dd/MM/yyyy')}"; self._update_signers(); ctx['firma_docente']=self._attendance_firmantes['docente'] or ctx.get('docente',''); ctx['firma_rector']=self._attendance_firmantes['rector'] or ctx.get('rector','')
        html=self.renderer.render_attendance_quarterly(ctx,data['rows'],data['stats']); self._set_attendance_preview_html(html)
        self._quarterly_data=(ctx,data['rows'],data['stats'],html)
    def _export_quarterly_pdf(self)->None:
        if not self._quarterly_data: self._generate_quarterly_preview()
        if not self._quarterly_data: return
        path,_=QFileDialog.getSaveFileName(self,'Exportar PDF','informe_asistencia_trimestral.pdf','PDF (*.pdf)')
        if not path: return
        ok=self.pdf_exporter.export_to_pdf(self._quarterly_data[3],path,orientation='landscape')
        QMessageBox.information(self,'PDF','Exportado correctamente' if ok else 'No se pudo exportar PDF')
    def _export_quarterly_excel(self)->None:
        if not self._quarterly_data: self._generate_quarterly_preview()
        if not self._quarterly_data: return
        path,_=QFileDialog.getSaveFileName(self,'Exportar Excel','informe_asistencia_trimestral.xlsx','Excel (*.xlsx)')
        if not path: return
        self.excel_exporter.export_attendance_quarterly_excel(path,self._quarterly_data[0],self._quarterly_data[1],self._quarterly_data[2])
        QMessageBox.information(self,'Excel','Exportado correctamente')
