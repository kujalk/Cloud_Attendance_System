from rest_framework import serializers
from .models import *

class studentSerializer(serializers.ModelSerializer):
    class Meta:
        model = student
        fields= "__all__"

class subjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = subjects
        fields= "__all__"

class attendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = attendance
        fields= ('id','studentId','subjectCode','status','lectureDate')


class studentSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = studentSubject
        fields= "__all__"