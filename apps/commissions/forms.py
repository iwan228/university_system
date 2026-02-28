from django import forms
from .models import CommissionSheet, CommissionEntry
from apps.students.models import AcademicDebt


class CommissionSheetForm(forms.ModelForm):
    """Форма создания/редактирования ведомости комиссии"""
    class Meta:
        model = CommissionSheet
        fields = ['subject', 'date', 'status', 'chairman', 'member_1', 'member_2', 'notes']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'chairman': forms.TextInput(attrs={'class': 'form-control'}),
            'member_1': forms.TextInput(attrs={'class': 'form-control'}),
            'member_2': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CommissionEntryForm(forms.ModelForm):
    """Форма записи студента в комиссию"""
    class Meta:
        model = CommissionEntry
        fields = ['student', 'grade', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AutoFillCommissionForm(forms.Form):
    """Автоматическое заполнение комиссии из должников по предмету"""
    subject = forms.ModelChoiceField(
        queryset=None,
        label='Предмет',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.students.models import Subject
        self.fields['subject'].queryset = Subject.objects.filter(
            debts__isnull=False
        ).distinct()
