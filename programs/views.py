from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Program, Department, AllowedEmail
from .forms import ProgramForm, DepartmentForm, AllowedEmailForm

def is_superuser(user):
    return user.is_superuser

# Create your views here.

@login_required
@user_passes_test(is_superuser)
def program_list(request):
    programs = Program.objects.all().select_related('department')
    return render(request, 'programs/program_list.html', {'programs': programs})

@login_required
@user_passes_test(is_superuser)
def program_create(request):
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program created successfully.')
            return redirect('programs:program_list')
    else:
        form = ProgramForm()
    return render(request, 'programs/program_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(is_superuser)
def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    return render(request, 'programs/program_detail.html', {'program': program})

@login_required
@user_passes_test(is_superuser)
def program_edit(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program updated successfully.')
            return redirect('programs:program_list')
    else:
        form = ProgramForm(instance=program)
    return render(request, 'programs/program_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_superuser)
def program_delete(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        program.delete()
        messages.success(request, 'Program deleted successfully!')
        return redirect('programs:program_list')
    return render(request, 'programs/program_confirm_delete.html', {'program': program})

@login_required
def allowed_email_list(request):
    allowed_emails = AllowedEmail.objects.all()
    return render(request, 'programs/allowed_email_list.html', {'allowed_emails': allowed_emails})

@login_required
def allowed_email_create(request):
    if request.method == 'POST':
        form = AllowedEmailForm(request.POST)
        if form.is_valid():
            allowed_email = form.save()
            messages.success(request, 'Allowed email added successfully!')
            return redirect('programs:allowed_email_list')
    else:
        form = AllowedEmailForm()
    return render(request, 'programs/allowed_email_form.html', {'form': form, 'action': 'Add'})

@login_required
def allowed_email_delete(request, pk):
    allowed_email = get_object_or_404(AllowedEmail, pk=pk)
    if request.method == 'POST':
        allowed_email.delete()
        messages.success(request, 'Allowed email deleted successfully!')
        return redirect('programs:allowed_email_list')
    return render(request, 'programs/allowed_email_confirm_delete.html', {'allowed_email': allowed_email})
