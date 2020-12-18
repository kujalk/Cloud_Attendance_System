from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.backends.signals import connection_created
from .models import student
from .send_mail import sendEmail

@receiver(post_save,sender=student)
def new_user_registration(sender, instance, created,**kwargs):
    if created:
        print("new user is created, therefore going to register it in Auth Model and send mail via AWS")
        
        #Filter student object to get more attributes
        newStudent=student.objects.get(studentId=instance)

        #Add the user to Auth.models.User Table
        user = User.objects.create_user(username=instance,email=newStudent.email,password='Student@123',
        first_name=newStudent.firstName,last_name=newStudent.lastName)

        #Add the user to new group
        Studentgroup = Group.objects.get(name='Student') 
        Studentgroup.user_set.add(user)

        #Send mail to user via AWS SES
        sendEmail(newStudent.studentId,newStudent.firstName,newStudent.lastName)