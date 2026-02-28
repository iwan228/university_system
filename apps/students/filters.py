import django_filters
from django.db import models as db_models

from .models import AcademicDebt, Direction, Group, Subject


class AcademicDebtFilter(django_filters.FilterSet):
    """Многоуровневые фильтры для списка должников"""

    student_name = django_filters.CharFilter(
        method='filter_student_name',
        label='ФИО студента',
    )
    subject = django_filters.ModelChoiceFilter(
        queryset=Subject.objects.all(),
        label='Дисциплина',
        empty_label='Все дисциплины',
    )
    direction = django_filters.ModelChoiceFilter(
        queryset=Direction.objects.all(),
        field_name='student__group__direction',
        label='Специальность',
        empty_label='Все специальности',
    )
    group = django_filters.ModelChoiceFilter(
        queryset=Group.objects.all(),
        field_name='student__group',
        label='Группа',
        empty_label='Все группы',
    )
    course = django_filters.NumberFilter(
        field_name='student__group__course',
        label='Курс',
    )
    control_type = django_filters.CharFilter(
        field_name='control_type',
        lookup_expr='icontains',
        label='Вид контроля',
    )
    status = django_filters.CharFilter(
        field_name='status',
        lookup_expr='icontains',
        label='Статус',
    )
    institute = django_filters.CharFilter(
        field_name='institute',
        lookup_expr='icontains',
        label='Институт',
    )
    academic_session = django_filters.CharFilter(
        field_name='academic_session',
        lookup_expr='icontains',
        label='Учебная сессия',
    )

    class Meta:
        model = AcademicDebt
        fields = []

    def filter_student_name(self, queryset, name, value):
        if value:
            parts = value.strip().split()
            qs = queryset
            for part in parts:
                qs = qs.filter(
                    db_models.Q(student__last_name__icontains=part) |
                    db_models.Q(student__first_name__icontains=part) |
                    db_models.Q(student__patronymic__icontains=part)
                )
            return qs
        return queryset
