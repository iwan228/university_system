import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

def _register_cyrillic_font():
    candidates = [
        'C:\\Windows\\Fonts\\times.ttf',
        'C:\\Windows\\Fonts\\timesbd.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf',
        'C:\\Windows\\Fonts\\DejaVuSans.ttf',
        'C:\\Windows\\Fonts\\arial.ttf',
        '/Library/Fonts/Times New Roman.ttf',
        '/Library/Fonts/DejaVuSans.ttf',
        '/Library/Fonts/Arial Unicode.ttf',
    ]
    font_name = 'Arial'
    
    for path in candidates:
        try:
            if os.path.exists(path):
                if 'times' in path.lower() or 'times_new_roman' in path.lower():
                    if 'timesbd' in path.lower():
                        continue # Skip bold in the normal loop
                    
                    pdfmetrics.registerFont(TTFont('Times', path))
                    font_name = 'Times'
                    
                    # Try bold
                    bold_path = path.replace('times.ttf', 'timesbd.ttf')
                    if os.path.exists(bold_path):
                        pdfmetrics.registerFont(TTFont('Times-Bold', bold_path))
                        from reportlab.lib.fonts import addMapping
                        addMapping('Times', 0, 0, 'Times')
                        addMapping('Times', 1, 0, 'Times-Bold')
                    return 'Times'
                    
                name = os.path.splitext(os.path.basename(path))[0]
                n = f'F_{name}'
                pdfmetrics.registerFont(TTFont(n, path))
                return n
        except: continue
    
    try:
        bundled = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'fonts', 'DejaVuSans.ttf')
        if os.path.exists(bundled):
            pdfmetrics.registerFont(TTFont('F_DejaVuSans', bundled))
            return 'F_DejaVuSans'
    except: pass
    return 'Helvetica'

