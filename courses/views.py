from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Avg, F, Q
from django.core.exceptions import PermissionDenied
from .models import (
    Course, CLO, Section, Student, Enrollment,
    AssessmentTemplate, AssessmentComponent, AssessmentMark, Attainment,
    ProjectGroup, Session, Attendance
)
from accounts.models import Faculty, Holiday
from programs.models import Program, PLO, Department
from .forms import CourseForm, SectionForm, BulkEnrollForm, EnrollmentForm, CLOForm
from django.core.exceptions import ValidationError
from accounts.views import faculty_required, require_access_level
from django.db import transaction
from django.db import IntegrityError
from django import forms
from datetime import datetime, timedelta
import json
from django.views.decorators.http import require_http_methods

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
def all_sections(request, f_id):
    faculty = get_object_or_404(Faculty, pk=f_id)
    sections = Section.objects.filter(faculties=faculty)
    print(len(sections))
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
    
    # Get all enrollments for this section and ensure they have Regular enrollment type
    enrollments = Enrollment.objects.filter(section=section).select_related('student').order_by('student__student_id')
    
    # Get assessment template if exists
    template = AssessmentTemplate.objects.filter(section=section).first()
    
    context = {
        'section': section,
        'template': template,
        'enrollments': enrollments,
        'title': f'{section.course.code} - Section {section.name}',
        'sessions': section.sessions.all()
    }
    
    return render(request, 'courses/section_detail.html', context)

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

def parse_student_name(name):
    """Parse student name to extract enrollment type from brackets"""
    import re
    # Match text in brackets at the end of the name
    match = re.match(r'(.*?)\s*\((.*?)\)$', name.strip())
    if match:
        # If brackets found, use the text inside as enrollment type
        return match.group(1).strip(), match.group(2).strip()
    # If no brackets found, return clean name and 'Regular' as default
    return name.strip(), 'Regular'

