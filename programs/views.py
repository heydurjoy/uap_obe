from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Program, AllowedEmail
from .forms import ProgramForm, AllowedEmailForm

# Create your views here.

@login_required
def program_list(request):
    programs = Program.objects.all()
    return render(request, 'programs/program_list.html', {'programs': programs})

@login_required
def program_create(request):
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            messages.success(request, 'Program created successfully!')
            return redirect('programs:program_detail', pk=program.pk)
    else:
        form = ProgramForm()
    return render(request, 'programs/program_form.html', {'form': form, 'action': 'Create'})

@login_required
def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    return render(request, 'programs/program_detail.html', {'program': program})

@login_required
def program_edit(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            program = form.save()
            messages.success(request, 'Program updated successfully!')
            return redirect('programs:program_detail', pk=program.pk)
    else:
        form = ProgramForm(instance=program)
    return render(request, 'programs/program_form.html', {'form': form, 'action': 'Edit'})

@login_required
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
