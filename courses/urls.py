from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    path('<int:pk>/update/', views.course_update, name='course_update'),
    path('<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # Section URLs
    path('sections/', views.all_sections, name='all_sections'),
    path('sections/create/<int:course_id>/', views.create_section, name='create_section'),
    path('sections/<int:section_id>/', views.section_detail, name='section_detail'),
    path('sections/<int:section_id>/enroll/', views.bulk_enroll_students, name='bulk_enroll'),
    path('sections/<int:section_id>/template/', views.assessment_template, name='assessment_template'),
    path('sections/<int:section_id>/marks/', views.enter_marks, name='enter_marks'),
    path('sections/<int:section_id>/analytics/', views.obe_analytics, name='obe_analytics'),
    
    # Course-specific section URLs
    path('<str:course_code>/sections/', views.section_list, name='section_list'),
    
    # Student attainment URLs
    path('students/<str:student_id>/attainment/', views.student_attainment_history, name='student_attainment'),
    
    # Course selection URL
    path('select-course/', views.select_course, name='select_course'),
] 