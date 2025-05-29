from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, FacultyProfileForm, UserProfileForm, CustomAuthenticationForm
from .models import Faculty
from programs.models import AllowedEmail
from functools import wraps

def faculty_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'faculty'):
            messages.error(request, 'You must be a faculty member to access this page.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def require_access_level(level_func):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            faculty = get_object_or_404(Faculty, user=request.user)
            if not getattr(faculty, level_func)():
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # This will create both user and faculty profile
            login(request, user)
            messages.success(request, 'Registration successful! Please complete your profile.')
            return redirect('accounts:profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('home')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
@faculty_required
@require_access_level('can_access_dashboard')
def dashboard(request):
    faculty = get_object_or_404(Faculty, user=request.user)
    context = {
        'faculty': faculty,
        'courses': faculty.section_set.all().distinct('course'),
        'sections': faculty.section_set.all(),
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
@faculty_required
def profile(request):
    faculty = get_object_or_404(Faculty, user=request.user)
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user)
        faculty_form = FacultyProfileForm(request.POST, instance=faculty)
        if user_form.is_valid() and faculty_form.is_valid():
            user_form.save()
            faculty_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        faculty_form = FacultyProfileForm(instance=faculty)
    
    context = {
        'user_form': user_form,
        'faculty_form': faculty_form,
        'faculty': faculty,
    }
    return render(request, 'accounts/profile.html', context)
