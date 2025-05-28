from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, FacultyProfileForm, UserProfileForm, CustomAuthenticationForm
from .models import Faculty
from programs.models import AllowedEmail

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            allowed_email = AllowedEmail.objects.get(email=form.cleaned_data.get('email'))
            faculty = Faculty.objects.create(
                user=user,
                allowed_email=allowed_email,
                name=f"{user.first_name} {user.last_name}",
                short_name=user.username[:4].upper(),
                department=allowed_email.department,
                designation='Lecturer',  # Default designation
                phone_number=''  # Empty phone number
            )
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
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('accounts:dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')

@login_required
def dashboard(request):
    faculty = get_object_or_404(Faculty, user=request.user)
    context = {
        'faculty': faculty,
        'courses': faculty.section_set.all().distinct('course'),
        'sections': faculty.section_set.all(),
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
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