@login_required
@faculty_required
def bulk_enroll_view(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    
    # Check if user is a faculty of this section or superuser
    if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
        messages.error(request, 'You do not have permission to enroll students in this section.')
        return redirect('courses:section_detail', section_id=section.id)
    
    if request.method == 'POST':
        form = BulkEnrollForm(request.POST)
        if form.is_valid():
            student_ids_str = form.cleaned_data['student_ids']
            student_names_str = form.cleaned_data['student_names']
            
            # Split IDs and names by lines and strip whitespace
            student_ids = [id.strip() for id in student_ids_str.splitlines() if id.strip()]
            student_names = [name.strip() for name in student_names_str.splitlines() if name.strip()]
            
            # Check if the number of IDs and names match
            if len(student_ids) != len(student_names):
                messages.error(request, 'Number of student IDs and names do not match.')
                return render(request, 'courses/bulk_enroll.html', {
                    'section': section,
                    'form': form,
                    'title': f'Bulk Enroll Students - {section.course.code} Section {section.name}'
                })

            enrolled_count = 0
            created_count = 0
            errors = []
            name_conflicts = []
            successful_enrollments_data = [] # Store data for successful enrollments to process later

            # Use a transaction for atomicity for the initial processing
            try:
                with transaction.atomic():
                    for i in range(len(student_ids)):
                        student_id = student_ids[i]
                        student_name = student_names[i]

                        # Skip if student ID is empty after stripping
                        if not student_id:
                            errors.append(f'Skipping line {i+1}: Empty student ID.')
                            continue

                        # Parse student name to extract enrollment type
                        parsed_name, enrollment_type = parse_student_name(student_name)

                        try:
                            # Try to get existing student
                            existing_student = Student.objects.get(student_id=student_id)
                            
                            # Student exists, check name
                            if existing_student.name.strip().lower() != parsed_name.strip().lower():
                                # Name mismatch - record conflict
                                name_conflicts.append({
                                    'student_id': student_id,
                                    'existing_name': existing_student.name,
                                    'provided_name': parsed_name,
                                    'enrollment_type': enrollment_type,
                                    'index': i # Keep track of the original position
                                })
                                # Do NOT process enrollment for this student in this batch due to conflict
                                continue # Move to the next student
                            else:
                                # Name matches, add to successful enrollments data
                                successful_enrollments_data.append({
                                    'student': existing_student,
                                    'enrollment_type': enrollment_type
                                })

                        except Student.DoesNotExist:
                            # Student does not exist, add to successful enrollments data for creation and enrollment
                            successful_enrollments_data.append({
                                'student_id': student_id,
                                'name': parsed_name,
                                'enrollment_type': enrollment_type,
                                'index': i
                            })

                        except Exception as e:
                            # Catch any other unexpected errors during processing this student
                            errors.append(f'Unexpected error processing student ID {student_id}: {e}')
                            # Decide whether to stop or continue on other errors. Let's stop for now for safety.
                            raise # Re-raise to trigger atomic rollback of the whole batch

                # --- End of initial processing atomic block ---

                # If conflicts were found, store them in session and redirect to conflict resolution page
                if name_conflicts:
                    request.session['bulk_enroll_conflicts'] = name_conflicts
                    request.session['bulk_enroll_section_id'] = section.id
                    request.session['bulk_enroll_successful_data'] = successful_enrollments_data # Store successful ones too
                    messages.warning(request, f'{len(name_conflicts)} name conflicts detected. Please resolve them.')
                    return redirect('courses:resolve_conflicts', section_id=section.id)

                else: # No conflicts, proceed with creating new students and enrollments in a new atomic block
                    if not successful_enrollments_data:
                         messages.info(request, 'No valid student data provided.')
                         # Display any individual processing errors
                         for error in errors:
                              messages.error(request, error)
                         return redirect('courses:section_detail', section_id=section.id)

                    # Create new students and enrollments for entries without conflicts
                    try:
                        with transaction.atomic():
                            for item in successful_enrollments_data:
                                if 'student' in item: # Existing student with matching name
                                    student = item['student']
                                    enrollment, enrolled = Enrollment.objects.get_or_create(
                                        student=student,
                                        section=section,
                                        defaults={'enrollment_type': item['enrollment_type']}
                                    )
                                    if enrolled:
                                        enrolled_count += 1
                                else: # New student
                                    student_id = item['student_id']
                                    student_name = item['name']
                                    enrollment_type = item['enrollment_type']
                                    try:
                                        new_student = Student.objects.create(
                                            student_id=student_id,
                                            name=student_name,
                                            program=section.course.program
                                        )
                                        created_count += 1
                                        messages.info(request, f'Created new student: {new_student.name} ({new_student.student_id})')

                                        enrollment, enrolled = Enrollment.objects.get_or_create(
                                            student=new_student,
                                            section=section,
                                            defaults={'enrollment_type': enrollment_type}
                                        )
                                        if enrolled:
                                            enrolled_count += 1 # Should always be true here
                                    except IntegrityError:
                                        errors.append(f'Error creating student ID {student_id} concurrently.')
                                        raise # Critical, rollback
                                    except Exception as e:
                                        errors.append(f'Unexpected error creating student ID {student_id}: {e}')
                                        raise # Critical, rollback

                        # If this second atomic block completes successfully
                        if created_count > 0 or enrolled_count > 0:
                            success_message = f'Successfully enrolled {enrolled_count} students.'
                            if created_count > 0:
                                 success_message += f' ({created_count} new students created).'
                            messages.success(request, success_message)

                        # Display any individual processing errors
                        for error in errors:
                             messages.error(request, error)

                        return redirect('courses:section_detail', section_id=section.id)

                    except Exception as e: # Catch exceptions from the second atomic block
                        final_errors = errors + [f'An unrecoverable error occurred during enrollment: {e}']
                        for error_msg in final_errors:
                            messages.error(request, error_msg)
                        messages.error(request, 'Bulk enrollment failed during enrollment phase. The transaction was rolled back.')
                        # Re-render the form, potentially without submitted data if redirect clears it
                        return render(request, 'courses/bulk_enroll.html', {
                            'section': section,
                            'form': form,
                            'errors': final_errors,
                            'title': f'Bulk Enroll Students - {section.course.code} Section {section.name}'
                        })

            except Exception as e: # Catch exceptions from the first atomic block (initial processing)
                final_errors = errors + [f'An unrecoverable error occurred during initial processing: {e}']
                for error_msg in final_errors:
                    messages.error(request, error_msg)
                messages.error(request, 'Bulk enrollment failed during initial processing. The transaction was rolled back.')
                 # Re-render the form, potentially without submitted data if redirect clears it
                return render(request, 'courses/bulk_enroll.html', {
                    'section': section,
                    'form': form,
                    'errors': final_errors,
                    'title': f'Bulk Enroll Students - {section.course.code} Section {section.name}'
                })

    else: # GET request
        form = BulkEnrollForm()

    return render(request, 'courses/bulk_enroll.html', {
        'section': section,
        'form': form,
        'title': f'Bulk Enroll Students - {section.course.code} Section {section.name}'
    })

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

# Define a form for conflict resolution dynamically based on conflicts
class ConflictResolutionForm(forms.Form):
    def __init__(self, conflicts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conflicts = conflicts
        for i, conflict in enumerate(conflicts):
            choices = [
                ('existing', f"Keep Existing Name: {conflict['existing_name']}"),
                ('provided', f"Use Provided Name: {conflict['provided_name']}")
            ]
            self.fields[f'conflict_{i}'] = forms.ChoiceField(
                choices=choices,
                widget=forms.RadioSelect,
                label=f"Student ID: {conflict['student_id']}",
                initial='existing' # Default to keeping existing name
            )

@login_required
@faculty_required
def resolve_conflicts_view(request, section_id):
    # Ensure the user has permission to be here and the conflicts data is in session
    section = get_object_or_404(Section, id=section_id)
    if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('courses:section_detail', section_id=section.id)

    conflicts = request.session.get('bulk_enroll_conflicts')
    successful_data = request.session.get('bulk_enroll_successful_data')
    session_section_id = request.session.get('bulk_enroll_section_id')

    # Check if session data exists and matches the current section
    if not conflicts or session_section_id != section.id:
        messages.warning(request, 'No conflicts to resolve for this section or session data expired.')
        # Clean up session data if it exists but is for a different section
        if 'bulk_enroll_conflicts' in request.session:
            del request.session['bulk_enroll_conflicts']
        if 'bulk_enroll_successful_data' in request.session:
             del request.session['bulk_enroll_successful_data']
        if 'bulk_enroll_section_id' in request.session:
             del request.session['bulk_enroll_section_id']

        return redirect('courses:bulk_enroll', section_id=section.id)

    if request.method == 'POST':
        form = ConflictResolutionForm(conflicts, request.POST)
        if form.is_valid():
            resolved_conflicts = []
            # Process the form data to see which name was chosen for each conflict
            for i, conflict in enumerate(conflicts):
                choice = form.cleaned_data[f'conflict_{i}']
                resolved_conflicts.append({
                    'student_id': conflict['student_id'],
                    'chosen_name': conflict['existing_name'] if choice == 'existing' else conflict['provided_name'],
                    'enrollment_type': conflict['enrollment_type']
                })

            enrolled_count = 0
            created_count = 0
            errors = []

            # Process successful enrollments and then resolved conflicts
            try:
                with transaction.atomic():
                    # Process entries that had no conflicts initially
                    if successful_data:
                        for item in successful_data:
                             if 'student' in item: # Existing student with matching name
                                 student = item['student']
                             else: # This case shouldn't happen with the new bulk_enroll_view logic storing new students in successful_data
                                # Fallback/precaution: look up or create the new student if needed
                                 try:
                                     student, created = Student.objects.get_or_create(
                                         student_id=item['student_id'],
                                         defaults={'name': item['name'], 'program': section.course.program}
                                     )
                                     if created:
                                         created_count += 1
                                         messages.info(request, f'Created new student during conflict resolution processing: {student.name} ({student.student_id})')
                                 except IntegrityError:
                                      errors.append(f'Concurrent creation error for student ID {item["student_id"]}.')
                                      raise # Critical, rollback
                                 except Exception as e:
                                      errors.append(f'Unexpected error creating student ID {item["student_id"]} during conflict resolution: {e}')
                                      raise # Critical, rollback

                             # Create enrollment for these successful students
                             enrollment, enrolled = Enrollment.objects.get_or_create(
                                 student=student,
                                 section=section,
                                 defaults={'enrollment_type': item['enrollment_type']}
                             )
                             if enrolled:
                                 enrolled_count += 1

                    # Process entries that had name conflicts, now resolved
                    for resolved_conflict in resolved_conflicts:
                        student_id = resolved_conflict['student_id']
                        chosen_name = resolved_conflict['chosen_name']
                        enrollment_type = resolved_conflict['enrollment_type']

                        try:
                            student = Student.objects.get(student_id=student_id)

                            # Update student name if the chosen name is different from the current name
                            if student.name != chosen_name:
                                student.name = chosen_name
                                student.save()
                                # Optionally add info message about name update
                                # messages.info(request, f'Updated name for student {student_id} to "{chosen_name}".')

                            # Create enrollment for the resolved student
                            enrollment, enrolled = Enrollment.objects.get_or_create(
                                student=student,
                                section=section,
                                defaults={'enrollment_type': enrollment_type}
                            )
                            if enrolled:
                                enrolled_count += 1

                        except Student.DoesNotExist:
                            # This should not happen if initial check was done, but as a precaution
                            errors.append(f'Error enrolling student ID {student_id}: Student not found after conflict resolution.')
                            # Decide if this is critical enough to rollback or just report
                            # For now, let's report and continue
                            # raise # Uncomment to rollback on this error
                        except IntegrityError:
                            errors.append(f'Concurrent enrollment error for student ID {student_id}.')
                            raise # Critical, rollback
                        except Exception as e:
                            errors.append(f'Unexpected error processing resolved conflict for student ID {student_id}: {e}')
                            raise # Critical, rollback

                # If the atomic block completes successfully
                if created_count > 0 or enrolled_count > 0:
                    success_message = f'Successfully enrolled {enrolled_count} students.'
                    if created_count > 0:
                        success_message += f' ({created_count} new students created).'
                    messages.success(request, success_message)

                # Display any individual processing errors
                for error in errors:
                     messages.error(request, error)

                # Clean up session data after successful processing
                if 'bulk_enroll_conflicts' in request.session:
                    del request.session['bulk_enroll_conflicts']
                if 'bulk_enroll_successful_data' in request.session:
                     del request.session['bulk_enroll_successful_data']
                if 'bulk_enroll_section_id' in request.session:
                     del request.session['bulk_enroll_section_id']

                return redirect('courses:section_detail', section_id=section.id)

            except Exception as e: # Catch exceptions that caused the atomic block to rollback
                final_errors = errors + [f'An unrecoverable error occurred during conflict resolution processing: {e}']
                for error_msg in final_errors:
                    messages.error(request, error_msg)
                messages.error(request, 'Bulk enrollment failed during conflict resolution. The transaction was rolled back.')

                # Keep session data so the user can try again
                return render(request, 'courses/resolve_conflicts.html', {
                    'section': section,
                    'form': form,
                    'conflicts': conflicts, # Pass conflicts to the template to repopulate form
                    'errors': final_errors,
                    'title': f'Resolve Enrollment Conflicts - {section.course.code} Section {section.name}'
                })

    else: # GET request
        form = ConflictResolutionForm(conflicts)

    return render(request, 'courses/resolve_conflicts.html', {
        'section': section,
        'form': form,
        'conflicts': conflicts, # Pass conflicts to the template for display
        'title': f'Resolve Enrollment Conflicts - {section.course.code} Section {section.name}'
    })

@login_required
@faculty_required
def search_students_ajax(request):
    """AJAX endpoint to search for students by ID or name."""
    term = request.GET.get('term', '')
    students = []
    if term:
        # Search by student_id (exact match) or name (case-insensitive contains)
        students = Student.objects.filter(
            Q(student_id__iexact=term) | Q(name__icontains=term)
        ).values('student_id', 'name')[:10] # Limit results
        
    # Format results for Select2 or similar autocomplete libraries if needed, 
    # but simple list of dicts is generally usable.
    results = list(students) # Convert queryset to list

    return JsonResponse(results, safe=False)

@login_required
@faculty_required
def single_enroll_view(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    
    # Check if user is a faculty of this section or superuser
    if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
        messages.error(request, 'You do not have permission to enroll students in this section.')
        return redirect('courses:section_detail', section_id=section.id)
    
    if request.method == 'POST':
        student_identifier = request.POST.get('student_identifier', '').strip()
        
        if not student_identifier:
            messages.warning(request, 'Please enter a student ID or name.')
            return redirect('courses:section_detail', section_id=section.id)
        
        try:
            # Try to find student by ID first
            student = Student.objects.get(student_id=student_identifier)
        except Student.DoesNotExist:
            # If not found by ID, try to find by name (case-insensitive, partial match)
            # Note: This might return multiple students, consider refining search if needed
            students_by_name = Student.objects.filter(name__icontains=student_identifier)
            if students_by_name.count() == 1:
                student = students_by_name.first()
            elif students_by_name.count() > 1:
                messages.warning(request, f'Multiple students found matching "{student_identifier}". Please use a more specific identifier or Student ID.')
                return redirect('courses:section_detail', section_id=section.id)
            else:
                messages.warning(request, f'Student with identifier "{student_identifier}" not found. Please use bulk enrollment to add a new student.')
                return redirect('courses:bulk_enroll', section_id=section.id)
        
        # If a student was found (either by ID or unique name match)
        if student:
            # Check if student is already enrolled in this section
            if Enrollment.objects.filter(student=student, section=section).exists():
                messages.info(request, f'{student.name} ({student.student_id}) is already enrolled in this section.')
            else:
                # Enroll the student
                try:
                    Enrollment.objects.create(student=student, section=section, enrollment_type='Regular') # Default to Regular
                    messages.success(request, f'Successfully enrolled {student.name} ({student.student_id}).')
                except Exception as e:
                    messages.error(request, f'Error enrolling {student.name} ({student.student_id}): {e}')
        
        # Redirect back to section detail page
        return redirect('courses:section_detail', section_id=section.id)
    
    else: # GET request not allowed for this view
        return redirect('courses:section_detail', section_id=section.id)

@login_required
@faculty_required
def edit_enrollment_view(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    # Check if user has permission (is faculty of the section or superuser)
    if not request.user.is_superuser and not enrollment.section.faculties.filter(id=request.user.faculty.id).exists():
        messages.error(request, 'You do not have permission to edit this enrollment.')
        return redirect('courses:section_detail', section_id=enrollment.section.id)

    if request.method == 'POST':
        form = EnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Enrollment for {enrollment.student.name} updated successfully.')
            return redirect('courses:section_detail', section_id=enrollment.section.id)
    else:
        form = EnrollmentForm(instance=enrollment)

    return render(request, 'courses/edit_enrollment.html', {
        'form': form,
        'enrollment': enrollment,
        'section': enrollment.section,
        'title': f'Edit Enrollment - {enrollment.student.name} in {enrollment.section.course.code} Section {enrollment.section.name}'
    })

@login_required
@faculty_required
def delete_enrollment_view(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    # Check if user has permission (is faculty of the section or superuser)
    if not request.user.is_superuser and not enrollment.section.faculties.filter(id=request.user.faculty.id).exists():
        messages.error(request, 'You do not have permission to delete this enrollment.')
        return redirect('courses:section_detail', section_id=enrollment.section.id)

    if request.method == 'POST':
        section_id = enrollment.section.id # Get section ID before deleting enrollment
        enrollment.delete()
        messages.success(request, f'Enrollment for {enrollment.student.name} removed successfully.')
        return redirect('courses:section_detail', section_id=section_id)

    # If it's not a POST request, maybe render a confirmation page? Or just redirect.
    # Given the modal handles confirmation, redirecting seems appropriate for GET.
    return redirect('courses:section_detail', section_id=enrollment.section.id)

@login_required
@faculty_required
def manage_project_groups_view(request, section_id):
    section = get_object_or_404(Section, id=section_id)

    # Check if user has permission (is faculty of the section or superuser)
    if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
        messages.error(request, 'You do not have permission to manage project groups for this section.')
        return redirect('courses:section_detail', section_id=section.id)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_group':
            project_name = request.POST.get('project_name')
            group_number = request.POST.get('group_number')
            
            try:
                # Check if group number already exists
                if ProjectGroup.objects.filter(section=section, group_sl=group_number).exists():
                    messages.error(request, f'Group number {group_number} already exists in this section.')
                else:
                    ProjectGroup.objects.create(
                        section=section,
                        group_sl=group_number,
                        project_name=project_name
                    )
                    messages.success(request, f'Project group {group_number} created successfully.')
            except Exception as e:
                messages.error(request, f'Error creating project group: {str(e)}')

        elif action == 'delete_group':
            group_id = request.POST.get('group_id')
            try:
                group = ProjectGroup.objects.get(id=group_id, section=section)
                group.delete()
                messages.success(request, 'Project group deleted successfully.')
            except ProjectGroup.DoesNotExist:
                messages.error(request, 'Project group not found.')
            except Exception as e:
                messages.error(request, f'Error deleting project group: {str(e)}')

        elif action == 'add_student':
            group_id = request.POST.get('group_id')
            student_id = request.POST.get('student_id')
            
            try:
                group = ProjectGroup.objects.get(id=group_id, section=section)
                student = Student.objects.get(student_id=student_id)
                
                # Check if student is enrolled in the section
                if not section.enrollment_set.filter(student=student).exists():
                    messages.error(request, 'Student is not enrolled in this section.')
                else:
                    # Check if student is already in a group
                    if ProjectGroup.objects.filter(section=section, students=student).exists():
                        messages.error(request, 'Student is already assigned to a group in this section.')
                    else:
                        group.students.add(student)
                        messages.success(request, f'Student {student.name} added to group {group.group_sl}.')
            except ProjectGroup.DoesNotExist:
                messages.error(request, 'Project group not found.')
            except Student.DoesNotExist:
                messages.error(request, 'Student not found.')
            except Exception as e:
                messages.error(request, f'Error adding student to group: {str(e)}')

        elif action == 'remove_student':
            group_id = request.POST.get('group_id')
            student_id = request.POST.get('student_id')
            
            try:
                group = ProjectGroup.objects.get(id=group_id, section=section)
                student = Student.objects.get(student_id=student_id)
                group.students.remove(student)
                messages.success(request, f'Student {student.name} removed from group {group.group_sl}.')
            except ProjectGroup.DoesNotExist:
                messages.error(request, 'Project group not found.')
            except Student.DoesNotExist:
                messages.error(request, 'Student not found.')
            except Exception as e:
                messages.error(request, f'Error removing student from group: {str(e)}')

    # Get all project groups for this section
    project_groups = ProjectGroup.objects.filter(section=section).prefetch_related('students')
    
    # Get all students enrolled in this section who are not in any group
    enrolled_students = Student.objects.filter(
        enrollment__section=section
    ).exclude(
        project_groups__section=section
    ).distinct()

    # Get all students enrolled in this section
    all_enrolled_students = Student.objects.filter(
        enrollment__section=section
    ).distinct()

    # Create a list of students with their group information
    students_with_groups = []
    for student in all_enrolled_students:
        group = ProjectGroup.objects.filter(section=section, students=student).first()
        students_with_groups.append({
            'student': student,
            'group': group
        })

    context = {
        'section': section,
        'title': f'Manage Project Groups - {section.course.code} Section {section.name}',
        'project_groups': project_groups,
        'available_students': enrolled_students,  # keep for now, but not used in modal
        'students_with_groups': students_with_groups,
    }
    return render(request, 'courses/manage_project_groups.html', context)

@login_required
@faculty_required
def edit_section_view(request, section_id):
    section = get_object_or_404(Section, id=section_id)

    # Check if user has permission (is primary/secondary faculty of the section or superuser)
    if not request.user.is_superuser and request.user.faculty not in [section.primary_faculty, section.secondary_faculty]:
         messages.error(request, 'You do not have permission to edit this section.')
         return redirect('courses:section_detail', section_id=section.id)

    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Section {section.name} details updated successfully.')
            return redirect('courses:section_detail', section_id=section.id)
    else:
        form = SectionForm(instance=section, user=request.user)

    context = {
        'form': form,
        'section': section,
        'title': f'Edit Section - {section.course.code} Section {section.name}'
    }
    return render(request, 'courses/edit_section.html', context)

@login_required
@faculty_required
def manage_clos_view(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    
    # Check if user has permission
    if not request.user.is_superuser and request.user.faculty not in [section.primary_faculty, section.secondary_faculty]:
        messages.error(request, 'You do not have permission to manage CLOs for this section.')
        return redirect('courses:section_detail', section_id=section.id)

    clos = CLO.objects.filter(course=section.course).order_by('sl')
    
    if request.method == 'POST':
        form = CLOForm(request.POST, course=section.course)
        if form.is_valid():
            try:
                clo = form.save(commit=False)
                clo.course = section.course
                clo.save()
                messages.success(request, f'CLO {clo.get_clo_code()} created successfully.')
                return redirect('courses:manage_clos', section_id=section.id)
            except IntegrityError:
                messages.error(request, f'CLO with serial number {form.cleaned_data.get("sl")} already exists for this course.')
        else:
            # If form is invalid, show the first error message
            for field, errors in form.errors.items():
                if field == 'sl':
                    messages.error(request, errors[0])
                    break
    else:
        form = CLOForm(course=section.course)

    context = {
        'section': section,
        'clos': clos,
        'form': form,
        'title': f'Manage CLOs - {section.course.code} Section {section.name}'
    }
    return render(request, 'courses/manage_clos.html', context)

@login_required
@faculty_required
def edit_clo_view(request, section_id, clo_id):
    section = get_object_or_404(Section, id=section_id)
    clo = get_object_or_404(CLO, id=clo_id, course=section.course)
    
    # Check if user has permission
    if not request.user.is_superuser and request.user.faculty not in [section.primary_faculty, section.secondary_faculty]:
        messages.error(request, 'You do not have permission to edit CLOs for this section.')
        return redirect('courses:section_detail', section_id=section.id)

    if request.method == 'POST':
        form = CLOForm(request.POST, instance=clo, course=section.course)
        if form.is_valid():
            form.save()
            messages.success(request, f'CLO {clo.get_clo_code()} updated successfully.')
            return redirect('courses:manage_clos', section_id=section.id)
    else:
        form = CLOForm(instance=clo, course=section.course)

    context = {
        'section': section,
        'clo': clo,
        'form': form,
        'title': f'Edit CLO - {section.course.code} Section {section.name}'
    }
    return render(request, 'courses/edit_clo.html', context)

@login_required
@faculty_required
def delete_clo_view(request, section_id, clo_id):
    section = get_object_or_404(Section, id=section_id)
    clo = get_object_or_404(CLO, id=clo_id, course=section.course)
    
    # Check if user has permission
    if not request.user.is_superuser and request.user.faculty not in [section.primary_faculty, section.secondary_faculty]:
        messages.error(request, 'You do not have permission to delete CLOs for this section.')
        return redirect('courses:section_detail', section_id=section.id)

    if request.method == 'POST':
        clo_code = clo.get_clo_code()
        clo.delete()
        messages.success(request, f'CLO {clo_code} deleted successfully.')
        return redirect('courses:manage_clos', section_id=section.id)

    context = {
        'section': section,
        'clo': clo,
        'title': f'Delete CLO - {section.course.code} Section {section.name}'
    }
    return render(request, 'courses/delete_clo.html', context)

@login_required
@faculty_required
def add_session_dates_view(request, section_id):
    section = get_object_or_404(Section, id=section_id)

    # Permission check
    if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
        messages.error(request, 'You do not have permission to add session dates for this section.')
        return redirect('courses:section_detail', section_id=section.id)

    if Session.objects.filter(section=section).exists():
        messages.error(request, 'Session dates already exist. Contact admin to update them.')
        return redirect('courses:section_detail', section_id=section.id)

    if request.method == 'POST':
        first_date_str = request.POST.get('first_date')
        second_date_str = request.POST.get('second_date')

        if not first_date_str or not second_date_str:
            messages.error(request, 'Please provide both first and second session dates.')
            return redirect('courses:section_detail', section_id=section.id)

        try:
            first_date = datetime.strptime(first_date_str, '%Y-%m-%d').date()
            second_date = datetime.strptime(second_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('courses:section_detail', section_id=section.id)

        interval = (second_date - first_date).days
        num_sessions = 14 if section.course.is_lab else 28
        session_number = 1
        week_index = 0
        sessions = []

        # Preload single-day holiday dates for fast lookup
        single_holiday_dates = set(Holiday.objects.filter(end_date__isnull=True).values_list('start_date', flat=True))
        print(single_holiday_dates)
        try:
            while session_number <= num_sessions:
                # Calculate target_date for current session
                if session_number % 2 == 1:  # First session of the week
                    target_date = first_date + timedelta(weeks=week_index)
                else:  # Second session of the week
                    target_date = first_date + timedelta(days=interval + week_index * 7)

                # Check if target_date is a single-day holiday
                print(target_date, type(target_date))
                if target_date in single_holiday_dates:
                    sessions.append(Session(
                        section=section,
                        session_number=session_number,
                        date=target_date,
                        is_holiday=True
                    ))
                    session_number += 1
                    # Increment week_index after both sessions (every 2 sessions)
                    if session_number % 2 == 1:
                        week_index += 1
                    continue

                # Check if target_date falls within any holiday range
                range_holiday = Holiday.objects.filter(
                    start_date__lte=target_date,
                    end_date__gte=target_date
                ).first()

                if range_holiday:
                    # Skip the whole week by increasing week_index
                    week_index += 1
                    continue

                # Create a normal session (not holiday)
                sessions.append(Session(
                    section=section,
                    session_number=session_number,
                    date=target_date,
                    is_holiday=False
                ))
                session_number += 1

                # Increment week_index after both sessions (every 2 sessions)
                if session_number % 2 == 1:
                    week_index += 1

            # Bulk create all sessions
            Session.objects.bulk_create(sessions)
            messages.success(request, f"Successfully created {len(sessions)} sessions.")

        except Exception as e:
            messages.error(request, f"Error creating sessions: {str(e)}")

    return redirect('courses:section_detail', section_id=section.id)

@login_required
@faculty_required
def delete_all_sessions_view(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    
    # Check if user is a faculty of this section
    if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
        messages.error(request, 'You do not have permission to delete sessions for this section.')
        return redirect('courses:section_detail', section_id=section.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Delete all sessions for this section
                Session.objects.filter(section=section).delete()
            messages.success(request, 'All sessions have been deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting sessions: {str(e)}')
    
    return redirect('courses:section_detail', section_id=section.id)

@login_required
@faculty_required
def update_session_date_view(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        session = get_object_or_404(Session, id=session_id)
        section = session.section
        
        # Check if user is a faculty of this section
        if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
            return JsonResponse({'success': False, 'message': 'You do not have permission to update this session.'})
        
        # Parse the JSON data
        data = json.loads(request.body)
        new_date = data.get('date')
        
        if not new_date:
            return JsonResponse({'success': False, 'message': 'No date provided'})
        
        # Update the session date
        session.date = datetime.strptime(new_date, '%Y-%m-%d').date()
        session.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@faculty_required
def update_section_total_classes_view(request, section_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        section = get_object_or_404(Section, id=section_id)
        
        # Check if user has permission for this section
        if request.user.faculty not in section.faculties.all():
            return JsonResponse({'success': False, 'message': 'You do not have permission to update this section'})
        
        data = json.loads(request.body)
        total_classes = int(data.get('total_classes', 28))
        
        if total_classes < 1:
            return JsonResponse({'success': False, 'message': 'Total classes must be at least 1'})
        
        section.total_classes = total_classes
        section.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@faculty_required
@require_http_methods(["GET"])
def get_attendance(request, section_id):
    """Get attendance data for a section."""
    section = get_object_or_404(Section, id=section_id)
    
    # Check if user is a faculty of this section or superuser
    if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get all attendance records for this section
    attendance_records = Attendance.objects.filter(
        session__section=section
    ).values('student_id', 'session_id', 'is_present')
    
    return JsonResponse(list(attendance_records), safe=False)

@login_required
@faculty_required
@require_http_methods(["POST"])
def save_attendance(request, section_id):
    """Save attendance data for a student in a session."""
    section = get_object_or_404(Section, id=section_id)
    
    # Check if user is a faculty of this section or superuser
    if not request.user.is_superuser and not section.faculties.filter(id=request.user.faculty.id).exists():
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        session_id = data.get('session_id')
        is_present = data.get('is_present')
        
        if not all([student_id, session_id, is_present is not None]):
            return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)
        
        # Get or create attendance record
        attendance, created = Attendance.objects.get_or_create(
            student_id=student_id,
            session_id=session_id,
            defaults={'is_present': is_present}
        )
        
        if not created:
            attendance.is_present = is_present
            attendance.save()
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
