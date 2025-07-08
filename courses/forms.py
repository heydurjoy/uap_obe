from django import forms
from .models import Course, Section, Faculty, Student, Enrollment, CLO
from programs.models import PLO
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
    student_id = forms.CharField(label='Student ID', required=True)
    student_name = forms.CharField(label='Student Name', required=True)

    class Meta:
        model = Enrollment
        fields = ['student_id', 'student_name', 'enrollment_type']
        widgets = {
            'enrollment_type': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.student:
            self.fields['student_id'].initial = self.instance.student.student_id
            self.fields['student_name'].initial = self.instance.student.name

    def clean_student_id(self):
        new_id = self.cleaned_data['student_id']
        # Exclude the current student from the uniqueness check
        qs = self.instance.student.__class__.objects.filter(student_id=new_id)
        if self.instance and self.instance.student:
            qs = qs.exclude(pk=self.instance.student.pk)
        if qs.exists():
            raise forms.ValidationError('A student with this ID already exists.')
        return new_id

    def save(self, commit=True):
        enrollment = super().save(commit=False)
        # Update student info if changed
        student = enrollment.student
        new_id = self.cleaned_data.get('student_id')
        new_name = self.cleaned_data.get('student_name')
        if student:
            if new_id and student.student_id != new_id:
                student.student_id = new_id
            if new_name and student.name != new_name:
                student.name = new_name
            if commit:
                student.save()
        if commit:
            enrollment.save()
        return enrollment

class CLOForm(forms.ModelForm):
    class Meta:
        model = CLO
        fields = ['sl', 'plo', 'description']
        widgets = {
            'sl': forms.NumberInput(attrs={'class': 'form-control'}),
            'plo': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-select'

    def clean_sl(self):
        sl = self.cleaned_data.get('sl')
        if self.course:
            # Check if a CLO with this serial number already exists for this course
            existing_clo = CLO.objects.filter(course=self.course, sl=sl)
            if self.instance.pk:  # If editing existing CLO
                existing_clo = existing_clo.exclude(pk=self.instance.pk)
            if existing_clo.exists():
                raise forms.ValidationError(f'CLO with serial number {sl} already exists for this course.')
        return sl 