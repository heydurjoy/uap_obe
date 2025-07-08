from django.contrib import admin
from .models import (
    Course, CLO, Section, Student, Enrollment,
    AssessmentTemplate, AssessmentItem, AssessmentItemGroup, AssessmentMark, Attainment,
    ProjectGroup, Session, Attendance
)

@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    list_display = ('section', 'get_total_marks')
    list_filter = ('section__course', 'section__semester', 'section__year')
    search_fields = ('section__course__code', 'section__name')

@admin.register(AssessmentItemGroup)
class AssessmentItemGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'max_count', 'get_total_marks')
    list_filter = ('template__section__course', 'template__section__semester')
    search_fields = ('name', 'template__section__course__code')

@admin.register(AssessmentItem)
class AssessmentItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'group', 'max_marks')
    list_filter = ('template__section__course', 'template__section__semester')
    search_fields = ('name', 'template__section__course__code')

@admin.register(AssessmentMark)
class AssessmentMarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'assessment_item', 'marks')
    list_filter = ('assessment_item__template__section__course', 'assessment_item__template__section__semester')
    search_fields = ('student__student_id', 'student__name', 'assessment_item__name')

@admin.register(Attainment)
class AttainmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'clo', 'section', 'attainment_value')
    list_filter = ('clo__course', 'section__semester', 'section__year')
    search_fields = ('student__student_id', 'student__name', 'clo__code')

@admin.register(ProjectGroup)
class ProjectGroupAdmin(admin.ModelAdmin):
    list_display = ('section', 'group_sl', 'project_name')
    list_filter = ('section__course', 'section__semester', 'section__year')
    search_fields = ('project_name', 'section__course__code')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('section', 'session_number', 'date', 'is_holiday')
    list_filter = ('section__course', 'section__semester', 'section__year', 'is_holiday')
    search_fields = ('section__course__code', 'section__name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'is_present')
    list_filter = ('session__section__course', 'session__section__semester', 'is_present')
    search_fields = ('student__student_id', 'student__name', 'session__section__course__code')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'program', 'credits')
    list_filter = ('program', 'credits')
    search_fields = ('code', 'title')

@admin.register(CLO)
class CLOAdmin(admin.ModelAdmin):
    list_display = ('get_clo_code', 'course', 'sl', 'description')
    list_filter = ('course',)
    search_fields = ('description', 'course__code')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'name', 'semester', 'year', 'primary_faculty')
    list_filter = ('course', 'semester', 'year')
    search_fields = ('course__code', 'name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'program')
    list_filter = ('program',)
    search_fields = ('student_id', 'name')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'section', 'enrollment_type')
    list_filter = ('section__course', 'section__semester', 'enrollment_type')
    search_fields = ('student__student_id', 'student__name', 'section__course__code')
