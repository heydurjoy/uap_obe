from django.db import models

from programs.models import AllowedEmail, Department
from django.contrib.auth.models import User

# Create your models here.
from django.db import models
from programs.models import AllowedEmail, Department
from django.contrib.auth.models import User


class Faculty(models.Model):
    DESIGNATION_CHOICES = [
        ('Professor', 'Professor'),
        ('Associate Professor', 'Associate Professor'),
        ('Assistant Professor', 'Assistant Professor'),
        ('Lecturer', 'Lecturer'),
        ('Teaching Assistant', 'Teaching Assistant'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    allowed_email = models.OneToOneField(AllowedEmail, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=4)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    designation = models.CharField(max_length=30, choices=DESIGNATION_CHOICES)
    phone_number = models.CharField(max_length=11)

    def __str__(self):
        return f"{self.short_name} - {self.name}"