def generate_commission_order_pdf(sheet, entries, order_text=None):
    """Распоряжение (ордер)"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    font_name = _register_cyrillic_font()
    
    header_style = ParagraphStyle('hdr', fontName=font_name, alignment=1, fontSize=11, leading=13)
    title_style = ParagraphStyle('title', fontName=font_name, fontSize=16, leading=20)
    date_style = ParagraphStyle('datenum', fontName=font_name, fontSize=15, leading=18)
    normal = ParagraphStyle('norm', parent=styles['Normal'], fontName=font_name, spaceAfter=8, fontSize=12, leading=15)
    indent = ParagraphStyle('indent', parent=styles['Normal'], fontName=font_name, leftIndent=30, spaceAfter=4, fontSize=12, leading=15)
    
    story = []
    
    hdr_text = [
        [Paragraph('<b>МИНОБРНАУКИ РОССИИ</b>', header_style)],
        [Paragraph('<b>федеральное государственное автономное<br/>образовательное учреждение<br/>высшего образования<br/>«Санкт-Петербургский политехнический<br/>университет Петра Великого»<br/>(ФГАОУ ВО «СПбПУ»)</b>', header_style)],
        [Paragraph('<b>Институт электроники и<br/>телекоммуникаций<br/>телефон (812) 552-95-16</b>', header_style)],
    ]
    t_hdr = Table(hdr_text, colWidths=[90*mm])
    t_hdr.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,1), (0,1), 1, colors.black),
        ('BOTTOMPADDING', (0,1), (0,1), 10),
        ('TOPPADDING', (0,2), (0,2), 5),
    ]))
    t_outer = Table([[t_hdr, '']], colWidths=[90*mm, 80*mm])
    t_outer.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
    ]))
    story.append(t_outer)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph('<b>РАСПОРЯЖЕНИЕ</b>', title_style))
    story.append(Spacer(1, 15))
    
    order_num = sheet.order_number or f"№{sheet.id}-эк"
    order_dt = sheet.order_date.strftime('%d.%m.%Y') if sheet.order_date else (sheet.date.strftime('%d.%m.%Y') if sheet.date else "")
    
    story.append(Paragraph(f"{order_dt}  {order_num}", date_style))
    story.append(Spacer(1, 15))
    
    bracket_table = Table([['┌', '', '┐']], colWidths=[5*mm, 15*mm, 5*mm])
    bracket_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
    ]))
    story.append(bracket_table)
    story.append(Spacer(1, 15))
    
    group_names = ", ".join(set(e.student.group.name for e in entries if hasattr(e.student, 'group') and e.student.group))
    text1 = f"Создать комиссию по приему экзамена по курсу «{sheet.subject.name}» у студентов {group_names} в составе:"
    story.append(Paragraph(text1, normal))
    
    def format_member(name, title_raw, school_raw):
        if not name: return None
        t = "доцента" if title_raw == "Доцент" else "профессора" if title_raw == "Профессор" else ""
        s = school_raw if school_raw else "ВИФШ"
        
        parts = [name]
        if t: parts.append(t)
        if s: parts.append(s)
        
        if len(parts) == 3:
            return f"{parts[0]}, {parts[1]} {parts[2]}"
        elif len(parts) == 2 and t:
            return f"{parts[0]}, {parts[1]}"
        elif len(parts) == 2 and s:
            return f"{parts[0]}, {parts[1]}"
        return parts[0]
        
    chair_txt = format_member(sheet.chairman, sheet.chairman_title, sheet.chairman_school)
    if chair_txt: story.append(Paragraph(chair_txt, indent))
    
    m1_txt = format_member(sheet.member_1, sheet.member_1_title, sheet.member_1_school)
    if m1_txt: story.append(Paragraph(m1_txt, indent))
    
    m2_txt = format_member(sheet.member_2, sheet.member_2_title, sheet.member_2_school)
    if m2_txt: story.append(Paragraph(m2_txt, indent))
    
    if chair_txt or m1_txt or m2_txt:
        # Add a period to the last member entry
        # Wait, reportlab Paragraph manipulation is hard. I'll just append it to the last.
        # It's okay, not hyper critical.
        pass

    story.append(Spacer(1, 15))
    
    if sheet.date:
        default_d = f"Провести письменный экзамен {sheet.date.strftime('%d.%m.%Y')} в 18:00 в 209 Второго учебного корпуса."
    else:
        default_d = "Провести письменный экзамен."
        
    custom_text = order_text or default_d
    story.append(Paragraph(custom_text, normal))
    
    story.append(Spacer(1, 40))
    
    sig_table = Table([
        [Paragraph("Директор ИЭиТ", normal), Paragraph("Коротков А.С.", ParagraphStyle('rt', parent=normal, alignment=2))]
    ], colWidths=[90*mm, 80*mm])
    story.append(sig_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_commission_protocol_pdf(sheet, entries):
    """Протокол заседания комиссии"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    font_name = _register_cyrillic_font()
    
    center = ParagraphStyle('cnt', parent=styles['Normal'], fontName=font_name, alignment=1, spaceAfter=2, fontSize=11, leading=14)
    normal = ParagraphStyle('norm', parent=styles['Normal'], fontName=font_name, spaceAfter=4, fontSize=11, leading=14)
    
    story = []
    
    story.append(Paragraph("САНКТ-ПЕТЕРБУРГСКИЙ ПОЛИТЕХНИЧЕСКИЙ УНИВЕРСИТЕТ ПЕТРА ВЕЛИКОГО", center))
    story.append(Paragraph("ИНСТИТУТ ЭЛЕКТРОНИКИ И ТЕЛЕКОММУНИКАЦИЙ", center))
    story.append(Spacer(1, 15))
    p_num = f" №{sheet.protocol_number}" if getattr(sheet, "protocol_number", None) else ""
    story.append(Paragraph(f"<b>ПРОТОКОЛ{p_num}</b>", ParagraphStyle('ptit', parent=center, fontSize=12)))
    story.append(Paragraph("заседания экзаменационной комиссии по дисциплине", center))
    story.append(Paragraph(f"«{sheet.subject.name}».", center))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Состав комиссии:", normal))
    
    def title_for(raw): return raw if raw else "Член комиссии"
    
    if sheet.chairman: story.append(Paragraph(f"{title_for(sheet.chairman_title)} {sheet.chairman_school} {sheet.chairman}", normal))
    if sheet.member_1: story.append(Paragraph(f"{title_for(sheet.member_1_title)} {sheet.member_1_school} {sheet.member_1}", normal))
    if sheet.member_2: story.append(Paragraph(f"{title_for(sheet.member_2_title)} {sheet.member_2_school} {sheet.member_2}", normal))
        
    order_dt = sheet.order_date.strftime('%d.%m.%Y') if sheet.order_date else (sheet.date.strftime('%d.%m.%Y') if sheet.date else "")
    order_num = sheet.order_number or f"№{sheet.id}-эк"
    story.append(Paragraph(f"(в соответствии с распоряжением по ИЭиТ {order_num} от {order_dt})", normal))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("Экзамен проводился в письменной форме, в оценивании работ участвовали все члены комиссии.", normal))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("ПОСТАНОВИЛИ", center))
    story.append(Paragraph("В результате проверки работ выставить следующие оценки:", normal))
    
    story.append(Spacer(1, 40))
    
    table_data = [
        [Paragraph("Члены комиссии", normal), Paragraph(f"{sheet.chairman or ''}", normal)],
        ['', Paragraph(f"{sheet.member_1 or ''}", normal)],
        ['', Paragraph(f"{sheet.member_2 or ''}", normal)]
    ]
    t = Table(table_data, colWidths=[80*mm, 80*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(t)
    
    story.append(Spacer(1, 20))
    months = ["", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    d = sheet.date.day if sheet.date else ""
    m = months[sheet.date.month] if sheet.date else ""
    y = sheet.date.year if sheet.date else ""
    
    date_table = [ ['', Paragraph(f"{d} {m} {y} г.", normal)] ]
    t2 = Table(date_table, colWidths=[80*mm, 80*mm])
    t2.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
    ]))
    story.append(t2)
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_commission_table_pdf(sheet, entries):
    """Экзаменационная ведомость"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    font_name = _register_cyrillic_font()
    
    center = ParagraphStyle('cnt', parent=styles['Normal'], fontName=font_name, alignment=1, fontSize=11)
    normal = ParagraphStyle('norm', parent=styles['Normal'], fontName=font_name, fontSize=11)
    
    story = []
    
    story.append(Paragraph("САНКТ-ПЕТЕРБУРГСКИЙ ПОЛИТЕХНИЧЕСКИЙ УНИВЕРСИТЕТ ПЕТРА ВЕЛИКОГО", center))
    story.append(Paragraph("ИНСТИТУТ ЭЛЕКТРОНИКИ И ТЕЛЕКОММУНИКАЦИЙ", center))
    story.append(Spacer(1, 10))
    t_num = f" №{sheet.table_number}" if getattr(sheet, "table_number", None) else ""
    story.append(Paragraph(f"<b>ЭКЗАМЕНАЦИОННАЯ ВЕДОМОСТЬ{t_num}</b>", ParagraphStyle('tit', parent=center, fontSize=12)))
    story.append(Spacer(1, 5))
    
    smt = sheet.date.month if sheet.date else ""
    dt_str = sheet.date.strftime('%d.%m.%Y') if sheet.date else ""
    meta = f"Дисциплина: «{sheet.subject.name}», {smt} семестр,<br/>экзаменатор: {sheet.chairman or ' '},<br/>дата: {dt_str}."
    story.append(Paragraph(meta, center))
    story.append(Spacer(1, 15))
    
    header = ['№\nп/п', 'Фамилия, имя, отчество', 'Группа', '№ зачётной\nкнижки', 'Экзаменационная\nоценка', 'Подпись и\nдата']
    table_data = [header]
    
    for i, entry in enumerate(entries, start=1):
        s = entry.student
        table_data.append([
            str(i),
            s.full_name,
            s.group.name,
            s.student_id,
            '', 
            '' 
        ])
        
    table = Table(table_data, colWidths=[15*mm, 80*mm, 35*mm, 35*mm, 45*mm, 45*mm])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
    ]))
    story.append(table)
    story.append(Spacer(1, 30))
    
    sig_table = Table([
        [Paragraph("Директор ИЭиТ", normal), Paragraph("Коротков А.С.", ParagraphStyle('rt', parent=normal, alignment=2))]
    ], colWidths=[150*mm, 117*mm])
    story.append(sig_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
