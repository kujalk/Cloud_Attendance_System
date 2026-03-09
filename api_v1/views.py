from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)

from .forms import (
    AttendanceFilterForm,
    AttendanceForm,
    BulkAttendanceForm,
    DepartmentForm,
    StudentForm,
    SubjectForm,
)
from .models import Attendance, Department, Student, StudentSubject, Subject
from .send_mail import send_student_welcome
from .serializers import (
    AttendanceSerializer,
    DepartmentSerializer,
    StudentSerializer,
    StudentSubjectSerializer,
    SubjectSerializer,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_student(user) -> bool:
    return user.groups.filter(name='Student').exists()


def _require_admin(request):
    """Redirect students away from admin-only pages."""
    if is_student(request.user):
        return redirect('student_dashboard')
    return None


# ---------------------------------------------------------------------------
# REST API views (DRF)
# ---------------------------------------------------------------------------

class StudentListCreate(ListCreateAPIView):
    serializer_class = StudentSerializer
    queryset = Student.objects.all()


class StudentDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = StudentSerializer
    lookup_url_kwarg = 'student_id'
    queryset = Student.objects.all()


class AttendanceListCreate(ListCreateAPIView):
    serializer_class = AttendanceSerializer
    queryset = Attendance.objects.select_related('student', 'subject').all()


class AttendanceDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = AttendanceSerializer
    lookup_url_kwarg = 'pk'
    queryset = Attendance.objects.all()


class SubjectListCreate(ListCreateAPIView):
    serializer_class = SubjectSerializer
    queryset = Subject.objects.all()


class SubjectDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = SubjectSerializer
    lookup_url_kwarg = 'subject_code'
    queryset = Subject.objects.all()


class DepartmentListCreate(ListCreateAPIView):
    serializer_class = DepartmentSerializer
    queryset = Department.objects.all()


class StudentSubjectListCreate(ListCreateAPIView):
    serializer_class = StudentSubjectSerializer
    queryset = StudentSubject.objects.all()


# Legacy API class names (backward compatibility)
CreateStudent = StudentListCreate
CreateAttendance = AttendanceListCreate
CreateSubject = SubjectListCreate
CreateStudentSubject = StudentSubjectListCreate
manageStudentRecord = StudentDetail
manageAttendanceRecord = AttendanceDetail
manageSubjectRecord = SubjectDetail


# ---------------------------------------------------------------------------
# Dashboard / home
# ---------------------------------------------------------------------------

@login_required
def homePage(request):
    """Legacy URL /home — redirects to role-appropriate dashboard."""
    return redirect('dashboard')


@login_required
def dashboard(request):
    if is_student(request.user):
        return redirect('student_dashboard')
    return redirect('admin_dashboard')


@login_required
def admin_dashboard(request):
    guard = _require_admin(request)
    if guard:
        return guard

    today = timezone.now().date()

    total_students = Student.objects.filter(is_active=True).count()
    total_subjects = Subject.objects.filter(is_active=True).count()
    total_departments = Department.objects.count()

    today_qs = Attendance.objects.filter(lecture_date=today)
    today_present = today_qs.filter(status='Present').count()
    today_absent = today_qs.filter(status='Absent').count()
    today_late = today_qs.filter(status='Late').count()

    # Weekly chart data — last 7 days
    weekly = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        present = Attendance.objects.filter(lecture_date=d, status='Present').count()
        absent = Attendance.objects.filter(lecture_date=d, status='Absent').count()
        late = Attendance.objects.filter(lecture_date=d, status='Late').count()
        weekly.append({'label': d.strftime('%a %d'), 'present': present, 'absent': absent, 'late': late})

    chart_labels = json.dumps([w['label'] for w in weekly])
    chart_present = json.dumps([w['present'] for w in weekly])
    chart_absent = json.dumps([w['absent'] for w in weekly])
    chart_late = json.dumps([w['late'] for w in weekly])

    # Status distribution (all time)
    status_dist = (
        Attendance.objects
        .values('status')
        .annotate(count=Count('status'))
        .order_by('status')
    )
    status_labels = json.dumps([s['status'] for s in status_dist])
    status_counts = json.dumps([s['count'] for s in status_dist])

    # Subject-wise attendance rate
    subjects_stats = (
        Subject.objects
        .filter(is_active=True)
        .annotate(
            total=Count('attendances'),
            present=Count('attendances', filter=Q(attendances__status='Present')),
        )
        .filter(total__gt=0)
        .order_by('-present')[:8]
    )

    # Recent attendance records
    recent_attendance = (
        Attendance.objects
        .select_related('student', 'subject')
        .order_by('-lecture_date', '-created_at')[:15]
    )

    context = {
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_departments': total_departments,
        'today_present': today_present,
        'today_absent': today_absent,
        'today_late': today_late,
        'chart_labels': chart_labels,
        'chart_present': chart_present,
        'chart_absent': chart_absent,
        'chart_late': chart_late,
        'status_labels': status_labels,
        'status_counts': status_counts,
        'subjects_stats': subjects_stats,
        'recent_attendance': recent_attendance,
        'today': today,
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
def student_dashboard(request):
    if not is_student(request.user):
        return redirect('admin_dashboard')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact admin.')
        return redirect('admin_dashboard')

    all_attendance = student.attendances.select_related('subject').order_by('-lecture_date')
    total = all_attendance.count()
    present = all_attendance.filter(status='Present').count()
    absent = all_attendance.filter(status='Absent').count()
    late = all_attendance.filter(status='Late').count()
    pct = round((present / total) * 100, 1) if total else 0

    # Per-subject breakdown
    subject_stats = (
        all_attendance
        .values('subject__title')
        .annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status='Present')),
            absent=Count('id', filter=Q(status='Absent')),
        )
        .order_by('subject__title')
    )
    for s in subject_stats:
        t = s['total']
        s['pct'] = round((s['present'] / t) * 100, 1) if t else 0

    recent = all_attendance[:10]

    context = {
        'student': student,
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'pct': pct,
        'subject_stats': subject_stats,
        'recent': recent,
    }
    return render(request, 'dashboard/student.html', context)


