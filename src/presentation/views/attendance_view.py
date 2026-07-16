from __future__ import annotations
from datetime import date
import re
import unicodedata
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
from src.presentation.styles import ATTENDANCE_TABS_STYLE

class AttendanceView(QWidget):
    STATUS=["P","A","F","J"]
    def __init__(self, attendance_service: AttendanceService)->None:
        super().__init__(); self.service=attendance_service
        self.renderer=AttendanceReportRenderer(); self.excel_exporter=AttendanceExcelExporter(); self.pdf_exporter=PdfReportExporter()
        self.assignments=[]; self._days=[]; self._quarterly_data=None; self._annual_data=None
        self._attendance_firmantes={"docente":"","tutor":"","rector":""}
        root=QVBoxLayout(self); self.tabs=QTabWidget(); self.tabs.setObjectName("AttendanceTabs"); self.tabs.setStyleSheet(ATTENDANCE_TABS_STYLE); root.addWidget(self.tabs)
        self.tabs.addTab(self._build_month_sheet_tab(),"Sábana mensual")
        self.tabs.addTab(self._build_quarterly_report_tab(),"Informe trimestral")
        self.tabs.addTab(self._build_annual_report_tab(),"Informe anual")
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
        self.signer_docente_combo=QComboBox(); self.signer_tutor_combo=QComboBox(); self.signer_rector_combo=QComboBox()
        self.signer_docente_combo.currentIndexChanged.connect(self._update_signers)
        self.signer_tutor_combo.currentIndexChanged.connect(self._update_signers)
        self.signer_rector_combo.currentIndexChanged.connect(self._update_signers)
        sign_l.addWidget(QLabel("Docente")); sign_l.addWidget(self.signer_docente_combo,1)
        sign_l.addWidget(QLabel("Tutor")); sign_l.addWidget(self.signer_tutor_combo,1)
        sign_l.addWidget(QLabel("Rector")); sign_l.addWidget(self.signer_rector_combo,1); l.addWidget(sign)
        if QWebEngineView is not None:
            self.attendance_preview_view=QWebEngineView(); self._attendance_preview_uses_webengine=True
        else:
            self.attendance_preview_view=QTextBrowser(); self.attendance_preview_view.setOpenExternalLinks(True); self._attendance_preview_uses_webengine=False
        l.addWidget(self.attendance_preview_view,1)
        return w

    def _build_annual_report_tab(self)->QWidget:
        w=QWidget(); l=QVBoxLayout(w)
        top=QHBoxLayout(); self.a_assignment=QComboBox(); self.a_assignment.currentIndexChanged.connect(self._on_annual_assignment_changed)
        self.a_t1_start=QDateEdit(); self.a_t1_start.setCalendarPopup(True); self.a_t1_start.setDate(QDate.currentDate().addMonths(-9))
        self.a_t1_end=QDateEdit(); self.a_t1_end.setCalendarPopup(True); self.a_t1_end.setDate(QDate.currentDate().addMonths(-6))
        self.a_t2_start=QDateEdit(); self.a_t2_start.setCalendarPopup(True); self.a_t2_start.setDate(QDate.currentDate().addMonths(-6))
        self.a_t2_end=QDateEdit(); self.a_t2_end.setCalendarPopup(True); self.a_t2_end.setDate(QDate.currentDate().addMonths(-3))
        self.a_t3_start=QDateEdit(); self.a_t3_start.setCalendarPopup(True); self.a_t3_start.setDate(QDate.currentDate().addMonths(-3))
        self.a_t3_end=QDateEdit(); self.a_t3_end.setCalendarPopup(True); self.a_t3_end.setDate(QDate.currentDate())
        self.a_btn_preview=QPushButton("Generar vista previa"); self.a_btn_preview.clicked.connect(self._generate_annual_preview)
        self.a_btn_pdf=QPushButton("Exportar PDF"); self.a_btn_pdf.clicked.connect(self._export_annual_pdf)
        self.a_btn_xlsx=QPushButton("Exportar Excel"); self.a_btn_xlsx.clicked.connect(self._export_annual_excel)
        for wid in (QLabel("Asignación"),self.a_assignment,QLabel("Inicio T1"),self.a_t1_start,QLabel("Fin T1"),self.a_t1_end,QLabel("Inicio T2"),self.a_t2_start,QLabel("Fin T2"),self.a_t2_end,QLabel("Inicio T3"),self.a_t3_start,QLabel("Fin T3"),self.a_t3_end,self.a_btn_preview,self.a_btn_pdf,self.a_btn_xlsx): top.addWidget(wid)
        l.addLayout(top)
        sign=QGroupBox("Firmantes del reporte"); sl=QHBoxLayout(sign); self.a_signer_docente=QComboBox(); self.a_signer_tutor=QComboBox(); self.a_signer_rector=QComboBox(); self.a_signer_docente.currentIndexChanged.connect(self._update_annual_signers); self.a_signer_tutor.currentIndexChanged.connect(self._update_annual_signers); self.a_signer_rector.currentIndexChanged.connect(self._update_annual_signers); sl.addWidget(QLabel("Docente")); sl.addWidget(self.a_signer_docente,1); sl.addWidget(QLabel("Tutor")); sl.addWidget(self.a_signer_tutor,1); sl.addWidget(QLabel("Rector")); sl.addWidget(self.a_signer_rector,1); l.addWidget(sign)
        if QWebEngineView is not None: self.annual_preview_view=QWebEngineView()
        else: self.annual_preview_view=QTextBrowser()
        l.addWidget(self.annual_preview_view,1)
        self._annual_firmantes={"docente":"","tutor":"","rector":""}
        return w

    def _set_attendance_preview_html(self, html_content: str) -> None:
        self.attendance_preview_view.setHtml(html_content)
    def refresh_data(self)->None:
        self.assignments=self.service.list_assignments()
        for combo in (self.assignment_combo,self.q_assignment,self.a_assignment):
            combo.blockSignals(True); combo.clear()
            for a in self.assignments: combo.addItem(f"{a['asignatura']} | {a['curso']}-{a['paralelo']} | {a['periodo_id']}",a['id_asignacion'])
            combo.blockSignals(False)
        self._reload_sheet(); self._on_quarterly_assignment_changed(); self._on_annual_assignment_changed()
    def _on_quarterly_assignment_changed(self)->None:
        aid=self.q_assignment.currentData()
        self._load_attendance_signer_options()
        ctx=self.service.get_assignment_context(aid) if aid else {}
        docente=ctx.get('docente','')
        rector=ctx.get('rector','')
        if docente:
            idx=self.signer_docente_combo.findData(docente)
            if idx>=0: self.signer_docente_combo.setCurrentIndex(idx)
        if rector:
            idx=self.signer_rector_combo.findData(rector)
            if idx>=0: self.signer_rector_combo.setCurrentIndex(idx)
        self._update_signers()

    def _load_attendance_signer_options(self)->None:
        options=self.service.listar_firmantes_disponibles()
        for combo in (self.signer_docente_combo,self.signer_tutor_combo,self.signer_rector_combo):
            combo.blockSignals(True); combo.clear(); combo.addItem('Seleccione','')
            for row in options: combo.addItem(row.get('firma',''),row.get('firma',''))
            combo.blockSignals(False)
    def _update_signers(self)->None:
        self._attendance_firmantes['docente']=self.signer_docente_combo.currentData() or self.signer_docente_combo.currentText().strip()
        self._attendance_firmantes['tutor']=self.signer_tutor_combo.currentData() or self.signer_tutor_combo.currentText().strip()
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
        ctx=data['context']; ctx['trimestre']=self.q_trimester.currentText(); ctx['periodo']=f"{self.q_from.date().toString('dd/MM/yyyy')} al {self.q_to.date().toString('dd/MM/yyyy')}"; self._update_signers(); ctx['firma_docente']=self._attendance_firmantes['docente'] or ctx.get('docente',''); ctx['tutor']=self._attendance_firmantes['tutor'] or ctx.get('tutor',''); ctx['firma_tutor']=self._attendance_firmantes['tutor'] or ctx.get('tutor',''); ctx['firma_rector']=self._attendance_firmantes['rector'] or ctx.get('rector','')
        html=self.renderer.render_attendance_quarterly(ctx,data['rows'],data['stats']); self._set_attendance_preview_html(html)
        self._quarterly_data=(ctx,data['rows'],data['stats'],html)

    @staticmethod
    def _sanitize_filename(text: str) -> str:
        value = str(text or '').strip()
        value = unicodedata.normalize('NFD', value)
        value = ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn')
        value = re.sub(r'[|/\\:*?"<>]', '_', value)
        value = value.replace(' ', '_')
        value = re.sub(r'_+', '_', value).strip(' ._')
        return value or 'reporte'

    def _export_quarterly_pdf(self)->None:
        if not self._quarterly_data: self._generate_quarterly_preview()
        if not self._quarterly_data: return
        assignment_text=self.q_assignment.currentText() or str(self.q_assignment.currentData() or '')
        default_name=f"{self._sanitize_filename(assignment_text)}_asistencia.pdf"
        path,_=QFileDialog.getSaveFileName(self,'Exportar PDF',default_name,'PDF (*.pdf)')
        if not path: return
        ok=self.pdf_exporter.export_to_pdf(self._quarterly_data[3],path,orientation='landscape',margins_mm=8)
        QMessageBox.information(self,'PDF','Exportado correctamente' if ok else 'No se pudo exportar PDF')
    def _export_quarterly_excel(self)->None:
        if not self._quarterly_data: self._generate_quarterly_preview()
        if not self._quarterly_data: return
        assignment_text=self.q_assignment.currentText() or str(self.q_assignment.currentData() or '')
        default_name=f"{self._sanitize_filename(assignment_text)}_asistencia.xlsx"
        path,_=QFileDialog.getSaveFileName(self,'Exportar Excel',default_name,'Excel (*.xlsx)')
        if not path: return
        self.excel_exporter.export_attendance_quarterly_excel(path,self._quarterly_data[0],self._quarterly_data[1],self._quarterly_data[2])
        QMessageBox.information(self,'Excel','Exportado correctamente')

    def _on_annual_assignment_changed(self)->None:
        self._load_attendance_signer_options()
        self.a_signer_docente.clear(); self.a_signer_rector.clear()
        for i in range(self.signer_docente_combo.count()): self.a_signer_docente.addItem(self.signer_docente_combo.itemText(i),self.signer_docente_combo.itemData(i))
        for i in range(self.signer_tutor_combo.count()): self.a_signer_tutor.addItem(self.signer_tutor_combo.itemText(i),self.signer_tutor_combo.itemData(i))
        for i in range(self.signer_rector_combo.count()): self.a_signer_rector.addItem(self.signer_rector_combo.itemText(i),self.signer_rector_combo.itemData(i))

    def _update_annual_signers(self)->None:
        self._annual_firmantes['docente']=self.a_signer_docente.currentData() or self.a_signer_docente.currentText().strip()
        self._annual_firmantes['tutor']=self.a_signer_tutor.currentData() or self.a_signer_tutor.currentText().strip()
        self._annual_firmantes['rector']=self.a_signer_rector.currentData() or self.a_signer_rector.currentText().strip()

    def _validate_annual_dates(self)->bool:
        if self.a_t1_start.date()>self.a_t1_end.date() or self.a_t2_start.date()>self.a_t2_end.date() or self.a_t3_start.date()>self.a_t3_end.date():
            QMessageBox.warning(self,'Informe anual','Rangos trimestrales inválidos'); return False
        if not (self.a_t1_end.date()<self.a_t2_start.date()<self.a_t3_start.date()) or not (self.a_t2_end.date()<self.a_t3_start.date()):
            QMessageBox.warning(self,'Informe anual','Secuencia de trimestres inválida'); return False
        return True

    def _generate_annual_preview(self)->None:
        aid=self.a_assignment.currentData()
        if not aid: return QMessageBox.warning(self,'Informe anual','Seleccione una asignación')
        if not self._validate_annual_dates(): return
        self._update_annual_signers()
        data=self.service.build_annual_attendance_report(aid,self.a_t1_start.date().toString('yyyy-MM-dd'),self.a_t1_end.date().toString('yyyy-MM-dd'),self.a_t2_start.date().toString('yyyy-MM-dd'),self.a_t2_end.date().toString('yyyy-MM-dd'),self.a_t3_start.date().toString('yyyy-MM-dd'),self.a_t3_end.date().toString('yyyy-MM-dd'),self._annual_firmantes)
        ctx=data['context']; ctx['periodo_anual']=f"{self.a_t1_start.date().toString('dd/MM/yyyy')} al {self.a_t3_end.date().toString('dd/MM/yyyy')}"; ctx['periodo_t1']=f"{self.a_t1_start.date().toString('dd/MM/yyyy')} al {self.a_t1_end.date().toString('dd/MM/yyyy')}"; ctx['periodo_t2']=f"{self.a_t2_start.date().toString('dd/MM/yyyy')} al {self.a_t2_end.date().toString('dd/MM/yyyy')}"; ctx['periodo_t3']=f"{self.a_t3_start.date().toString('dd/MM/yyyy')} al {self.a_t3_end.date().toString('dd/MM/yyyy')}"; ctx['firma_docente']=self._annual_firmantes['docente'] or ctx.get('docente',''); ctx['tutor']=self._annual_firmantes['tutor'] or ctx.get('tutor',''); ctx['firma_tutor']=self._annual_firmantes['tutor'] or ctx.get('tutor',''); ctx['firma_rector']=self._annual_firmantes['rector'] or ctx.get('rector','')
        html=self.renderer.render_attendance_annual(ctx,data['rows'],data['stats']); self.annual_preview_view.setHtml(html); self._annual_data=(ctx,data['rows'],data['stats'],html)

    def _export_annual_pdf(self)->None:
        if not self._annual_data: self._generate_annual_preview()
        if not self._annual_data: return
        assignment_text=self.a_assignment.currentText() or str(self.a_assignment.currentData() or '')
        path,_=QFileDialog.getSaveFileName(self,'Exportar PDF',f"{self._sanitize_filename(assignment_text)}_asistencia_anual.pdf",'PDF (*.pdf)')
        if not path: return
        ok=self.pdf_exporter.export_to_pdf(self._annual_data[3],path,orientation='landscape',margins_mm=6)
        QMessageBox.information(self,'PDF','Exportado correctamente' if ok else 'No se pudo exportar PDF')

    def _export_annual_excel(self)->None:
        if not self._annual_data: self._generate_annual_preview()
        if not self._annual_data: return
        assignment_text=self.a_assignment.currentText() or str(self.a_assignment.currentData() or '')
        path,_=QFileDialog.getSaveFileName(self,'Exportar Excel',f"{self._sanitize_filename(assignment_text)}_asistencia_anual.xlsx",'Excel (*.xlsx)')
        if not path: return
        self.excel_exporter.export_attendance_annual_excel(path,self._annual_data[0],self._annual_data[1],self._annual_data[2]); QMessageBox.information(self,'Excel','Exportado correctamente')
