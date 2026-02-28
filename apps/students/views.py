from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator

from .models import AcademicDebt, Student, Group, Direction, Subject, ExcelImportLog
from .filters import AcademicDebtFilter
from .forms import ExcelImportForm, AcademicDebtForm
from .services import import_from_excel, export_debts_to_excel


@login_required
def debt_list(request):
    """Список должников с многоуровневыми фильтрами"""
    queryset = AcademicDebt.objects.select_related(
        'student', 'student__group', 'student__group__direction', 'subject'
    )
    debt_filter = AcademicDebtFilter(request.GET, queryset=queryset)
    filtered_qs = debt_filter.qs

    paginator = Paginator(filtered_qs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': debt_filter,
        'page_obj': page_obj,
        'total_count': filtered_qs.count(),
        'courses': sorted(set(
            Group.objects.values_list('course', flat=True)
        )),
        'statuses': sorted(set(
            AcademicDebt.objects.exclude(status='').values_list('status', flat=True)
        )),
        'control_types': sorted(set(
            AcademicDebt.objects.exclude(control_type='').values_list('control_type', flat=True)
        )),
        'institutes': sorted(set(
            AcademicDebt.objects.exclude(institute='').values_list('institute', flat=True)
        )),
        'sessions': sorted(set(
            AcademicDebt.objects.exclude(academic_session='').values_list('academic_session', flat=True)
        )),
    }
    return render(request, 'students/debt_list.html', context)


@login_required
def toggle_absence(request, debt_id):
    """Переключение отметки о неявке"""
    debt = get_object_or_404(AcademicDebt, pk=debt_id)
    debt.absence_noted = not debt.absence_noted
    debt.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'absence_noted': debt.absence_noted})

    messages.success(request, f'Отметка о неявке {"установлена" if debt.absence_noted else "снята"}.')
    return redirect('debt_list')


@login_required
def debt_edit(request, debt_id):
    """Редактирование задолженности"""
    debt = get_object_or_404(AcademicDebt, pk=debt_id)

    if request.method == 'POST':
        form = AcademicDebtForm(request.POST, instance=debt)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задолженность обновлена.')
            return redirect('debt_list')
    else:
        form = AcademicDebtForm(instance=debt)

    return render(request, 'students/debt_edit.html', {'form': form, 'debt': debt})


@login_required
def import_excel(request):
    """Импорт данных из Excel"""
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            log = import_from_excel(file, file_name=file.name)

            if log.rows_errors > 0:
                messages.warning(
                    request,
                    f'Импорт завершён. Загружено: {log.rows_imported} из {log.rows_total}. '
                    f'Ошибок: {log.rows_errors}.'
                )
            else:
                messages.success(
                    request,
                    f'Импорт успешно завершён! Загружено: {log.rows_imported} записей.'
                )
            return redirect('import_log_detail', log_id=log.id)
    else:
        form = ExcelImportForm()

    recent_logs = ExcelImportLog.objects.all()[:10]
    return render(request, 'students/import_excel.html', {
        'form': form,
        'recent_logs': recent_logs,
    })


@login_required
def import_log_detail(request, log_id):
    """Детали импорта"""
    log = get_object_or_404(ExcelImportLog, pk=log_id)
    return render(request, 'students/import_log_detail.html', {'log': log})


@login_required
def export_excel(request):
    """Экспорт текущего отфильтрованного списка в Excel"""
    queryset = AcademicDebt.objects.select_related(
        'student', 'student__group', 'student__group__direction', 'subject'
    )
    debt_filter = AcademicDebtFilter(request.GET, queryset=queryset)
    output = export_debts_to_excel(debt_filter.qs)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="dolzhniki.xlsx"'
    return response


@login_required
def api_groups_by_direction(request):
    """API: группы по направлению (для динамической фильтрации)"""
    direction_id = request.GET.get('direction_id')
    if direction_id:
        groups = Group.objects.filter(direction_id=direction_id).values('id', 'name')
    else:
        groups = Group.objects.all().values('id', 'name')
    return JsonResponse(list(groups), safe=False)
