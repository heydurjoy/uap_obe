from django import forms
from .models import Program, AllowedEmail, Department

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'department', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'short_name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AllowedEmailForm(forms.ModelForm):
    class Meta:
        model = AllowedEmail
        fields = ['email', 'department']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        } 