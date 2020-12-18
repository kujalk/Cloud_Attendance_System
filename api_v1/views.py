from django.shortcuts import render
from rest_framework.generics import ListAPIView,RetrieveUpdateDestroyAPIView, ListCreateAPIView, ListAPIView
from .models import *
from .serializers import *
from django import http
from django.contrib.auth.decorators import login_required


# Create your views here.
class manageStudentRecord(RetrieveUpdateDestroyAPIView):
    '''
    This view is used to manage records related to a Student
    '''

    serializer_class = studentSerializer
    lookup_url_kwarg = 'studentId'
    queryset = student.objects.all()

class manageAttendanceRecord(RetrieveUpdateDestroyAPIView):
    '''
    This view is used to manage records related to a Attendance
    '''

    serializer_class = attendanceSerializer
    lookup_url_kwarg = 'id'
    queryset = attendance.objects.all()

class manageSubjectRecord(RetrieveUpdateDestroyAPIView):
    '''
    This view is used to manage records related to a Subject
    '''

    serializer_class = subjectSerializer
    lookup_url_kwarg = 'subjectCode'
    queryset = subjects.objects.all()


class CreateStudent(ListCreateAPIView):
    '''
    This view is used to create a record and retrieve all records to student
    '''

    serializer_class = studentSerializer
    queryset = student.objects.all()

class CreateAttendance(ListCreateAPIView):
    '''
    This view is used to create a record and retrieve all records related to attandance
    '''

    serializer_class = attendanceSerializer
    queryset = attendance.objects.all()

class CreateSubject(ListCreateAPIView):
    '''
    This view is used to create a record and retrieve all records related to subjects
    '''

    serializer_class = subjectSerializer
    queryset = subjects.objects.all()

class CreateStudentSubject(ListCreateAPIView):
    '''
    This view is used to create a record and retrieve all records related to StudentSubjects
    '''

    serializer_class = studentSubjectSerializer
    queryset = studentSubject.objects.all()


@login_required
def homePage(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "index.htm")

    if group.name=="Student":
        print("User ID : "+str(request.user))
        personalData = student.objects.get(studentId=request.user)
        context = {"student": personalData}
        return render(request, "my_record.htm",context)
    else:
        return render(request, "index.htm")

'''
Student Record Management
'''

@login_required
def student_insert(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "student_insert.htm")

    if group.name=="Student":
        personalData = student.objects.get(studentId=request.user)
        context = {"student": personalData}
        return render(request, "my_record.htm",context)
    else:
        return render(request, "student_insert.htm")

@login_required
def student_update(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "student_update.htm")

    if group.name=="Student":
        return render(request, "my_record.htm")
    else:
        return render(request, "student_update.htm")

@login_required
def student_delete(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "student_delete.htm")

    if group.name=="Student":
        return render(request, "my_record.htm")
    else:
        return render(request, "student_delete.htm")

@login_required
def student_viewsingle(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "student_viewsingle.htm")

    if group.name=="Student":
        return render(request, "my_record.htm")
    else:
        return render(request, "student_viewsingle.htm")

@login_required
def student_viewall(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        personalRecords = student.objects.all()
        context = {"allrecord": personalRecords}
        return render(request, "student_viewall.htm",context)

    if group.name=="Student":
        personalData = student.objects.get(studentId=request.user)
        context = {"student": personalData}
        return render(request, "my_record.htm",context)
    else:
        personalRecords = student.objects.all()
        context = {"allrecord": personalRecords}
        return render(request, "student_viewall.htm",context)


'''
Attendance
'''

@login_required
def attendance_insert(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "attendance_insert.htm")

    if group.name=="Student":
        personalData = student.objects.get(studentId=request.user)
        context = {"student": personalData}
        return render(request, "my_record.htm",context)

@login_required
def attendance_update(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "attendance_update.htm")

    if group.name=="Student":
        personalData = student.objects.get(studentId=request.user)
        context = {"student": personalData}
        return render(request, "my_record.htm",context)

@login_required
def attendance_delete(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "attendance_delete.htm")

    if group.name=="Student":
        personalData = student.objects.get(studentId=request.user)
        context = {"student": personalData}
        return render(request, "my_record.htm",context)

@login_required
def attendance_viewsingle(request):

    try:
        group = request.user.groups.get(name="Student")
    except:

        try:
            student=(request.POST['studentIdValue'])
            personalData = attendance.objects.filter(studentId=student)
            context = {"allrecord": personalData}
            return render(request, "attendance_viewsingle.htm",context)
        
        except:
            return render(request, "attendance_viewsingle.htm")

    if group.name=="Student":
        personalData = student.objects.get(studentId=request.user)
        context = {"student": personalData}
        return render(request, "my_record.htm",context)

@login_required
def attendance_viewall(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        attendanceRecords = attendance.objects.all()
        context = {"allrecord": attendanceRecords}
        return render(request, "attendance_viewall.htm",context)

    if group.name=="Student":
        personalData = student.objects.get(studentId=request.user)
        context = {"student": personalData}
        return render(request, "my_record.htm",context)

'''
Personal Student Record
'''

@login_required
def viewPersonal(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "index.htm")

    if group.name=="Student":
        attendanceRecords = attendance.objects.filter(studentId=str(request.user))
        context = {"allrecord": attendanceRecords}
        return render(request, "my_recordall.htm",context)
    else:
        return render(request, "index.htm")

'''
Subjects
'''

@login_required
def subjects_viewall(request):

    try:
        group = request.user.groups.get(name="Student")
    except:
        return render(request, "subjects_viewall.htm")

    if group.name=="Student":
        personalData = student.objects.get(studentId=request.user)
        context = {"student": personalData}
        return render(request, "my_record.htm",context)
