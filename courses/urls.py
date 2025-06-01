from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_update, name='course_update'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    path('courses/<str:course_code>/sections/', views.section_list, name='section_list'),
    path('sections/<int:section_id>/', views.section_detail, name='section_detail'),
    path('courses/<int:course_id>/sections/create/', views.create_section, name='create_section'),
    path('courses/select-course/', views.select_course, name='select_course'),
    
    # Bulk enrollment URLs
    path('sections/<int:section_id>/enroll/', views.bulk_enroll_view, name='bulk_enroll'),
    path('sections/<int:section_id>/enroll/resolve-conflicts/', views.resolve_conflicts_view, name='resolve_conflicts'),
    
    # Section URLs
    path('sections/<int:f_id>', views.all_sections, name='all_sections'),
    path('sections/<int:section_id>/template/', views.assessment_template, name='assessment_template'),
    path('sections/<int:section_id>/marks/', views.enter_marks, name='enter_marks'),
    path('sections/<int:section_id>/analytics/', views.obe_analytics, name='obe_analytics'),
    
    # Single enrollment URL
    path('sections/<int:section_id>/single-enroll/', views.single_enroll_view, name='single_enroll'),
    
    # AJAX student search URL
    path('ajax/search-students/', views.search_students_ajax, name='search_students_ajax'),
    
    # Enrollment management URLs
    path('enrollments/<int:enrollment_id>/edit/', views.edit_enrollment_view, name='edit_enrollment'),
    path('enrollments/<int:enrollment_id>/delete/', views.delete_enrollment_view, name='delete_enrollment'),
    
    # Project group management URL
    path('sections/<int:section_id>/project-groups/', views.manage_project_groups_view, name='manage_project_groups'),
    
    # Section editing URL
    path('sections/<int:section_id>/edit/', views.edit_section_view, name='edit_section'),
    
    # CLO management URLs
    path('sections/<int:section_id>/clos/', views.manage_clos_view, name='manage_clos'),
    path('sections/<int:section_id>/clos/<int:clo_id>/edit/', views.edit_clo_view, name='edit_clo'),
    path('sections/<int:section_id>/clos/<int:clo_id>/delete/', views.delete_clo_view, name='delete_clo'),
    
    # Student attainment URLs
    path('students/<str:student_id>/attainment/', views.student_attainment_history, name='student_attainment'),
    
    # Add this line to the urlpatterns list
    path('sections/<int:section_id>/add-session-dates/', views.add_session_dates_view, name='add_session_dates'),
    
    # New URL pattern for deleting all sessions
    path('sections/<int:section_id>/delete-all-sessions/', views.delete_all_sessions_view, name='delete_all_sessions'),
    path('sessions/<int:session_id>/update-date/', views.update_session_date_view, name='update_session_date'),
    path('sections/<int:section_id>/update-total-classes/', views.update_section_total_classes_view, name='update_section_total_classes'),
    
    # Add this line for deleting all attendance
    path('sections/<int:section_id>/delete-all-attendance/', views.delete_all_attendance_view, name='delete_all_attendance'),
    
    # Add this line for exporting attendance to Excel
    path('sections/<int:section_id>/export-excel/', views.export_attendance_excel_view, name='export_attendance_excel'),
    
    # Attendance URLs
    path('sections/<int:section_id>/attendance/', views.get_attendance, name='get_attendance'),
    path('sections/<int:section_id>/attendance/save/', views.save_attendance, name='save_attendance'),
] 