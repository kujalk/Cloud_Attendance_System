from rest_framework import serializers
from .models import Department, Subject, Student, StudentSubject, Attendance


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class SubjectSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Subject
        fields = '__all__'


class StudentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    attendance_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ('student_id', 'created_at', 'updated_at')

    def get_attendance_percentage(self, obj):
        return obj.attendance_percentage()


class StudentSubjectSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    subject_title = serializers.CharField(source='subject.title', read_only=True)

    class Meta:
        model = StudentSubject
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    subject_title = serializers.CharField(source='subject.title', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


# Legacy-compatible serializers (old names)
studentSerializer = StudentSerializer
subjectSerializer = SubjectSerializer
attendanceSerializer = AttendanceSerializer
studentSubjectSerializer = StudentSubjectSerializer
