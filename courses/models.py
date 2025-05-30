from django.db import models
from django.contrib.auth.models import User
from programs.models import Program, PLO
from accounts.models import Faculty
from django.core.exceptions import ValidationError

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    credits = models.DecimalField(max_digits=3, decimal_places=1)
    description = models.TextField(blank=True, null=True)
    is_lab = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.code} - {self.title}"

class CLO(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='clos')
    sl = models.PositiveIntegerField(verbose_name="Serial Number")
    plo = models.ForeignKey(PLO, on_delete=models.SET_NULL, null=True, related_name='clos')
    description = models.CharField(max_length=500)

    class Meta:
        unique_together = ['course', 'sl']
        ordering = ['sl']

    def __str__(self):
        plo_str = f" (Mapped to {self.plo})" if self.plo else ""
        return f"{self.course.code} CLO {self.sl}{plo_str}"

    def get_clo_code(self):
        return f"{self.course.code}-CLO{self.sl}"

class Section(models.Model):
    SEMESTER_CHOICES = [
        ('Spring', 'Spring'),
        ('Summer', 'Summer'),
        ('Fall', 'Fall')
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=10)  # e.g., A, B, C
    year = models.IntegerField()
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    primary_faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='primary_sections')
    secondary_faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='secondary_sections')
    faculties = models.ManyToManyField(Faculty, related_name='sections')
    
    class Meta:
        unique_together = ['course', 'name', 'year', 'semester']
        ordering = ['-year', 'semester', 'name']
    
    def __str__(self):
        return f"{self.course.code} - {self.name} ({self.semester} {self.year})"
    
    def save(self, *args, **kwargs):
        # Ensure primary faculty is in the faculties M2M field
        super().save(*args, **kwargs)
        if self.primary_faculty and self.primary_faculty not in self.faculties.all():
            self.faculties.add(self.primary_faculty)
        if self.secondary_faculty and self.secondary_faculty not in self.faculties.all():
            self.faculties.add(self.secondary_faculty)

class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    sections = models.ManyToManyField(Section, through='Enrollment')
    
    def __str__(self):
        return f"{self.student_id} - {self.name}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)

    ENROLLMENT_CHOICES = [
        ('Regular', 'Regular'),
        ('Backlog', 'Backlog'),
        ('Self-Study', 'Self-Study'),
        # Add more choices here as needed
    ]

    enrollment_type = models.CharField(
        max_length=50, 
        choices=ENROLLMENT_CHOICES, 
        default='Regular'
    )

    class Meta:
        unique_together = ('student', 'section')

    def __str__(self):
        return f'{self.student.name} in {self.section.course.code} Section {self.section.name}'

class AssessmentTemplate(models.Model):
    section = models.OneToOneField(Section, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Template for {self.section}"

class AssessmentComponent(models.Model):
    COMPONENT_TYPE_CHOICES = [
        ('THEORY', 'Theory'),
        ('LAB', 'Lab'),
    ]
    
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE, related_name='components')
    name = models.CharField(max_length=50)
    component_type = models.CharField(max_length=10, choices=COMPONENT_TYPE_CHOICES)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    clo = models.ForeignKey(CLO, on_delete=models.CASCADE)
    alternative_group = models.CharField(max_length=50, blank=True, null=True)
    best_of_count = models.IntegerField(default=1)  # Number of best marks to consider
    is_visible_to_students = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['template', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"

class AssessmentMark(models.Model):
    component = models.ForeignKey(AssessmentComponent, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    mark = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['component', 'student']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.component.name}: {self.mark}"

class Attainment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    clo = models.ForeignKey(CLO, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    attainment_value = models.DecimalField(max_digits=5, decimal_places=2)
    semester = models.CharField(max_length=20)
    year = models.IntegerField()
    
    class Meta:
        unique_together = ['student', 'clo', 'section']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.clo.code}: {self.attainment_value}"

# New models for project groups
class ProjectGroup(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='project_groups')
    group_sl = models.IntegerField() # Group Serial Number
    project_name = models.CharField(max_length=255, blank=True, null=True)
    students = models.ManyToManyField(Student, related_name='project_groups')

    class Meta:
        unique_together = ['section', 'group_sl']
        ordering = ['section', 'group_sl']

    def __str__(self):
        return f'Group {self.group_sl} ({self.section.name})'

class ProjectGroupEnrollment(models.Model):
    project_group = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['project_group', 'student']

    def __str__(self):
        return f'{self.student.name} in {self.project_group}'
