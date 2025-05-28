from django.contrib import admin
from .models import (
    Course, CLO, Section, Student, Enrollment,
    AssessmentTemplate, AssessmentComponent, AssessmentMark, Attainment
)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'program', 'credits', 'is_lab')
    list_filter = ('program', 'is_lab')
    search_fields = ('code', 'title', 'program__name')

@admin.register(CLO)
class CLOAdmin(admin.ModelAdmin):
    list_display = ('code', 'course', 'description')
    list_filter = ('course',)
    search_fields = ('code', 'description', 'course__code')
    filter_horizontal = ('plos',)

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'section_number', 'semester', 'year', 'is_active', 'created_at')
    list_filter = ('course', 'semester', 'year', 'is_active')
    search_fields = ('course__code', 'section_number')
    filter_horizontal = ('faculties',)

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

@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    list_display = ('section', 'is_public', 'created_at')
    list_filter = ('is_public', 'section__course')
    search_fields = ('section__course__code', 'section__section_number')

@admin.register(AssessmentComponent)
class AssessmentComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'component_type', 'weight', 'clo', 'is_visible_to_students')
    list_filter = ('component_type', 'is_visible_to_students', 'template__section__course')
    search_fields = ('name', 'template__section__course__code')

@admin.register(AssessmentMark)
class AssessmentMarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'component', 'mark', 'updated_at')
    list_filter = ('component__template__section__course', 'component__component_type')
    search_fields = ('student__student_id', 'student__name', 'component__name')

@admin.register(Attainment)
class AttainmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'clo', 'section', 'attainment_value', 'semester', 'year')
    list_filter = ('semester', 'year', 'section__course')
    search_fields = ('student__student_id', 'student__name', 'clo__code')
