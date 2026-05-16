from django.db import models
from apps.students.models import Student, Subject, AcademicDebt


class CommissionSheet(models.Model):
    """Ведомость комиссии"""
    STATUS_CHOICES = [
        ('open', 'Открыта'),
        ('closed', 'Закрыта'),
    ]

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE,
        related_name='commission_sheets', verbose_name='Предмет'
    )
    date = models.DateField('Дата проведения')
    status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='open')
    
    ACADEMIC_TITLE_CHOICES = [
        ('', '---------'),
        ('Доцент', 'Доцент'),
        ('Профессор', 'Профессор'),
    ]
    HIGH_SCHOOL_CHOICES = [
        ('', '---------'),
        ('ВИФШ', 'ВИФШ'),
        ('ВШПФиКТ', 'ВШПФиКТ'),
        ('ВШЭиМТ', 'ВШЭиМТ'),
    ]

    order_number = models.CharField('Номер распоряжения', max_length=50, blank=True, null=True)
    order_date = models.DateField('Дата создания распоряжения', blank=True, null=True)
    
    protocol_number = models.CharField('Номер протокола', max_length=50, blank=True, null=True)
    table_number = models.CharField('Номер ведомости', max_length=50, blank=True, null=True)


    chairman = models.CharField('Председатель комиссии', max_length=255, blank=True, default='')
    chairman_title = models.CharField('Звание председателя', max_length=50, choices=ACADEMIC_TITLE_CHOICES, blank=True, default='')
    chairman_school = models.CharField('Высшая школа председателя', max_length=50, choices=HIGH_SCHOOL_CHOICES, blank=True, default='')
    
    member_1 = models.CharField('Член комиссии 1', max_length=255, blank=True, default='')
    member_1_title = models.CharField('Звание члена 1', max_length=50, choices=ACADEMIC_TITLE_CHOICES, blank=True, default='')
    member_1_school = models.CharField('Высшая школа члена 1', max_length=50, choices=HIGH_SCHOOL_CHOICES, blank=True, default='')
    
    member_2 = models.CharField('Член комиссии 2', max_length=255, blank=True, default='')
    member_2_title = models.CharField('Звание члена 2', max_length=50, choices=ACADEMIC_TITLE_CHOICES, blank=True, default='')
    member_2_school = models.CharField('Высшая школа члена 2', max_length=50, choices=HIGH_SCHOOL_CHOICES, blank=True, default='')
    
    notes = models.TextField('Примечания', blank=True, default='')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Ведомость комиссии'
        verbose_name_plural = 'Ведомости комиссий'
        ordering = ['-date']

    def __str__(self):
        return f'{self.subject} — {self.date:%d.%m.%Y}'

    @property
    def is_open(self):
        return self.status == 'open'


class CommissionEntry(models.Model):
    """Запись студента в комиссию"""
    GRADE_CHOICES = [
        ('', 'Не выставлена'),
        ('2', 'Неудовлетворительно'),
        ('3', 'Удовлетворительно'),
        ('4', 'Хорошо'),
        ('5', 'Отлично'),
        ('pass', 'Зачтено'),
        ('fail', 'Не зачтено'),
        ('absent', 'Неявка'),
    ]

    sheet = models.ForeignKey(
        CommissionSheet, on_delete=models.CASCADE,
        related_name='entries', verbose_name='Ведомость'
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE,
        related_name='commission_entries', verbose_name='Студент'
    )
    debt = models.ForeignKey(
        AcademicDebt, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='commission_entries', verbose_name='Задолженность'
    )
    grade = models.CharField('Оценка', max_length=10, choices=GRADE_CHOICES, blank=True, default='')
    notes = models.TextField('Примечания', blank=True, default='')

    class Meta:
        verbose_name = 'Запись в комиссии'
        verbose_name_plural = 'Записи в комиссиях'
        unique_together = ['sheet', 'student']

    def __str__(self):
        return f'{self.student} — {self.sheet}'
