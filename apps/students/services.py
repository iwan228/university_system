"""
Сервис импорта/экспорта данных из Excel-файлов.

Реальный формат файла (из СДО / системы учёта):
  Col 0:  № п/п
  Col 1:  Институт
  Col 4:  Учебная сессия
  Col 5:  Ведомость
  Col 6:  Дисциплина
  Col 8:  Вид контроля
  Col 9:  Студент  (ФИО|зачётка|уровень)
  Col 10: Статус
  Col 11: Попытка
  Col 12: Дата попытки
  Col 13: Оценка
  Col 14: Курс
  Col 15: Группа
  Col 16: Форма обучения
  Col 17: Специальность (код + название)
  Col 18: Преподаватель
"""

import re
from io import BytesIO
from datetime import datetime, date

from django.db import transaction

from apps.students.models import (
    Direction, Group, Subject, Student, AcademicDebt, ExcelImportLog
)


def _read_rows(file_obj, file_name):
    """
    Читает строки из .xls или .xlsx файла.
    Возвращает список строк (каждая строка — list значений), пропуская заголовок.
    """
    raw = file_obj.read()
    magic = raw[:8]

    # OLE Compound (old .xls)  — magic D0CF11E0A1B11AE1
    if magic[:4] == b'\xd0\xcf\x11\xe0':
        import xlrd
        wb = xlrd.open_workbook(file_contents=raw)
        ws = wb.sheet_by_index(0)
        rows = []
        for i in range(1, ws.nrows):  # skip header
            row = [ws.cell_value(i, j) for j in range(ws.ncols)]
            rows.append(row)
        return rows

    # ZIP-based (.xlsx)
    import openpyxl
    from io import BytesIO as BIO
    wb = openpyxl.load_workbook(BIO(raw), read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        rows.append(list(row))
    wb.close()
    return rows


def _safe_str(val):
    """Безопасно приводит к строке, убирая None."""
    if val is None:
        return ''
    return str(val).strip()


def _safe_int(val, default=0):
    """Безопасно приводит к int."""
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _parse_date(val):
    """Парсит дату из строки dd.mm.yyyy или float (xlrd date serial)."""
    if val is None or val == '':
        return None
    if isinstance(val, (date, datetime)):
        return val if isinstance(val, date) else val.date()
    s = _safe_str(val)
    if not s:
        return None
    # Попробуем dd.mm.yyyy
    for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_student_field(raw):
    """
    Парсит поле «Студент»: «Иванов Иван Иванович |17340001|Бакалавр»
    Возвращает (last_name, first_name, patronymic, student_id, education_level)
    """
    s = _safe_str(raw)
    if not s:
        return ('', '', '', '', '')

    parts = [p.strip() for p in s.split('|')]
    fio = parts[0] if len(parts) > 0 else ''
    student_id = parts[1] if len(parts) > 1 else ''
    education_level = parts[2] if len(parts) > 2 else ''

    fio_parts = fio.split()
    last_name = fio_parts[0] if len(fio_parts) > 0 else ''
    first_name = fio_parts[1] if len(fio_parts) > 1 else ''
    patronymic = fio_parts[2] if len(fio_parts) > 2 else ''

    return (last_name, first_name, patronymic, student_id, education_level)


def _parse_direction(raw):
    """
    Парсит поле «Специальность»: «11.03.04 Электроника и наноэлектроника»
    Возвращает (code, name)
    """
    s = _safe_str(raw)
    if not s:
        return ('', '')
    m = re.match(r'^([\d.]+)\s+(.+)$', s)
    if m:
        return (m.group(1), m.group(2))
    return ('', s)


def import_from_excel(file_obj, file_name='import.xlsx'):
    """
    Импортирует данные должников из Excel-файла.
    Поддерживает .xls и .xlsx.
    Возвращает объект ExcelImportLog.
    """
    log = ExcelImportLog(file_name=file_name)
    errors = []

    try:
        rows = _read_rows(file_obj, file_name)
        log.rows_total = len(rows)
        imported = 0

        with transaction.atomic():
            for row_num, row in enumerate(rows, start=2):
                try:
                    # Пропускаем пустые строки
                    if not row or not row[0]:
                        continue

                    # Pad row to at least 19 columns
                    while len(row) < 19:
                        row.append(None)

                    # --- Парсим поля ---
                    institute = _safe_str(row[1])
                    academic_session = _safe_str(row[4])
                    sheet_number = _safe_str(row[5])
                    discipline = _safe_str(row[6])
                    control_type = _safe_str(row[8])

                    # Студент
                    last_name, first_name, patronymic, student_id, education_level = \
                        _parse_student_field(row[9])

                    status = _safe_str(row[10])
                    attempt = _safe_int(row[11], 1)
                    attempt_date = _parse_date(row[12])
                    grade = _safe_str(row[13])
                    course = _safe_int(row[14], 1)
                    group_name = _safe_str(row[15])
                    education_form = _safe_str(row[16])

                    # Специальность
                    dir_code, dir_name = _parse_direction(row[17])

                    teacher = _safe_str(row[18])

                    if not student_id or not last_name:
                        errors.append(f'Строка {row_num}: пустой номер зачётки или фамилия')
                        continue

                    if not discipline:
                        errors.append(f'Строка {row_num}: пустое название дисциплины')
                        continue

                    # --- Создаём / получаем объекты ---

                    # Специальность
                    direction = None
                    if dir_code:
                        direction, _ = Direction.objects.get_or_create(
                            code=dir_code,
                            name=dir_name,
                        )
                    else:
                        direction, _ = Direction.objects.get_or_create(
                            code='00.00.00',
                            defaults={'name': 'Не указана'},
                        )

                    # Группа
                    if group_name:
                        group, created = Group.objects.get_or_create(
                            name=group_name,
                            defaults={'direction': direction, 'course': course}
                        )
                        if not created and course:
                            group.course = course
                            group.direction = direction
                            group.save()
                    else:
                        group, _ = Group.objects.get_or_create(
                            name='Не указана',
                            defaults={'direction': direction, 'course': course}
                        )

                    # Дисциплина
                    subject, _ = Subject.objects.get_or_create(name=discipline)

                    # Студент
                    student, created = Student.objects.get_or_create(
                        student_id=student_id,
                        defaults={
                            'last_name': last_name,
                            'first_name': first_name,
                            'patronymic': patronymic,
                            'group': group,
                            'education_level': education_level,
                            'education_form': education_form,
                        }
                    )
                    if not created:
                        student.last_name = last_name
                        student.first_name = first_name
                        student.patronymic = patronymic
                        student.group = group
                        student.education_level = education_level or student.education_level
                        student.education_form = education_form or student.education_form
                        student.save()

                    # Задолженность
                    AcademicDebt.objects.create(
                        student=student,
                        subject=subject,
                        institute=institute,
                        academic_session=academic_session,
                        sheet_number=sheet_number,
                        control_type=control_type,
                        status=status,
                        attempt=attempt,
                        attempt_date=attempt_date,
                        grade=grade,
                        teacher=teacher,
                    )

                    imported += 1

                except Exception as e:
                    errors.append(f'Строка {row_num}: {str(e)}')

        log.rows_imported = imported

    except Exception as e:
        errors.append(f'Ошибка чтения файла: {str(e)}')

    log.rows_errors = len(errors)
    log.error_details = '\n'.join(errors)
    log.save()

    return log


def export_debts_to_excel(debts_queryset):
    """
    Экспортирует список задолженностей в Excel-файл (.xlsx).
    Возвращает BytesIO с файлом.
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Должники'

    headers = [
        '№ п/п', 'Институт', 'Учебная сессия', 'Ведомость',
        'Дисциплина', 'Вид контроля', 'Студент', 'Статус',
        'Попытка', 'Дата попытки', 'Оценка', 'Курс', 'Группа',
        'Форма обучения', 'Специальность', 'Преподаватель',
    ]
    ws.append(headers)

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1a4d8f', end_color='1a4d8f', fill_type='solid')
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    qs = debts_queryset.select_related(
        'student', 'student__group', 'student__group__direction', 'subject'
    )
    for idx, debt in enumerate(qs, 1):
        s = debt.student
        ws.append([
            idx,
            debt.institute,
            debt.academic_session,
            debt.sheet_number,
            debt.subject.name,
            debt.control_type,
            f'{s.full_name}|{s.student_id}|{s.education_level}',
            debt.status,
            debt.attempt,
            debt.attempt_date.strftime('%d.%m.%Y') if debt.attempt_date else '',
            debt.grade,
            s.group.course,
            s.group.name,
            s.education_form,
            str(s.group.direction),
            debt.teacher,
        ])

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_length + 4, 50)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def export_commission_sheet_to_excel(sheet):
    """Экспортирует ведомость комиссии в Excel."""
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Ведомость комиссии'

    ws.merge_cells('A1:F1')
    ws['A1'] = f'Ведомость комиссии по дисциплине: {sheet.subject.name}'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws['A3'] = 'Дата проведения:'
    ws['B3'] = sheet.date.strftime('%d.%m.%Y')
    ws['A4'] = 'Председатель:'
    ws['B4'] = sheet.chairman
    ws['A5'] = 'Член комиссии 1:'
    ws['B5'] = sheet.member_1
    ws['A6'] = 'Член комиссии 2:'
    ws['B6'] = sheet.member_2
    ws['A7'] = 'Статус:'
    ws['B7'] = 'Открыта' if sheet.is_open else 'Закрыта'

    for row in range(3, 8):
        ws[f'A{row}'].font = Font(bold=True)

    header_row = 9
    entry_headers = ['№', 'ФИО', 'Группа', 'Зачётная книжка', 'Оценка', 'Примечания']
    for col_idx, header in enumerate(entry_headers, 1):
        cell = ws.cell(row=header_row, column=col_idx, value=header)
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='1a4d8f', end_color='1a4d8f', fill_type='solid')

    entries = sheet.entries.select_related('student', 'student__group').all()
    for idx, entry in enumerate(entries, 1):
        row = header_row + idx
        ws.cell(row=row, column=1, value=idx)
        ws.cell(row=row, column=2, value=entry.student.full_name)
        ws.cell(row=row, column=3, value=entry.student.group.name)
        ws.cell(row=row, column=4, value=entry.student.student_id)
        ws.cell(row=row, column=5, value=entry.get_grade_display())
        ws.cell(row=row, column=6, value=entry.notes)

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_length + 4, 50)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
