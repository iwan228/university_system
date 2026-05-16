from django import forms
from .models import CommissionSheet, CommissionEntry
from apps.students.models import AcademicDebt


class CommissionSheetForm(forms.ModelForm):
    """Форма создания/редактирования ведомости комиссии"""
    class Meta:
        model = CommissionSheet
        fields = [
            'subject', 'date', 'status', 'order_number', 'order_date',
            'protocol_number', 'table_number',
            'chairman', 'chairman_title', 'chairman_school',
            'member_1', 'member_1_title', 'member_1_school',
            'member_2', 'member_2_title', 'member_2_school',
            'notes'
        ]
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            
            'order_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: 143-23-эк'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'protocol_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Свой номер (без этого - авто)'}),
            'table_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Свой номер (без этого - авто)'}),
            
            'chairman': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО (например: Гасумянц В.Э.)'}),
            'chairman_title': forms.Select(attrs={'class': 'form-select'}),
            'chairman_school': forms.Select(attrs={'class': 'form-select'}),
            
            'member_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО (например: Рыков С.А.)'}),
            'member_1_title': forms.Select(attrs={'class': 'form-select'}),
            'member_1_school': forms.Select(attrs={'class': 'form-select'}),
            
            'member_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО (например: Винниченко М.Я.)'}),
            'member_2_title': forms.Select(attrs={'class': 'form-select'}),
            'member_2_school': forms.Select(attrs={'class': 'form-select'}),
            
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
