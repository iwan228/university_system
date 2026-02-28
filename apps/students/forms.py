from django import forms
from .models import AcademicDebt


class ExcelImportForm(forms.Form):
    """Форма загрузки Excel-файла"""
    file = forms.FileField(
        label='Файл Excel (.xls / .xlsx)',
        help_text='Загрузите файл с данными о должниках',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls,.csv',
            'class': 'form-control',
        })
    )


class AcademicDebtForm(forms.ModelForm):
    """Форма редактирования задолженности"""
    class Meta:
        model = AcademicDebt
        fields = [
            'student', 'subject', 'institute', 'academic_session',
            'sheet_number', 'control_type', 'status', 'attempt',
            'attempt_date', 'grade', 'teacher', 'absence_noted', 'notes',
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'institute': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_session': forms.TextInput(attrs={'class': 'form-control'}),
            'sheet_number': forms.TextInput(attrs={'class': 'form-control'}),
            'control_type': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.TextInput(attrs={'class': 'form-control'}),
            'attempt': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'attempt_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'teacher': forms.TextInput(attrs={'class': 'form-control'}),
            'absence_noted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
