from django import forms
from .models import Course, Section, Faculty

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
    faculty1 = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        label='Primary Faculty',
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    faculty2 = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        label='Secondary Faculty (Optional)',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Section
        fields = ['section_number', 'semester', 'year']
        widgets = {
            'section_number': forms.TextInput(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('Spring', 'Spring'),
                ('Summer', 'Summer'),
                ('Fall', 'Fall')
            ]),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all faculties
        self.fields['faculty1'].queryset = Faculty.objects.all()
        self.fields['faculty2'].queryset = Faculty.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        faculty1 = cleaned_data.get('faculty1')
        faculty2 = cleaned_data.get('faculty2')

        if faculty1 and faculty2 and faculty1 == faculty2:
            raise forms.ValidationError("Primary and Secondary faculty cannot be the same person.")

        return cleaned_data

    def save(self, commit=True):
        section = super().save(commit=False)
        if commit:
            section.save()
            # Add faculties to the section
            section.faculties.add(self.cleaned_data['faculty1'])
            if self.cleaned_data['faculty2']:
                section.faculties.add(self.cleaned_data['faculty2'])
        return section 