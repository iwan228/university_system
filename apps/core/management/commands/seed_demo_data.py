"""
Команда для создания тестовых данных для демонстрации системы.
Usage: python manage.py seed_demo_data
"""

from datetime import date
from django.core.management.base import BaseCommand
from apps.students.models import Direction, Group, Subject, Student, AcademicDebt


class Command(BaseCommand):
    help = 'Создать демо-данные для проверки системы'

    def handle(self, *args, **options):
        # Направления
        d1, _ = Direction.objects.get_or_create(code='09.03.01', defaults={'name': 'Информатика и вычислительная техника'})
        d2, _ = Direction.objects.get_or_create(code='11.03.04', defaults={'name': 'Электроника и наноэлектроника'})
        d3, _ = Direction.objects.get_or_create(code='38.03.01', defaults={'name': 'Экономика'})

        # Группы
        g1, _ = Group.objects.get_or_create(name='4931104/30301', defaults={'direction': d2, 'course': 3})
        g2, _ = Group.objects.get_or_create(name='4931102/20601', defaults={'direction': d1, 'course': 4})
        g3, _ = Group.objects.get_or_create(name='3831001/10101', defaults={'direction': d3, 'course': 2})

        # Предметы
        s1, _ = Subject.objects.get_or_create(name='Автоматизация физического эксперимента')
        s2, _ = Subject.objects.get_or_create(name='Алгоритмы обработки сигналов')
        s3, _ = Subject.objects.get_or_create(name='Математический анализ')
        s4, _ = Subject.objects.get_or_create(name='Базы данных')

        # Студенты
        students_data = [
            ('Иванов', 'Алексей', 'Петрович', '20210001', g1, 'Бакалавр', 'Очное'),
            ('Петрова', 'Мария', 'Сергеевна', '20210002', g1, 'Бакалавр', 'Очное'),
            ('Сидоров', 'Дмитрий', 'Александрович', '20210003', g2, 'Бакалавр', 'Очное'),
            ('Козлова', 'Анна', 'Владимировна', '20210004', g2, 'Бакалавр', 'Очное'),
            ('Морозов', 'Иван', 'Дмитриевич', '20220001', g3, 'Бакалавр', 'Очное'),
        ]

        students = []
        for ln, fn, pt, sid, grp, lvl, form in students_data:
            st, _ = Student.objects.get_or_create(
                student_id=sid,
                defaults={
                    'last_name': ln, 'first_name': fn, 'patronymic': pt,
                    'group': grp, 'education_level': lvl, 'education_form': form,
                }
            )
            students.append(st)

        # Задолженности
        debts_data = [
            (students[0], s1, 'ИЭиТ', 'Осень 2025-2026', '49/437268', 'экзамен', 'восстановлен', 1, date(2025, 12, 24), 'не явился', 'Румянцев И.А.'),
            (students[0], s1, 'ИЭиТ', 'Осень 2025-2026', '49/437268', 'экзамен', 'восстановлен', 2, date(2026, 2, 14), 'не явился', 'Румянцев И.А.'),
            (students[1], s2, 'ИЭиТ', 'Осень 2025-2026', '49/437396', 'экзамен', 'продленная сессия', 1, date(2025, 12, 29), 'неудовлетворительно', 'Орлова А.С.'),
            (students[2], s3, 'ИЭиТ', 'Осень 2025-2026', '49/100001', 'экзамен', 'продленная сессия', 1, date(2025, 12, 20), 'неудовлетворительно', 'Кузнецов В.И.'),
            (students[3], s4, 'ИЭиТ', 'Осень 2025-2026', '49/100002', 'зачёт', 'продленная сессия', 1, date(2025, 12, 22), 'не зачтено', 'Павлов С.А.'),
            (students[4], s3, 'ИЭиТ', 'Осень 2025-2026', '49/100003', 'экзамен', '', 1, date(2025, 12, 18), 'не явился', 'Кузнецов В.И.'),
        ]

        created = 0
        for student, subject, inst, sess, sheet, ctrl, status, att, att_date, grade, teacher in debts_data:
            _, was_created = AcademicDebt.objects.get_or_create(
                student=student,
                subject=subject,
                attempt=att,
                defaults={
                    'institute': inst,
                    'academic_session': sess,
                    'sheet_number': sheet,
                    'control_type': ctrl,
                    'status': status,
                    'attempt_date': att_date,
                    'grade': grade,
                    'teacher': teacher,
                }
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Демо-данные созданы: {len(students_data)} студентов, {created} задолженностей'
        ))
