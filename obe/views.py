from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Faculty
from courses.models import Section
from django.contrib import messages


@login_required
def home(request):
    # Initialize variables
    faculty = None
    sections = []
    can_create_section = False
    can_manage_courses = False
    can_manage_allowed_emails = False
    can_access_dashboard = False
    
    # Get faculty object if user is not superuser
    if not request.user.is_superuser:
        try:
            faculty = Faculty.objects.get(user=request.user)
            sections = Section.objects.filter(faculties=faculty)
            can_create_section = faculty.can_create_section
            can_manage_courses = faculty.can_manage_courses
            can_manage_allowed_emails = faculty.can_manage_allowed_emails
            can_access_dashboard = faculty.can_access_dashboard
        except Faculty.DoesNotExist:
            messages.warning(request, 'Faculty profile not found. Please contact administrator.')
            return redirect('accounts:profile')
    else:
        # Superuser has all access
        can_create_section = True
        can_manage_courses = True
        can_manage_allowed_emails = True
        can_access_dashboard = True
        sections = Section.objects.all()  # Get all sections for superuser
    
    context = {
        'faculty': faculty,
        'sections': sections,
        'can_create_section': can_create_section,
        'can_manage_courses': can_manage_courses,
        'can_manage_allowed_emails': can_manage_allowed_emails,
        'can_access_dashboard': can_access_dashboard,
    }
    
    return render(request, 'home.html', context)


@login_required
def dashboard(request):
    context = {
        'username': request.user.username,
        'user_level': 'Superuser' if request.user.is_superuser else 'User'
    }
    return render(request, 'dashboard.html', context)
