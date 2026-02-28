from django.contrib import admin
from .models import Direction, Group, Subject, Student, AcademicDebt, ExcelImportLog


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'direction', 'course')
    list_filter = ('course', 'direction')
    search_fields = ('name',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'patronymic', 'student_id', 'group',
                    'education_level', 'education_form')
    list_filter = ('group__course', 'group__direction', 'group', 'education_level', 'education_form')
    search_fields = ('last_name', 'first_name', 'student_id')


@admin.register(AcademicDebt)
class AcademicDebtAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'control_type', 'status', 'attempt',
                    'attempt_date', 'grade', 'teacher', 'institute')
    list_filter = ('status', 'control_type', 'institute', 'academic_session', 'subject')
    search_fields = ('student__last_name', 'student__first_name', 'subject__name', 'teacher')


@admin.register(ExcelImportLog)
class ExcelImportLogAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'imported_at', 'rows_total', 'rows_imported', 'rows_errors')
    readonly_fields = ('file_name', 'imported_at', 'rows_total', 'rows_imported',
                       'rows_errors', 'error_details')
