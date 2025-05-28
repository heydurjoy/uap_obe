from django.urls import path
from . import views

app_name = 'programs'

urlpatterns = [
    path('', views.program_list, name='program_list'),
    path('create/', views.program_create, name='program_create'),
    path('<int:pk>/', views.program_detail, name='program_detail'),
    path('<int:pk>/edit/', views.program_edit, name='program_edit'),
    path('<int:pk>/delete/', views.program_delete, name='program_delete'),
    path('allowed-emails/', views.allowed_email_list, name='allowed_email_list'),
    path('allowed-emails/create/', views.allowed_email_create, name='allowed_email_create'),
    path('allowed-emails/<int:pk>/delete/', views.allowed_email_delete, name='allowed_email_delete'),
] 