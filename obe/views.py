from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    context = {}

    if request.user.is_authenticated and request.user.is_superuser:
        context['username'] = request.user.username
        context['user_level'] = 'Superuser'
    else:
        context['username'] = request.user.username if request.user.is_authenticated else 'Guest'
        context['user_level'] = 'not logged in'

    return render(request,'home.html', context)


@login_required
def dashboard(request):
    context = {
        'username': request.user.username,
        'user_level': 'Superuser' if request.user.is_superuser else 'User'
    }
    return render(request, 'dashboard.html', context)