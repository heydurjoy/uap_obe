from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import Faculty
from courses.models import Section


def home(request):
    context = {}
    if request.user.is_authenticated:
        if hasattr(request.user, 'faculty'):
            faculty = request.user.faculty
            # Get sections where the faculty is either primary or secondary
            sections = Section.objects.filter(
                faculties=faculty
            ).select_related('course', 'primary_faculty', 'secondary_faculty').order_by('-year', 'semester', 'name')
            
            context.update({
                'faculty': faculty,
                'sections': sections,
                'can_create_section': faculty.can_create_section(),
                'can_manage_courses': faculty.can_manage_courses(),
                'can_manage_allowed_emails': faculty.can_manage_allowed_emails(),
                'can_access_dashboard': faculty.can_access_dashboard(),
                'access_level_display': faculty.get_access_level_display(),
            })
    return render(request, 'home.html', context)


@login_required
def dashboard(request):
    context = {
        'username': request.user.username,
        'user_level': 'Superuser' if request.user.is_superuser else 'User'
    }
    return render(request, 'dashboard.html', context)