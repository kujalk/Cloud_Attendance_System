from django.db import models
from uuid import uuid4

def generateUUID():
    return str(uuid4())

class record(models.Model):
    recordAdded = models.DateTimeField(auto_now_add=True)
    recordModified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class student(record):
     studentId = models.CharField(primary_key=True, default=generateUUID, editable=False,max_length=200)
     firstName = models.CharField(max_length=200, blank=False, null=False)
     lastName = models.CharField(max_length=200, blank=False, null=False)
     address = models.CharField(max_length=200, blank=False, null=False)
     email = models.CharField(max_length=200, blank=False, null=False)
     mobileNo = models.CharField(max_length=15, blank=False, null=False)
     department = models.CharField(max_length=100, blank=False, null=False)

     def __str__(self):
         return str(self.studentId)
     

class subjects(record):
    subjectCode = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, blank=False, null=False)
    #department = models.ForeignKey(student,to_field="department",on_delete=models.CASCADE)

    def __str__(self):
         return str(self.subjectCode)

class studentSubject(record):
    studentId = models.ForeignKey(student,to_field="studentId",on_delete=models.CASCADE)
    subjectCode = models.ForeignKey(subjects,to_field="subjectCode",on_delete=models.CASCADE)

    def __str__(self):
         return str(self.studentId)

class attendance(record):
    studentId = models.ForeignKey(student,to_field="studentId",on_delete=models.CASCADE)
    subjectCode = models.CharField(max_length=200, blank=False, null=False)
    lectureDate = models.CharField(max_length=50, blank=False, null=False)
    status = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
         return str(self.studentId)