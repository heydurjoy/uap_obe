from django import forms
from .models import Course, Section, Faculty, Student, Enrollment
from django.utils import timezone
from accounts.models import Faculty

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'title', 'program', 'credits', 'description', 'is_lab']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'program': forms.Select(attrs={'class': 'form-control'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_lab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Get current year
        current_year = timezone.now().year
        
        # Create year choices (3 years back to 3 years ahead)
        year_choices = [(year, str(year)) for year in range(current_year - 3, current_year + 4)]
        
        # Update year field choices
        self.fields['year'] = forms.ChoiceField(
            choices=year_choices,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # Update semester choices
        self.fields['semester'] = forms.ChoiceField(
            choices=Section.SEMESTER_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # Get all faculties for the dropdowns
        faculties = Faculty.objects.all().order_by('name')
        self.fields['primary_faculty'].queryset = faculties
        self.fields['secondary_faculty'].queryset = faculties
        
        # If editing, don't modify the primary faculty
        if not self.instance.pk:
            # Set the logged-in faculty as primary faculty
            if self.user and hasattr(self.user, 'faculty'):
                self.initial['primary_faculty'] = self.user.faculty
    
    class Meta:
        model = Section
        fields = ['name', 'year', 'semester', 'primary_faculty', 'secondary_faculty']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter section name (e.g., A, B, C)'
            }),
            'primary_faculty': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select primary faculty'
            }),
            'secondary_faculty': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select secondary faculty (optional)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        primary_faculty = cleaned_data.get('primary_faculty')
        secondary_faculty = cleaned_data.get('secondary_faculty')
        
        # Ensure primary and secondary faculty are different
        if primary_faculty and secondary_faculty and primary_faculty == secondary_faculty:
            raise forms.ValidationError("Primary and secondary faculty cannot be the same person.")
        
        return cleaned_data

    def save(self, commit=True):
        section = super().save(commit=False)
        if commit:
            section.save()
            # Add faculties to the section
            section.faculties.add(self.cleaned_data['primary_faculty'])
            if self.cleaned_data['secondary_faculty']:
                section.faculties.add(self.cleaned_data['secondary_faculty'])
        return section

class BulkEnrollForm(forms.Form):
    student_ids = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste student IDs here (one per line)'
        })
    )
    student_names = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste student names here (one per line)'
        })
    )

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['enrollment_type']
        widgets = {
            'enrollment_type': forms.Select(attrs={'class': 'form-select'})
        } 