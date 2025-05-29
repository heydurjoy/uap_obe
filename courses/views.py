from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Avg, F, Q
from django.core.exceptions import PermissionDenied
from .models import (
    Course, CLO, Section, Student, Enrollment,
    AssessmentTemplate, AssessmentComponent, AssessmentMark, Attainment
)
from accounts.models import Faculty
from programs.models import Program, PLO, Department
from .forms import CourseForm, SectionForm
from django.core.exceptions import ValidationError
from accounts.views import faculty_required, require_access_level

@login_required
@faculty_required
def course_list(request):
    if request.user.is_superuser:
        courses = Course.objects.all()
    else:
        faculty = get_object_or_404(Faculty, user=request.user)
        courses = Course.objects.filter(section__teacher=faculty).distinct()
    
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
@faculty_required
def all_sections(request):
    if request.user.is_superuser:
        sections = Section.objects.all()
    else:
        faculty = get_object_or_404(Faculty, user=request.user)
        sections = Section.objects.filter(faculties=faculty)
    
    return render(request, 'courses/all_sections.html', {
        'sections': sections,
        'title': 'All Sections'
    })

@login_required
@faculty_required
def section_list(request, course_code):
    course = get_object_or_404(Course, code=course_code)
    if request.user.is_superuser:
        sections = Section.objects.filter(course=course)
    else:
        faculty = get_object_or_404(Faculty, user=request.user)
        sections = Section.objects.filter(course=course, faculties=faculty)
    
    return render(request, 'courses/section_list.html', {
        'course': course,
        'sections': sections,
        'title': f'Sections - {course.code}'
    })

