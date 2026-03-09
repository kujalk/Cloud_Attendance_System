from django.contrib import admin
from .models import Department, Subject, Student, StudentSubject, Attendance


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_code', 'title', 'department', 'credits', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('title',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'email', 'department', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'roll_number')
    readonly_fields = ('student_id', 'created_at', 'updated_at')


@admin.register(StudentSubject)
class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'created_at')
    list_filter = ('subject',)
    search_fields = ('student__first_name', 'student__last_name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'lecture_date', 'status', 'marked_by')
    list_filter = ('status', 'subject', 'lecture_date')
    search_fields = ('student__first_name', 'student__last_name')
    date_hierarchy = 'lecture_date'
