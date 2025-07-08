from django.db import models
from django.contrib.auth.models import User
from programs.models import Program, PLO
from accounts.models import Faculty
from django.core.exceptions import ValidationError

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='courses')
    credits = models.PositiveIntegerField()
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
        return f"CLO{self.sl}"

class Section(models.Model):
    SEMESTER_CHOICES = [
        ('Spring', 'Spring'),
        ('Fall', 'Fall')
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=10)  # e.g., A, B, C
    year = models.IntegerField()
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    primary_faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='primary_sections')
    secondary_faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='secondary_sections')
    faculties = models.ManyToManyField(Faculty, related_name='sections')
    total_classes = models.PositiveIntegerField(default=28, help_text="Total number of classes for attendance calculation")
    
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
    section = models.OneToOneField(Section, on_delete=models.CASCADE, related_name='assessment_template')
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Assessment Template - {self.section.course.code} Section {self.section.name}"

    def get_total_marks(self):
        """Calculate total marks from all assessment items"""
        total = 0
        # Add marks from individual items
        total += self.assessment_items.filter(group__isnull=True).aggregate(
            total=models.Sum('max_marks'))['total'] or 0
        
        # Add marks from groups
        for group in self.assessment_groups.all():
            total += group.get_total_marks()
        
        return total

class AssessmentItemGroup(models.Model):
    MAX_COUNT_CHOICES = [
        (1, 'Top 1'),
        (2, 'Top 2'),
        (3, 'Top 3'),
        (4, 'Top 4'),
        (5, 'Top 5'),
        (6, 'Top 6'),
        (7, 'Top 7'),
        (8, 'Top 8'),
        (9, 'Top 9'),
        (10, 'Top 10'),
    ]
    
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE, related_name='assessment_groups')
    name = models.CharField(max_length=100)
    max_count = models.IntegerField(choices=MAX_COUNT_CHOICES, default=1)
    clo = models.ForeignKey(CLO, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    item1 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item1')
    item2 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item2')
    item3 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item3')
    item4 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item4')
    item5 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item5')
    item6 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item6')
    item7 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item7')
    item8 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item8')
    item9 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item9')
    item10 = models.ForeignKey('AssessmentItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='group_item10')
    totalmarks = models.FloatField(default=0)

    def clean(self):
        if self.pk and self.assessment_items.count() > 10:
            raise ValidationError('A group can contain at most 10 items.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.template.section.course.code} Section {self.template.section.name}"

    def get_total_marks(self):
        """Calculate total marks for the group based on max_count"""
        items = self.assessment_items.all().order_by('-max_marks')
        total = 0
        for i in range(min(self.max_count, len(items))):
            total += items[i].max_marks
        return total

class AssessmentItem(models.Model):
    ASSESSMENT_TYPES = [
        ('Assessment', 'Assessment'),
        ('Midterm', 'Midterm'),
        ('Final', 'Final'),
    ]
    
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE, related_name='assessment_items')
    group = models.ForeignKey(AssessmentItemGroup, on_delete=models.CASCADE, null=True, blank=True, related_name='assessment_items')
    name = models.CharField(max_length=100)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    clo = models.ForeignKey(CLO, on_delete=models.CASCADE)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    in_group = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.template.section.course.code} Section {self.template.section.name}"

    def save(self, *args, **kwargs):
        # Ensure CLO matches group CLO if item is in a group
        if self.group and self.clo != self.group.clo:
            self.clo = self.group.clo
        super().save(*args, **kwargs)

class AssessmentMark(models.Model):
    assessment_item = models.ForeignKey(AssessmentItem, on_delete=models.CASCADE, related_name='marks')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assessment_marks')
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['assessment_item', 'student']

    def __str__(self):
        return f"{self.student.name} - {self.assessment_item.name}"

    def save(self, *args, **kwargs):
        # Validate marks are within range
        if self.marks is not None:
            if self.marks < 0 or self.marks > self.assessment_item.max_marks:
                raise ValidationError(f'Marks must be between 0 and {self.assessment_item.max_marks}')
        super().save(*args, **kwargs)

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

# New model for attendance sessions
class Session(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='sessions')
    session_number = models.IntegerField()
    date = models.DateField()
    is_holiday = models.BooleanField(default=False)

    class Meta:
        ordering = ['session_number']

    def __str__(self):
        return f"{self.section.course.code} - Session {self.session_number} ({self.date})"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'session']
        ordering = ['session__session_number']

    def __str__(self):
        return f"{self.student.name} - Session {self.session.session_number} ({'Present' if self.is_present else 'Absent'})"
