from __future__ import annotations
import base64, html, mimetypes, re
from datetime import datetime
from pathlib import Path
from typing import Any

class AttendanceReportRenderer:
    def render_attendance_quarterly(self, context: dict[str, Any], rows: list[dict[str, Any]], stats: dict[str, Any]) -> str:
        template=(Path(__file__).resolve().parent.parent/'templates'/'reporte_asistencia_trimestral.html').read_text(encoding='utf-8')
        logo_inst=self._build_logo_source(context.get('logo_path'))
        logo_min=self._build_logo_source(context.get('logo_ministerio_path'))
        values={
            'institucion_nombre':context.get('institucion_nombre','Institución'),'institucion_subtitulo':context.get('institucion_subtitulo',''),
            'logo_inst_src':logo_inst,'logo_mineduc_src':logo_min,'logo_inst_html':f"<img src='{logo_inst}' class='logo-img' alt='Logo institucional'>" if logo_inst else "<div class='logo-placeholder'>LOGO<br>INST.</div>",
            'logo_mineduc_html':f"<img src='{logo_min}' class='logo-img' alt='Logo ministerio'>" if logo_min else "<div class='logo-placeholder'>MINE<br>DUC</div>",
            'docente':context.get('docente',''),'asignatura':context.get('asignatura',''),'curso':context.get('curso',''),'nivel':context.get('nivel',''),'paralelo':context.get('paralelo',''),
            'trimestre':context.get('trimestre',''),'periodo':context.get('periodo',''),'anio_lectivo':context.get('periodo_id',''),'fecha_emision':datetime.now().strftime('%d/%m/%Y'),'tutor':context.get('tutor',''),
            'rows_html':self._build_rows(rows),'stats_rows_html':self._build_stats(stats),'chart_svg':self._build_svg(stats),
            'porcentaje_general_asistencia':f"{float(stats.get('porcentaje_general_asistencia',0)):.2f}%".replace('.',','),'firma_docente':context.get('firma_docente',context.get('docente','')),'firma_rector':context.get('firma_rector',context.get('rector','')),
        }
        pat=re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}|\[\[\s*([a-zA-Z0-9_]+)\s*\]\]")
        raw={'rows_html','stats_rows_html','chart_svg','logo_inst_html','logo_mineduc_html'}
        return pat.sub(lambda m: str(values.get((m.group(1) or m.group(2) or ''),'')) if (m.group(1) or m.group(2)) in raw else html.escape(str(values.get((m.group(1) or m.group(2) or ''),''))),template)
    def _build_rows(self,rows):
        out=[]
        for r in rows:
            cls='ok' if r['observacion']=='Normal' else ('warn' if r['observacion']=='Seguimiento' else 'bad')
            pct=f"{float(r['porcentaje_asistencia']):.2f}%".replace('.',',')
            obs=r.get('observacion',''); out.append(f"<tr><td>{r['nro']}</td><td class='nomina'>{html.escape(str(r['nomina']))}</td><td>{r['dias_laborables']}</td><td>{r['presentes']}</td><td>{r['atrasos']}</td><td>{r['faltas_injustificadas']}</td><td>{r['faltas_justificadas']}</td><td class='bold'>{pct}</td><td class='{self._observation_class(obs)}'>{obs}</td></tr>")
        return ''.join(out)
    def _build_stats(self,s):
        rows=[('Presentes',s.get('total_presentes',0),s.get('porcentaje_p',s.get('porcentaje_presentes',0)),'dot-p'),('Atrasos',s.get('total_atrasos',0),s.get('porcentaje_a',s.get('porcentaje_atrasos',0)),'dot-a'),('Faltas injustificadas',s.get('total_faltas_injustificadas',0),s.get('porcentaje_f',s.get('porcentaje_faltas_injustificadas',0)),'dot-f'),('Faltas justificadas',s.get('total_faltas_justificadas',0),s.get('porcentaje_j',s.get('porcentaje_faltas_justificadas',0)),'dot-j')]
        h=[f"<tr><td class='s-desc'><span class='dot {c}'></span>{n}</td><td>{v}</td><td>{p:.2f}%</td></tr>" for n,v,p,c in rows]
        h.append(f"<tr class='total'><td>TOTAL REGISTROS</td><td>{s.get('total_registros',0)}</td><td>100,00%</td></tr>")
        return ''.join(h).replace('.',',')
    def _build_svg(self,s):
        vals=[('P',s.get('total_presentes',0),s.get('porcentaje_p',0),'#22C55E'),('A',s.get('total_atrasos',0),s.get('porcentaje_a',0),'#F59E0B'),('F',s.get('total_faltas_injustificadas',0),s.get('porcentaje_f',0),'#EF4444'),('J',s.get('total_faltas_justificadas',0),s.get('porcentaje_j',0),'#8B5CF6')]
        bars=[]; x=45
        for k,n,p,c in vals:
            bh=max(4,min(78,int(float(p)*0.8))); y=100-bh
            bars.append(f"<text x='{x+24}' y='{max(16,y-6)}' text-anchor='middle' font-size='9'>{float(p):.2f}%</text><rect x='{x}' y='{y}' width='48' height='{bh}' fill='{c}' stroke='#1F4E79'/><text x='{x+24}' y='116' text-anchor='middle' font-size='9'>{n}</text><text x='{x+24}' y='130' text-anchor='middle' font-size='9'>{k}</text>")
            x+=92
        return "<svg width='100%' height='125' viewBox='0 0 450 145' xmlns='http://www.w3.org/2000/svg'><rect x='0' y='0' width='450' height='145' fill='white'/>"+''.join(bars).replace('.',',')+"</svg>"
    def _build_logo_source(self,path_value:Any)->str:
        path=self._normalize_existing_path(path_value)
        if path is None: return ''
        mime=mimetypes.guess_type(str(path))[0] or 'image/png'
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
    def _normalize_existing_path(self,path_value:Any)->Path|None:
        raw=str(path_value or '').strip()
        if not raw: return None
        c=[Path(raw),Path.cwd()/raw,Path(__file__).resolve().parents[3]/raw]
        for p in c:
            try:
                rp=p.expanduser().resolve()
            except Exception:
                continue
            if rp.exists(): return rp
        return None


    def render_attendance_annual(self, context: dict[str, Any], rows: list[dict[str, Any]], stats: dict[str, Any]) -> str:
        template=(Path(__file__).resolve().parent.parent/'templates'/'reporte_asistencia_anual.html').read_text(encoding='utf-8')
        logo_inst=self._build_logo_source(context.get('logo_path')); logo_min=self._build_logo_source(context.get('logo_ministerio_path'))
        values={
            'institucion_nombre':context.get('institucion_nombre','Institución'),'institucion_subtitulo':context.get('institucion_subtitulo',''),'logo_inst_src':logo_inst,'logo_mineduc_src':logo_min,
            'logo_inst_html':f"<img src='{logo_inst}' class='logo-img'>" if logo_inst else "<div class='logo-placeholder'>LOGO<br>INST.</div>",
            'logo_mineduc_html':f"<img src='{logo_min}' class='logo-img'>" if logo_min else "<div class='logo-placeholder'>MINE<br>DUC</div>",
            'docente':context.get('docente',''),'asignatura':context.get('asignatura',''),'curso':context.get('curso',''),'nivel':context.get('nivel',''),'paralelo':context.get('paralelo',''),'anio_lectivo':context.get('periodo_id',''),
            'periodo_anual':context.get('periodo_anual',''),'periodo_t1':context.get('periodo_t1',''),'periodo_t2':context.get('periodo_t2',''),'periodo_t3':context.get('periodo_t3',''),'fecha_emision':datetime.now().strftime('%d/%m/%Y'),
            'rows_html':self._build_annual_rows_html(rows),'stats_rows_html':self._build_stats(stats),'chart_svg':self._build_svg({'total_presentes':stats.get('total_presentes',0),'total_atrasos':stats.get('total_atrasos',0),'total_faltas_injustificadas':stats.get('total_faltas_injustificadas',0),'total_faltas_justificadas':stats.get('total_faltas_justificadas',0),'porcentaje_p':stats.get('porcentaje_presentes',0),'porcentaje_a':stats.get('porcentaje_atrasos',0),'porcentaje_f':stats.get('porcentaje_faltas_injustificadas',0),'porcentaje_j':stats.get('porcentaje_faltas_justificadas',0)}),
            'porcentaje_general_anual_asistencia':f"{float(stats.get('porcentaje_general_anual_asistencia',0)):.2f}%".replace('.',','),'firma_docente':context.get('firma_docente',''),'firma_rector':context.get('firma_rector','')
        }
        pat=re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}|\[\[\s*([a-zA-Z0-9_]+)\s*\]\]")
        raw={'rows_html','stats_rows_html','chart_svg','logo_inst_html','logo_mineduc_html'}
        return pat.sub(lambda m: str(values.get((m.group(1) or m.group(2) or ''),'')) if (m.group(1) or m.group(2)) in raw else html.escape(str(values.get((m.group(1) or m.group(2) or ''),''))),template)

    def _build_annual_rows_html(self, rows: list[dict[str, Any]]) -> str:
        out=[]
        for r in rows:
            pct=f"{float(r.get('porcentaje_asistencia_anual',0)):.2f}%".replace('.',',')
            obs=r.get('observacion',''); out.append(f"<tr><td>{r.get('nro','')}</td><td class='nomina'>{html.escape(str(r.get('nomina','')))}</td><td>{r.get('t1_dias',0)}</td><td>{r.get('t1_faltas',0)}</td><td>{float(r.get('t1_porcentaje',0)):.1f}%</td><td>{r.get('t2_dias',0)}</td><td>{r.get('t2_faltas',0)}</td><td>{float(r.get('t2_porcentaje',0)):.1f}%</td><td>{r.get('t3_dias',0)}</td><td>{r.get('t3_faltas',0)}</td><td>{float(r.get('t3_porcentaje',0)):.1f}%</td><td>{r.get('dias_total',0)}</td><td>{r.get('presentes_total',0)}</td><td>{r.get('atrasos_total',0)}</td><td>{r.get('faltas_injustificadas_total',0)}</td><td>{r.get('faltas_justificadas_total',0)}</td><td>{pct}</td><td class='{self._observation_class(obs)}'>{obs}</td></tr>")
        return ''.join(out).replace('.',',')

    def _observation_class(self, obs: str) -> str:
        t=str(obs or '').lower()
        if 'riesgo' in t: return 'obs-riesgo'
        if 'alerta' in t: return 'obs-alerta'
        if 'seguimiento' in t: return 'obs-seguimiento'
        return 'obs-normal'