@login_required
@faculty_required
def section_detail(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    
    # Check if user is a faculty of this section
    if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
        messages.error(request, 'You do not have permission to view this section.')
        return redirect('courses:course_list')
    
    template = AssessmentTemplate.objects.filter(section=section).first()
    students = Student.objects.filter(enrollment__section=section)
    
    return render(request, 'courses/section_detail.html', {
        'section': section,
        'template': template,
        'students': students
    })

@login_required
@faculty_required
@require_access_level('can_create_section')
def create_section(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = SectionForm(request.POST, user=request.user)
        if form.is_valid():
            section = form.save(commit=False)
            section.course = course
            try:
                section.save()
                messages.success(request, 'Section created successfully.')
                return redirect('courses:section_detail', section_id=section.id)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = SectionForm(user=request.user)
    
    return render(request, 'courses/section_form.html', {
        'form': form,
        'course': course,
        'title': f'Create Section - {course.code}'
    })

@login_required
def bulk_enroll_students(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    if not request.user.is_superuser and section.teacher.user != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        student_data = request.POST.get('student_data', '').strip()
        lines = student_data.split('\n')
        
        for line in lines:
            if line.strip():
                student_id, name = line.strip().split(',')
                student, created = Student.objects.get_or_create(
                    student_id=student_id.strip(),
                    defaults={'name': name.strip(), 'program': section.course.program}
                )
                Enrollment.objects.get_or_create(student=student, section=section)
        
        messages.success(request, 'Students enrolled successfully.')
        return redirect('section_detail', section_id=section.id)
    
    return render(request, 'courses/bulk_enroll.html', {'section': section})

@login_required
def assessment_template(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    if not request.user.is_superuser and section.teacher.user != request.user:
        raise PermissionDenied
    
    template, created = AssessmentTemplate.objects.get_or_create(section=section)
    
    if request.method == 'POST':
        # Handle template updates
        template.is_public = request.POST.get('is_public') == 'on'
        template.save()
        
        # Handle component updates
        components_data = request.POST.getlist('components')
        for comp_data in components_data:
            # Process component data and update/create components
            pass
        
        messages.success(request, 'Assessment template updated successfully.')
        return redirect('section_detail', section_id=section.id)
    
    return render(request, 'courses/assessment_template.html', {
        'section': section,
        'template': template
    })

@login_required
def enter_marks(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    if not request.user.is_superuser and section.teacher.user != request.user:
        raise PermissionDenied
    
    template = get_object_or_404(AssessmentTemplate, section=section)
    students = Student.objects.filter(enrollment__section=section)
    
    if request.method == 'POST':
        for student in students:
            for component in template.components.all():
                mark_value = request.POST.get(f'mark_{student.id}_{component.id}')
                if mark_value:
                    AssessmentMark.objects.update_or_create(
                        component=component,
                        student=student,
                        defaults={'mark': mark_value}
                    )
        
        messages.success(request, 'Marks entered successfully.')
        return redirect('section_detail', section_id=section.id)
    
    return render(request, 'courses/enter_marks.html', {
        'section': section,
        'template': template,
        'students': students
    })

@login_required
def obe_analytics(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    if not request.user.is_superuser and section.teacher.user != request.user:
        raise PermissionDenied
    
    # Calculate CLO attainment
    clo_attainments = {}
    for clo in section.course.clos.all():
        marks = AssessmentMark.objects.filter(
            component__clo=clo,
            component__template__section=section
        ).values('student').annotate(
            total_mark=Sum('mark'),
            total_weight=Sum('component__weight')
        )
        
        for mark in marks:
            if mark['total_weight'] > 0:
                attainment = (mark['total_mark'] / mark['total_weight']) * 100
                if mark['student'] not in clo_attainments:
                    clo_attainments[mark['student']] = {}
                clo_attainments[mark['student']][clo.code] = attainment
    
    # Calculate PLO attainment
    plo_attainments = {}
    for plo in PLO.objects.all():
        related_clos = CLO.objects.filter(plos=plo, course=section.course)
        for student_id in clo_attainments:
            plo_marks = [clo_attainments[student_id].get(clo.code, 0) for clo in related_clos]
            if plo_marks:
                plo_attainments.setdefault(student_id, {})[plo.code] = sum(plo_marks) / len(plo_marks)
    
    return render(request, 'courses/obe_analytics.html', {
        'section': section,
        'clo_attainments': clo_attainments,
        'plo_attainments': plo_attainments
    })

@login_required
def student_attainment_history(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    if not request.user.is_superuser:
        faculty = get_object_or_404(Faculty, user=request.user)
        if not Section.objects.filter(teacher=faculty, enrollment__student=student).exists():
            raise PermissionDenied
    
    # Get all sections the student has been enrolled in
    sections = Section.objects.filter(enrollment__student=student).order_by('year', 'semester')
    
    # Calculate attainment history
    attainment_history = {}
    for section in sections:
        template = AssessmentTemplate.objects.filter(section=section).first()
        if template:
            for clo in section.course.clos.all():
                marks = AssessmentMark.objects.filter(
                    component__clo=clo,
                    component__template=template,
                    student=student
                ).values('student').annotate(
                    total_mark=Sum('mark'),
                    total_weight=Sum('component__weight')
                ).first()
                
                if marks and marks['total_weight'] > 0:
                    attainment = (marks['total_mark'] / marks['total_weight']) * 100
                    key = f"{section.semester} {section.year}"
                    if key not in attainment_history:
                        attainment_history[key] = {}
                    attainment_history[key][clo.code] = attainment
    
    return render(request, 'courses/student_attainment_history.html', {
        'student': student,
        'attainment_history': attainment_history
    })

@login_required
@faculty_required
@require_access_level('can_manage_courses')
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course created successfully.')
            return redirect('courses:course_list')
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form})

@login_required
@faculty_required
@require_access_level('can_manage_courses')
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully.')
            return redirect('courses:course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {'form': form})

@login_required
@faculty_required
@require_access_level('can_manage_courses')
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully.')
        return redirect('courses:course_list')
    return render(request, 'courses/course_confirm_delete.html', {'course': course})

@login_required
@faculty_required
@require_access_level('can_create_section')
def select_course(request):
    """View for selecting a course to create a section"""
    # Get all departments
    departments = Department.objects.all().order_by('name')
    
    # Get all courses with their related programs
    courses = Course.objects.select_related('program', 'program__department').all()
    
    context = {
        'courses': courses,
        'departments': departments,
    }
    return render(request, 'courses/select_course.html', context)
