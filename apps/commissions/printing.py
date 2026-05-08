from io import BytesIO
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _register_cyrillic_font():
    """Try to register a TTF font that supports Cyrillic.

    Returns the font name to use in reportlab styles.
    Tries common locations for DejaVuSans; falls back to Helvetica.
    """
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf',
        'C:\\Windows\\Fonts\\DejaVuSans.ttf',
        'C:\\Windows\\Fonts\\arial.ttf',
        '/Library/Fonts/DejaVuSans.ttf',
        '/Library/Fonts/Arial Unicode.ttf',
    ]

    for path in candidates:
        try:
            if os.path.exists(path):
                font_name = os.path.splitext(os.path.basename(path))[0]
                registered_name = f'F_{font_name}'
                pdfmetrics.registerFont(TTFont(registered_name, path))
                return registered_name
        except Exception:
            continue

    try:
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        bundled = os.path.join(base, 'static', 'fonts', 'DejaVuSans.ttf')
        if os.path.exists(bundled):
            pdfmetrics.registerFont(TTFont('F_DejaVuSans', bundled))
            return 'F_DejaVuSans'
    except Exception:
        pass

    return 'Helvetica'


def generate_commission_protocol_pdf(sheet, entries):
    """Generate a printable PDF protocol for a commission sheet.

    Returns BytesIO with PDF content.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    story = []

    font_name = _register_cyrillic_font()
    title_style = ParagraphStyle('title', parent=styles['Heading2'], alignment=1, fontName=font_name)
    normal_style = ParagraphStyle('normal', parent=styles['Normal'], fontName=font_name)

    story.append(Paragraph(f'Ведомость комиссии: {sheet.subject.name}', title_style))
    story.append(Spacer(1, 6))

    meta = f"Дата: {sheet.date.strftime('%d.%m.%Y')}    Председатель: {sheet.chairman or '-'}"
    story.append(Paragraph(meta, normal_style))
    story.append(Spacer(1, 6))

    header = ['№', 'ФИО студента', 'Группа', 'Зачётная книжка', 'Оценка', 'Примечания']
    table_data = [header]

    for i, entry in enumerate(entries, start=1):
        student = entry.student
        table_data.append([
            str(i),
            student.full_name,
            student.group.name,
            student.student_id,
            entry.get_grade_display() if hasattr(entry, 'get_grade_display') else (entry.grade or ''),
            entry.notes or '',
        ])

    table = Table(table_data, colWidths=[20*mm, 80*mm, 35*mm, 35*mm, 30*mm, 60*mm])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # Footer with commission members
    members = f"Председатель: {sheet.chairman or '-'}; Члены: {sheet.member_1 or '-'}, {sheet.member_2 or '-'}"
    story.append(Paragraph(members, normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_commission_order_pdf(sheet, entries, order_text=None):
    """Generate a printable administrative order (распоряжение) for a commission.

    order_text: optional textual instruction to include in the order.
    Returns BytesIO with PDF content.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []

    font_name = _register_cyrillic_font()
    title_style = ParagraphStyle('title', parent=styles['Heading2'], alignment=1, fontName=font_name)
    normal_style = ParagraphStyle('normal', parent=styles['Normal'], fontName=font_name)
    story.append(Paragraph('Распоряжение', title_style))
    story.append(Spacer(1, 12))

    meta = f"По дисциплине: {sheet.subject.name}. Дата комиссии: {sheet.date.strftime('%d.%m.%Y')}"
    story.append(Paragraph(meta, normal_style))
    story.append(Spacer(1, 12))

    if order_text:
        story.append(Paragraph(order_text, normal_style))
        story.append(Spacer(1, 12))

    # List students and outcomes
    for i, entry in enumerate(entries, start=1):
        s = entry.student
        grade_text = entry.grade if entry.grade else (entry.get_grade_display() if hasattr(entry, 'get_grade_display') else '-')
        line = f"{i}. {s.full_name} ({s.student_id}), Группа: {s.group.name} — Оценка: {grade_text}"
        story.append(Paragraph(line, normal_style))

    story.append(Spacer(1, 18))
    story.append(Paragraph(f'Подпись председателя: ______________________ {sheet.chairman or ""}', normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
