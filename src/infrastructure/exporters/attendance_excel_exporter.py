from __future__ import annotations
from pathlib import Path
from typing import Any
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

class AttendanceExcelExporter:
    def export_attendance_quarterly_excel(self, output_path:str, context:dict[str,Any], rows:list[dict[str,Any]], stats:dict[str,Any])->str:
        path=Path(output_path).expanduser().resolve(); path.parent.mkdir(parents=True,exist_ok=True)
        wb=Workbook(); ws=wb.active; ws.title='Asistencia trimestral'
        ws.page_setup.orientation=ws.ORIENTATION_LANDSCAPE
        headers=['N°','Nómina','Días laborables','Presentes','Atrasos','Faltas injustificadas','Faltas justificadas','% Asistencia','Observación']
        fill=PatternFill('solid',fgColor='1F4E79'); fnt=Font(color='FFFFFF',bold=True); bd=Border(left=Side(style='thin'),right=Side(style='thin'),top=Side(style='thin'),bottom=Side(style='thin'))
        ws.append(headers)
        for c in ws[1]: c.fill=fill; c.font=fnt; c.alignment=Alignment(horizontal='center'); c.border=bd
        for r in rows: ws.append([r['nro'],r['nomina'],r['dias_laborables'],r['presentes'],r['atrasos'],r['faltas_injustificadas'],r['faltas_justificadas'],float(r['porcentaje_asistencia'])/100.0,r['observacion']])
        for row in ws.iter_rows(min_row=2,max_row=1+len(rows),min_col=1,max_col=9):
            for c in row: c.border=bd
            row[7].number_format='0.00%'
        r0=3+len(rows); ws[f'A{r0}']='Resumen'; ws[f'A{r0}'].font=Font(bold=True)
        ws[f'A{r0+1}']='P'; ws[f'B{r0+1}']=stats.get('total_presentes',0)
        ws[f'A{r0+2}']='A'; ws[f'B{r0+2}']=stats.get('total_atrasos',0)
        ws[f'A{r0+3}']='F'; ws[f'B{r0+3}']=stats.get('total_faltas_injustificadas',0)
        ws[f'A{r0+4}']='J'; ws[f'B{r0+4}']=stats.get('total_faltas_justificadas',0)
        ws[f'A{r0+6}']='% General'; ws[f'B{r0+6}']=stats.get('porcentaje_general_asistencia',0)/100.0; ws[f'B{r0+6}'].number_format='0.00%'
        ws[f'F{r0+8}']=context.get('firma_docente',''); ws[f'H{r0+8}']=context.get('firma_rector','')
        wb.save(path); return str(path)