# ---------------------------------------------------------------------------
# Student CRUD
# ---------------------------------------------------------------------------

@login_required
def student_list(request):
    guard = _require_admin(request)
    if guard:
        return guard

    q = request.GET.get('q', '')
    dept = request.GET.get('dept', '')
    students = Student.objects.select_related('department').filter(is_active=True)
    if q:
        students = students.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(email__icontains=q) | Q(roll_number__icontains=q)
        )
    if dept:
        students = students.filter(department_id=dept)

    departments = Department.objects.all()
    context = {'students': students, 'departments': departments, 'q': q, 'dept': dept}
    return render(request, 'students/list.html', context)


@login_required
def student_create(request):
    guard = _require_admin(request)
    if guard:
        return guard

    form = StudentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        student = form.save()
        logger.info(
            "STUDENT_CREATED | id=%s name=%s email=%s dept=%s by=%s",
            student.student_id, student.full_name, student.email,
            getattr(student.department, 'name', '—'), request.user.username,
        )
        messages.success(request, f'Student {student.full_name} created successfully.')
        return redirect('student_list')

    return render(request, 'students/form.html', {'form': form, 'action': 'Add New'})


@login_required
def student_edit(request, student_id):
    guard = _require_admin(request)
    if guard:
        return guard

    student = get_object_or_404(Student, pk=student_id)
    form = StudentForm(request.POST or None, request.FILES or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        form.save()
        logger.info(
            "STUDENT_UPDATED | id=%s name=%s by=%s",
            student.student_id, student.full_name, request.user.username,
        )
        messages.success(request, f'Student {student.full_name} updated.')
        return redirect('student_detail', student_id=student_id)

    return render(request, 'students/form.html', {'form': form, 'student': student, 'action': 'Edit'})


@login_required
def student_detail(request, student_id):
    guard = _require_admin(request)
    if guard:
        return guard

    student = get_object_or_404(Student, pk=student_id)
    attendance_records = student.attendances.select_related('subject').order_by('-lecture_date')
    enrollments = student.enrollments.select_related('subject')
    context = {
        'student': student,
        'attendance_records': attendance_records,
        'enrollments': enrollments,
        'attendance_pct': student.attendance_percentage(),
    }
    return render(request, 'students/detail.html', context)


@login_required
def student_delete(request, student_id):
    guard = _require_admin(request)
    if guard:
        return guard

    student = get_object_or_404(Student, pk=student_id)
    if request.method == 'POST':
        name = student.full_name
        student.is_active = False
        student.save()
        logger.info(
            "STUDENT_DEACTIVATED | id=%s name=%s by=%s",
            student.student_id, name, request.user.username,
        )
        messages.success(request, f'Student {name} deactivated.')
        return redirect('student_list')

    return render(request, 'students/confirm_delete.html', {'student': student})


# Legacy URL handlers — kept for any old bookmarks
@login_required
def student_insert(request):
    return redirect('student_create')

@login_required
def student_update(request):
    return redirect('student_list')

@login_required
def student_viewsingle(request):
    return redirect('student_list')

@login_required
def student_viewall(request):
    return redirect('student_list')


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

@login_required
def attendance_list(request):
    guard = _require_admin(request)
    if guard:
        return guard

    form = AttendanceFilterForm(request.GET or None)
    records = Attendance.objects.select_related('student', 'subject').order_by('-lecture_date')

    if form.is_valid():
        if form.cleaned_data.get('subject'):
            records = records.filter(subject=form.cleaned_data['subject'])
        if form.cleaned_data.get('date_from'):
            records = records.filter(lecture_date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            records = records.filter(lecture_date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('status'):
            records = records.filter(status=form.cleaned_data['status'])

    context = {'records': records[:200], 'form': form}
    return render(request, 'attendance/list.html', context)


@login_required
def mark_attendance(request):
    guard = _require_admin(request)
    if guard:
        return guard

    subjects = Subject.objects.filter(is_active=True).select_related('department')
    selected_subject_id = request.GET.get('subject') or request.POST.get('subject')
    selected_date = request.GET.get('date', timezone.now().date().isoformat())
    students = []
    existing_map = {}
    selected_subject = None

    if selected_subject_id:
        selected_subject = get_object_or_404(Subject, pk=selected_subject_id)
        enrolled_ids = StudentSubject.objects.filter(
            subject=selected_subject
        ).values_list('student_id', flat=True)

        if enrolled_ids:
            students = Student.objects.filter(
                student_id__in=enrolled_ids, is_active=True
            ).order_by('first_name')
        else:
            students = Student.objects.filter(is_active=True).order_by('first_name')

        existing = Attendance.objects.filter(
            subject=selected_subject, lecture_date=selected_date
        )
        existing_map = {a.student_id: a.status for a in existing}

    if request.method == 'POST' and selected_subject:
        lecture_date = request.POST.get('date')
        student_ids = request.POST.getlist('student_ids')
        created_count = updated_count = 0

        for sid in student_ids:
            status_val = request.POST.get(f'status_{sid}', 'Absent')
            remarks_val = request.POST.get(f'remarks_{sid}', '')
            s = get_object_or_404(Student, pk=sid)
            _, created = Attendance.objects.update_or_create(
                student=s,
                subject=selected_subject,
                lecture_date=lecture_date,
                defaults={
                    'status': status_val,
                    'remarks': remarks_val,
                    'marked_by': request.user,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        logger.info(
            "ATTENDANCE_MARKED | subject=%s date=%s new=%d updated=%d by=%s",
            selected_subject.title, lecture_date, created_count, updated_count,
            request.user.username,
        )
        messages.success(
            request,
            f'Attendance saved: {created_count} new, {updated_count} updated.'
        )
        return redirect('attendance_list')

    context = {
        'subjects': subjects,
        'selected_subject': selected_subject,
        'selected_date': selected_date,
        'students': students,
        'existing_map': existing_map,
    }
    return render(request, 'attendance/mark.html', context)


@login_required
def attendance_create(request):
    guard = _require_admin(request)
    if guard:
        return guard

    form = AttendanceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.marked_by = request.user
        record.save()
        messages.success(request, 'Attendance record created.')
        return redirect('attendance_list')

    return render(request, 'attendance/form.html', {'form': form, 'action': 'Add'})


@login_required
def attendance_edit(request, pk):
    guard = _require_admin(request)
    if guard:
        return guard

    record = get_object_or_404(Attendance, pk=pk)
    form = AttendanceForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Attendance record updated.')
        return redirect('attendance_list')

    return render(request, 'attendance/form.html', {'form': form, 'record': record, 'action': 'Edit'})


@login_required
def attendance_delete_view(request, pk):
    guard = _require_admin(request)
    if guard:
        return guard

    record = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Record deleted.')
        return redirect('attendance_list')

    return render(request, 'attendance/confirm_delete.html', {'record': record})


# Legacy names
@login_required
def attendance_insert(request):
    return redirect('attendance_create')

@login_required
def attendance_update(request):
    return redirect('attendance_list')

@login_required
def attendance_viewall(request):
    return redirect('attendance_list')

@login_required
def attendance_viewsingle(request):
    return redirect('attendance_list')

@login_required
def attendance_delete(request):
    return redirect('attendance_list')


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

@login_required
def subject_list(request):
    guard = _require_admin(request)
    if guard:
        return guard

    subjects = (
        Subject.objects
        .select_related('department')
        .annotate(student_count=Count('enrollments', distinct=True))
        .order_by('title')
    )
    return render(request, 'subjects/list.html', {'subjects': subjects})


@login_required
def subject_create(request):
    guard = _require_admin(request)
    if guard:
        return guard

    form = SubjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        subject = form.save()
        logger.info(
            "SUBJECT_CREATED | id=%s title=%s dept=%s by=%s",
            subject.pk, subject.title,
            getattr(subject.department, 'name', '—'), request.user.username,
        )
        messages.success(request, f'Subject "{subject.title}" created.')
        return redirect('subject_list')

    return render(request, 'subjects/form.html', {'form': form, 'action': 'Add New'})


@login_required
def subject_edit(request, subject_code):
    guard = _require_admin(request)
    if guard:
        return guard

    subject = get_object_or_404(Subject, pk=subject_code)
    form = SubjectForm(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Subject "{subject.title}" updated.')
        return redirect('subject_list')

    return render(request, 'subjects/form.html', {'form': form, 'subject': subject, 'action': 'Edit'})


@login_required
def subjects_viewall(request):
    return redirect('subject_list')


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@login_required
def reports(request):
    guard = _require_admin(request)
    if guard:
        return guard

    subject_id = request.GET.get('subject')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    subjects = Subject.objects.filter(is_active=True)
    report_data = []
    selected_subject = None

    if subject_id:
        selected_subject = get_object_or_404(Subject, pk=subject_id)
        qs = Attendance.objects.filter(subject=selected_subject).select_related('student')
        if date_from:
            qs = qs.filter(lecture_date__gte=date_from)
        if date_to:
            qs = qs.filter(lecture_date__lte=date_to)

        student_stats = (
            qs.values('student__student_id', 'student__first_name', 'student__last_name')
            .annotate(
                total=Count('id'),
                present=Count('id', filter=Q(status='Present')),
                absent=Count('id', filter=Q(status='Absent')),
                late=Count('id', filter=Q(status='Late')),
            )
            .order_by('student__first_name')
        )
        for s in student_stats:
            t = s['total']
            s['pct'] = round((s['present'] / t) * 100, 1) if t else 0
        report_data = student_stats

    context = {
        'subjects': subjects,
        'selected_subject': selected_subject,
        'report_data': report_data,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'reports/index.html', context)


# ---------------------------------------------------------------------------
# Student personal views
# ---------------------------------------------------------------------------

@login_required
def my_record(request):
    """Student personal profile."""
    if not is_student(request.user):
        return redirect('admin_dashboard')
    return redirect('student_dashboard')


@login_required
def viewPersonal(request):
    """Legacy URL — redirect to student dashboard."""
    return redirect('student_dashboard')


# ---------------------------------------------------------------------------
# Department CRUD
# ---------------------------------------------------------------------------

@login_required
def department_list(request):
    guard = _require_admin(request)
    if guard:
        return guard

    departments = Department.objects.annotate(
        student_count=Count('students', distinct=True),
        subject_count=Count('subjects', distinct=True),
    ).order_by('name')
    return render(request, 'departments/list.html', {'departments': departments})


@login_required
def department_create(request):
    guard = _require_admin(request)
    if guard:
        return guard

    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        dept = form.save()
        logger.info(
            "DEPARTMENT_CREATED | id=%s name=%s code=%s by=%s",
            dept.pk, dept.name, dept.code, request.user.username,
        )
        messages.success(request, f'Department "{dept.name}" created.')
        return redirect('department_list')

    return render(request, 'departments/form.html', {'form': form, 'action': 'Add New'})


@login_required
def department_edit(request, pk):
    guard = _require_admin(request)
    if guard:
        return guard

    dept = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=dept)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Department "{dept.name}" updated.')
        return redirect('department_list')

    return render(request, 'departments/form.html', {'form': form, 'dept': dept, 'action': 'Edit'})


# ---------------------------------------------------------------------------
# Email utilities
# ---------------------------------------------------------------------------

@login_required
def resend_welcome_email(request, student_id):
    """Resend the welcome / credentials email to a student (POST only)."""
    guard = _require_admin(request)
    if guard:
        return guard

    if request.method != 'POST':
        return redirect('student_detail', student_id=student_id)

    student = get_object_or_404(Student, pk=student_id)
    logger.info(
        "EMAIL_RESEND_REQUESTED | id=%s email=%s by=%s",
        student.student_id, student.email, request.user.username,
    )
    ok = send_student_welcome(student)
    if ok:
        messages.success(request, f'Welcome email resent to {student.email}.')
        logger.info("EMAIL_RESEND_OK | id=%s email=%s", student.student_id, student.email)
    else:
        messages.error(
            request,
            f'Failed to send email to {student.email}. '
            'Check logs/email.log for details.'
        )
        logger.error("EMAIL_RESEND_FAILED | id=%s email=%s", student.student_id, student.email)

    return redirect('student_detail', student_id=student_id)
