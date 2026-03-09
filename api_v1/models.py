from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4


def generate_uuid():
    return str(uuid4())


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Department(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Subject(TimeStampedModel):
    subject_code = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='subjects'
    )
    credits = models.PositiveSmallIntegerField(default=3)
    is_active = models.BooleanField(default=True)

    # Legacy alias kept for templates/API that reference old field name
    @property
    def subjectCode(self):
        return self.subject_code

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Student(TimeStampedModel):
    student_id = models.CharField(
        primary_key=True, default=generate_uuid, editable=False, max_length=200
    )
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='student_profile'
    )
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    email = models.EmailField(unique=True)
    mobile_no = models.CharField(max_length=15)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='students'
    )
    roll_number = models.CharField(max_length=50, blank=True)
    profile_photo = models.ImageField(
        upload_to='student_photos/', null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    # Legacy property aliases
    @property
    def studentId(self):
        return self.student_id

    @property
    def firstName(self):
        return self.first_name

    @property
    def lastName(self):
        return self.last_name

    @property
    def mobileNo(self):
        return self.mobile_no

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def attendance_percentage(self):
        total = self.attendances.count()
        if not total:
            return 0
        present = self.attendances.filter(status='Present').count()
        return round((present / total) * 100, 1)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class StudentSubject(TimeStampedModel):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='enrollments'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='enrollments'
    )

    class Meta:
        unique_together = ('student', 'subject')
        ordering = ['subject__title']

    def __str__(self):
        return f"{self.student} — {self.subject}"


class Attendance(TimeStampedModel):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Excused', 'Excused'),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='attendances'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendances'
    )
    lecture_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='marked_attendances'
    )

    # Legacy alias
    @property
    def studentId(self):
        return self.student

    @property
    def subjectCode(self):
        return str(self.subject.subject_code) if self.subject else ''

    @property
    def lectureDate(self):
        return str(self.lecture_date)

    class Meta:
        unique_together = ('student', 'subject', 'lecture_date')
        ordering = ['-lecture_date']

    def __str__(self):
        return f"{self.student} | {self.subject} | {self.lecture_date} | {self.status}"
