from django.contrib import admin
from .models import (
    Course, CLO, Section, Student, Enrollment,
    AssessmentTemplate, AssessmentComponent, AssessmentMark, Attainment
)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'program', 'credits', 'is_lab')
    list_filter = ('program', 'is_lab')
    search_fields = ('code', 'title')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'name', 'semester', 'year', 'primary_faculty', 'secondary_faculty')
    list_filter = ('course', 'semester', 'year', 'primary_faculty', 'secondary_faculty')
    search_fields = ('course__code', 'name', 'primary_faculty__name', 'secondary_faculty__name')
    raw_id_fields = ('course', 'primary_faculty', 'secondary_faculty')

@admin.register(CLO)
class CLOAdmin(admin.ModelAdmin):
    list_display = ('code', 'course', 'description')
    list_filter = ('course',)
    search_fields = ('code', 'description', 'course__code')
    filter_horizontal = ('plos',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'program')
    list_filter = ('program',)
    search_fields = ('student_id', 'name')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'section', 'enrollment_date')
    list_filter = ('section__course', 'section__semester', 'section__year')
    search_fields = ('student__student_id', 'student__name', 'section__course__code')
    raw_id_fields = ('student', 'section')

@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    list_display = ('section', 'is_public', 'created_at')
    list_filter = ('is_public', 'section__course', 'section__semester', 'section__year')
    search_fields = ('section__course__code', 'section__name')
    raw_id_fields = ('section',)

@admin.register(AssessmentComponent)
class AssessmentComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'component_type', 'weight', 'clo', 'is_visible_to_students')
    list_filter = ('component_type', 'is_visible_to_students', 'template__section__course')
    search_fields = ('name', 'template__section__course__code', 'clo__code')
    raw_id_fields = ('template', 'clo')

@admin.register(AssessmentMark)
class AssessmentMarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'component', 'mark', 'updated_at')
    list_filter = ('component__template__section__course', 'component__component_type')
    search_fields = ('student__student_id', 'student__name', 'component__name')
    raw_id_fields = ('student', 'component')

@admin.register(Attainment)
class AttainmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'clo', 'section', 'attainment_value', 'semester', 'year')
    list_filter = ('section__course', 'semester', 'year')
    search_fields = ('student__student_id', 'student__name', 'clo__code', 'section__course__code')
    raw_id_fields = ('student', 'clo', 'section')
