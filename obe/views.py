from django.shortcuts import render


def home(request):
    context = {}

    if request.user.is_authenticated and request.user.is_superuser:
        context['username'] = request.user.username
        context['is_superuser'] = True
    else:
        context['username'] = request.user.username if request.user.is_authenticated else 'Guest'
        context['is_superuser'] = False

    return render(request,'home.html', context)