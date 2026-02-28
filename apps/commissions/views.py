from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.forms import modelformset_factory

from .models import CommissionSheet, CommissionEntry
from .forms import CommissionSheetForm, CommissionEntryForm, AutoFillCommissionForm
from apps.students.models import AcademicDebt, Student
from apps.students.services import export_commission_sheet_to_excel


@login_required
def commission_list(request):
    """Список ведомостей комиссий"""
    sheets = CommissionSheet.objects.select_related('subject').all()

    # Фильтрация по статусу
    status = request.GET.get('status')
    if status in ('open', 'closed'):
        sheets = sheets.filter(status=status)

    context = {'sheets': sheets, 'current_status': status}
    return render(request, 'commissions/commission_list.html', context)


@login_required
def commission_create(request):
    """Создание ведомости комиссии"""
    if request.method == 'POST':
        form = CommissionSheetForm(request.POST)
        if form.is_valid():
            sheet = form.save()
            messages.success(request, 'Ведомость комиссии создана.')
            return redirect('commissions:commission_detail', sheet_id=sheet.id)
    else:
        form = CommissionSheetForm()

    return render(request, 'commissions/commission_form.html', {
        'form': form,
        'title': 'Новая ведомость комиссии',
    })


@login_required
def commission_detail(request, sheet_id):
    """Просмотр и редактирование ведомости комиссии"""
    sheet = get_object_or_404(CommissionSheet, pk=sheet_id)
    entries = sheet.entries.select_related('student', 'student__group').all()

    context = {
        'sheet': sheet,
        'entries': entries,
    }
    return render(request, 'commissions/commission_detail.html', context)


@login_required
def commission_edit(request, sheet_id):
    """Редактирование ведомости"""
    sheet = get_object_or_404(CommissionSheet, pk=sheet_id)

    if request.method == 'POST':
        form = CommissionSheetForm(request.POST, instance=sheet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ведомость обновлена.')
            return redirect('commissions:commission_detail', sheet_id=sheet.id)
    else:
        form = CommissionSheetForm(instance=sheet)

    return render(request, 'commissions/commission_form.html', {
        'form': form,
        'title': f'Редактировать: {sheet}',
        'sheet': sheet,
    })


@login_required
def commission_autofill(request, sheet_id):
    """Автоматическое заполнение ведомости должниками по предмету"""
    sheet = get_object_or_404(CommissionSheet, pk=sheet_id)

    # Находим всех должников по предмету ведомости
    debts = AcademicDebt.objects.filter(
        subject=sheet.subject,
    ).select_related('student')

    added = 0
    skipped = 0
    for debt in debts:
        # Проверяем, нет ли уже студента в ведомости
        entry, created = CommissionEntry.objects.get_or_create(
            sheet=sheet,
            student=debt.student,
            defaults={'debt': debt}
        )
        if created:
            added += 1
        else:
            skipped += 1

    if added:
        messages.success(request, f'Добавлено {added} студентов в ведомость.')
    if skipped:
        messages.info(request, f'{skipped} студентов уже были в ведомости.')
    if not added and not skipped:
        messages.warning(request, 'Нет активных должников по данному предмету.')

    return redirect('commissions:commission_detail', sheet_id=sheet.id)


@login_required
def commission_add_student(request, sheet_id):
    """Добавить студента в ведомость вручную"""
    sheet = get_object_or_404(CommissionSheet, pk=sheet_id)

    if not sheet.is_open:
        messages.warning(request, 'Нельзя добавлять студентов в закрытую ведомость.')
        return redirect('commissions:commission_detail', sheet_id=sheet.id)

    if request.method == 'POST':
        form = CommissionEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.sheet = sheet

            # Проверка: не записан ли уже
            if CommissionEntry.objects.filter(sheet=sheet, student=entry.student).exists():
                messages.warning(request, 'Студент уже записан в эту ведомость.')
            else:
                # Предупреждение если ведомость по предмету ещё не закрыта
                open_sheets = CommissionSheet.objects.filter(
                    subject=sheet.subject,
                    status='open'
                ).exclude(pk=sheet.pk)
                if open_sheets.exists():
                    messages.warning(
                        request,
                        'Внимание! Существуют другие открытые ведомости по этому '
                        'предмету. Убедитесь, что предыдущие ведомости закрыты.'
                    )

                entry.save()
                messages.success(request, f'Студент {entry.student} добавлен.')

            return redirect('commissions:commission_detail', sheet_id=sheet.id)
    else:
        form = CommissionEntryForm()

    return render(request, 'commissions/add_student.html', {
        'form': form,
        'sheet': sheet,
    })


@login_required
def commission_update_grade(request, sheet_id, entry_id):
    """Обновить оценку студента в ведомости"""
    sheet = get_object_or_404(CommissionSheet, pk=sheet_id)
    entry = get_object_or_404(CommissionEntry, pk=entry_id, sheet=sheet)

    if request.method == 'POST':
        form = CommissionEntryForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save()

            # Если оценка положительная — отмечаем в примечаниях
            if entry.grade in ('3', '4', '5', 'pass') and entry.debt:
                entry.debt.notes = 'Закрыта по комиссии'
                entry.debt.save()
            elif entry.grade == 'absent' and entry.debt:
                entry.debt.absence_noted = True
                entry.debt.save()

            messages.success(request, 'Оценка обновлена.')
            return redirect('commissions:commission_detail', sheet_id=sheet.id)
    else:
        form = CommissionEntryForm(instance=entry)

    return render(request, 'commissions/update_grade.html', {
        'form': form,
        'sheet': sheet,
        'entry': entry,
    })


@login_required
def commission_close(request, sheet_id):
    """Закрыть ведомость"""
    sheet = get_object_or_404(CommissionSheet, pk=sheet_id)

    if request.method == 'POST':
        sheet.status = 'closed'
        sheet.save()
        messages.success(request, 'Ведомость закрыта.')

    return redirect('commissions:commission_detail', sheet_id=sheet.id)


@login_required
def commission_export(request, sheet_id):
    """Экспорт ведомости в Excel"""
    sheet = get_object_or_404(CommissionSheet, pk=sheet_id)
    output = export_commission_sheet_to_excel(sheet)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'vedomost_{sheet.subject.name}_{sheet.date:%Y%m%d}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def commission_remove_entry(request, sheet_id, entry_id):
    """Удаление студента из ведомости"""
    sheet = get_object_or_404(CommissionSheet, pk=sheet_id)
    entry = get_object_or_404(CommissionEntry, pk=entry_id, sheet=sheet)

    if not sheet.is_open:
        messages.warning(request, 'Нельзя изменять закрытую ведомость.')
        return redirect('commissions:commission_detail', sheet_id=sheet.id)

    if request.method == 'POST':
        # Убираем примечание о комиссии
        if entry.debt:
            entry.debt.notes = ''
            entry.debt.save()
        student_name = str(entry.student)
        entry.delete()
        messages.success(request, f'Студент {student_name} удалён из ведомости.')

    return redirect('commissions:commission_detail', sheet_id=sheet.id)
