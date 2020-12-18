from django.contrib import admin
from api_v1.models import *

# Register your models here.
admin.site.register(student)
admin.site.register(subjects)
admin.site.register(attendance)
admin.site.register(studentSubject)