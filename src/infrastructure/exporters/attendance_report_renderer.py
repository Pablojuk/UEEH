from __future__ import annotations
import base64, html, mimetypes, re
from datetime import datetime
from pathlib import Path
from typing import Any

class AttendanceReportRenderer:
    def render_attendance_quarterly(self, context: dict[str, Any], rows: list[dict[str, Any]], stats: dict[str, Any]) -> str:
        tpl = Path(__file__).resolve().parent.parent / 'templates' / 'reporte_asistencia_trimestral.html'
        template = tpl.read_text(encoding='utf-8')
        values = {
            'institucion_nombre': context.get('institucion_nombre','Institución'), 'institucion_subtitulo': context.get('institucion_subtitulo',''),
            'logo_inst_src': self._build_logo(context.get('logo_path'),'LOGO<br>INST.'), 'logo_mineduc_src': self._build_logo(context.get('logo_ministerio_path'),'MINE<br>DUC'),
            'docente': context.get('docente',''), 'asignatura': context.get('asignatura',''), 'curso': context.get('curso',''), 'nivel': context.get('nivel',''), 'paralelo': context.get('paralelo',''),
            'trimestre': context.get('trimestre',''), 'periodo': context.get('periodo',''), 'anio_lectivo': context.get('periodo_id',''), 'fecha_emision': datetime.now().strftime('%d/%m/%Y'), 'tutor': context.get('tutor',''),
            'rows_html': self._build_rows(rows), 'stats_rows_html': self._build_stats(stats), 'chart_svg': self._build_svg(stats),
            'porcentaje_general_asistencia': f"{float(stats.get('porcentaje_general_asistencia',0)):.2f}%".replace('.',','),
            'firma_docente': context.get('firma_docente', context.get('docente','')), 'firma_rector': context.get('firma_rector', context.get('rector','')),
        }
        pat=re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}|\[\[\s*([a-zA-Z0-9_]+)\s*\]\]")
        raw={'rows_html','stats_rows_html','chart_svg','logo_inst_src','logo_mineduc_src'}
        def repl(m):
            k=m.group(1) or m.group(2) or ''
            v=values.get(k,'')
            return str(v) if k in raw else html.escape(str(v))
        return pat.sub(repl, template)
    def _build_rows(self, rows):
        out=[]
        for r in rows:
            cls='ok' if r['observacion']=='Normal' else ('warn' if r['observacion']=='Seguimiento' else 'bad')
            pct=f"{float(r['porcentaje_asistencia']):.2f}%".replace('.',',')
            out.append(f"<tr><td>{r['nro']}</td><td class='nomina'>{html.escape(str(r['nomina']))}</td><td>{r['dias_laborables']}</td><td>{r['presentes']}</td><td>{r['atrasos']}</td><td>{r['faltas_injustificadas']}</td><td>{r['faltas_justificadas']}</td><td class='bold'>{pct}</td><td class='{cls}'>{r['observacion']}</td></tr>")
        return ''.join(out)
    def _build_stats(self, s):
        rows=[('Presentes',s.get('total_presentes',0),s.get('porcentaje_p',0),'#22C55E'),('Atrasos',s.get('total_atrasos',0),s.get('porcentaje_a',0),'#F59E0B'),('Faltas injustificadas',s.get('total_faltas_injustificadas',0),s.get('porcentaje_f',0),'#EF4444'),('Faltas justificadas',s.get('total_faltas_justificadas',0),s.get('porcentaje_j',0),'#8B5CF6')]
        h=[]
        for n,c,p,color in rows: h.append(f"<tr><td class='s-desc'><span class='dot' style='background:{color}'></span>{n}</td><td>{c}</td><td>{p:.2f}%</td></tr>")
        h.append(f"<tr class='total'><td>TOTAL REGISTROS</td><td>{s.get('total_registros',0)}</td><td>100,00%</td></tr>")
        return ''.join(h).replace('.',',')
    def _build_svg(self,s):
        vals=[('P',s.get('total_presentes',0),s.get('porcentaje_p',0),'#22C55E'),('A',s.get('total_atrasos',0),s.get('porcentaje_a',0),'#F59E0B'),('F',s.get('total_faltas_injustificadas',0),s.get('porcentaje_f',0),'#EF4444'),('J',s.get('total_faltas_justificadas',0),s.get('porcentaje_j',0),'#8B5CF6')]
        x=40; bars=[]
        for k,n,p,c in vals:
            h=max(3,int(float(p)*0.9)); y=120-h
            bars.append(f"<text x='{x+29}' y='{y-6}' text-anchor='middle' font-size='10'>{float(p):.2f}%</text><rect x='{x}' y='{y}' width='58' height='{h}' fill='{c}' stroke='#1F4E79'/><text x='{x+29}' y='136' text-anchor='middle' font-size='10'>{n}</text><text x='{x+29}' y='151' text-anchor='middle' font-size='10'>{k}</text>")
            x+=100
        return "<svg width='100%' height='165' viewBox='0 0 450 165' xmlns='http://www.w3.org/2000/svg'><rect x='0' y='0' width='450' height='165' fill='white'/>"+''.join(bars).replace('.',',')+"</svg>"
    def _build_logo(self,path,placeholder):
        if path and Path(path).exists():
            mime=mimetypes.guess_type(path)[0] or 'image/png'; data=base64.b64encode(Path(path).read_bytes()).decode('ascii')
            return f"<img src='data:{mime};base64,{data}' alt='logo'>"
        return f"<div class='logo-placeholder'>{placeholder}</div>"
