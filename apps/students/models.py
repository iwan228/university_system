from django.db import models


class Direction(models.Model):
    """Специальность / Направление подготовки"""
    code = models.CharField('Код специальности', max_length=20)
    name = models.CharField('Название', max_length=255)

    class Meta:
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'
        ordering = ['code']
        unique_together = ['code', 'name']

    def __str__(self):
        return f'{self.code} {self.name}'


class Group(models.Model):
    """Учебная группа"""
    name = models.CharField('Группа', max_length=50, unique=True)
    direction = models.ForeignKey(
        Direction, on_delete=models.CASCADE,
        related_name='groups', verbose_name='Специальность'
    )
    course = models.PositiveSmallIntegerField('Курс', default=1)

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['name']

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Дисциплина"""
    name = models.CharField('Название дисциплины', max_length=255, unique=True)

    class Meta:
        verbose_name = 'Дисциплина'
        verbose_name_plural = 'Дисциплины'
        ordering = ['name']

    def __str__(self):
        return self.name


class Student(models.Model):
    """Студент"""
    last_name = models.CharField('Фамилия', max_length=100)
    first_name = models.CharField('Имя', max_length=100)
    patronymic = models.CharField('Отчество', max_length=100, blank=True, default='')
    student_id = models.CharField('Номер зачётной книжки', max_length=30, unique=True)
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE,
        related_name='students', verbose_name='Группа'
    )
    education_level = models.CharField('Уровень образования', max_length=50,
                                       blank=True, default='')
    education_form = models.CharField('Форма обучения', max_length=50,
                                      blank=True, default='')

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name} {self.patronymic}'.strip()

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.patronymic}'.strip()


class AcademicDebt(models.Model):
    """Академическая задолженность — одна строка из ведомости должников"""

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE,
        related_name='debts', verbose_name='Студент'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE,
        related_name='debts', verbose_name='Дисциплина'
    )

    # Поля из Excel
    institute = models.CharField('Институт', max_length=100, blank=True, default='')
    academic_session = models.CharField('Учебная сессия', max_length=100, blank=True, default='')
    sheet_number = models.CharField('Ведомость', max_length=50, blank=True, default='')
    control_type = models.CharField('Вид контроля', max_length=100, blank=True, default='')
    status = models.CharField('Статус', max_length=100, blank=True, default='')
    attempt = models.PositiveSmallIntegerField('Попытка', default=1)
    attempt_date = models.DateField('Дата попытки', null=True, blank=True)
    grade = models.CharField('Оценка', max_length=100, blank=True, default='')
    teacher = models.CharField('Преподаватель', max_length=255, blank=True, default='')

    # Внутренние поля
    absence_noted = models.BooleanField('Отметка о неявке (ручная)', default=False)
    notes = models.TextField('Примечания', blank=True, default='')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Академическая задолженность'
        verbose_name_plural = 'Академические задолженности'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} — {self.subject} (попытка {self.attempt})'


class ExcelImportLog(models.Model):
    """Лог импорта из Excel"""
    file_name = models.CharField('Имя файла', max_length=255)
    imported_at = models.DateTimeField('Дата импорта', auto_now_add=True)
    rows_total = models.PositiveIntegerField('Всего строк', default=0)
    rows_imported = models.PositiveIntegerField('Импортировано', default=0)
    rows_errors = models.PositiveIntegerField('Ошибок', default=0)
    error_details = models.TextField('Детали ошибок', blank=True, default='')

    class Meta:
        verbose_name = 'Лог импорта'
        verbose_name_plural = 'Логи импорта'
        ordering = ['-imported_at']

    def __str__(self):
        return f'{self.file_name} — {self.imported_at:%d.%m.%Y %H:%M}'
