from django.shortcuts import render


def home(request):
    context = {}

    if request.user.is_authenticated and request.user.is_superuser:
        context['username'] = request.user.username
        context['user_level'] = 'Superuser'
    else:
        context['username'] = request.user.username if request.user.is_authenticated else 'Guest'
        context['user_level'] = 'not logged in'

    return render(request,'home.html', context)