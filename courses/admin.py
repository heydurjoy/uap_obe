from django.contrib import admin
from .models import (
    Course, Section, Student, Enrollment, CLO, AssessmentTemplate, AssessmentComponent, AssessmentMark, Attainment,
    ProjectGroup, ProjectGroupEnrollment, Session, Attendance
)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'program', 'credits', 'is_lab')
    search_fields = ('code', 'title')
    list_filter = ('program', 'is_lab')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'name', 'year', 'semester', 'primary_faculty', 'secondary_faculty')
    list_filter = ('course', 'year', 'semester')
    search_fields = ('course__code', 'name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'program')
    search_fields = ('student_id', 'name')
    list_filter = ('program',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'section', 'enrollment_type', 'enrollment_date')
    list_filter = ('enrollment_type', 'section__course', 'section__semester', 'section__year')
    search_fields = ('student__student_id', 'student__name', 'section__course__code')

@admin.register(CLO)
class CLOAdmin(admin.ModelAdmin):
    list_display = ('get_clo_code', 'course', 'sl', 'plo', 'description')
    list_filter = ('course', 'plo')
    search_fields = ('course__code', 'description')
    ordering = ('course', 'sl')

@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    list_display = ('section', 'is_public', 'created_at')
    list_filter = ('is_public', 'section__course', 'section__semester', 'section__year')

@admin.register(AssessmentComponent)
class AssessmentComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'component_type', 'weight', 'clo', 'is_visible_to_students')
    list_filter = ('component_type', 'template__section__course', 'is_visible_to_students')
    search_fields = ('name', 'template__section__course__code')

@admin.register(AssessmentMark)
class AssessmentMarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'component', 'mark', 'created_at', 'updated_at')
    list_filter = ('component__template__section__course', 'component__component_type')
    search_fields = ('student__student_id', 'student__name', 'component__name')

@admin.register(Attainment)
class AttainmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'clo', 'section', 'attainment_value', 'semester', 'year')
    list_filter = ('section__course', 'semester', 'year')
    search_fields = ('student__student_id', 'student__name', 'clo__course__code')

@admin.register(ProjectGroup)
class ProjectGroupAdmin(admin.ModelAdmin):
    list_display = ('section', 'group_sl', 'project_name')
    list_filter = ('section__course', 'section__semester', 'section__year')
    search_fields = ('project_name', 'section__course__code')

@admin.register(ProjectGroupEnrollment)
class ProjectGroupEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('project_group', 'student')
    list_filter = ('project_group__section__course', 'project_group__section__semester', 'project_group__section__year')
    search_fields = ('student__student_id', 'student__name', 'project_group__project_name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'is_present', 'created_at', 'updated_at')
    list_filter = ('is_present', 'session__section__course', 'session__section__semester', 'session__section__year')
    search_fields = ('student__student_id', 'student__name', 'session__section__course__code')
    ordering = ('-session__date', 'student__student_id')

admin.site.register(Session)
