from django.contrib.auth.models import AbstractUser
from django.db import models

from programs.models import AllowedEmail, Department
from django.utils.translation import gettext_lazy as _


# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username


class Faculty(models.Model):
    DESIGNATION_CHOICES = [
        ('Professor', 'Professor'),
        ('Associate Professor', 'Associate Professor'),
        ('Assistant Professor', 'Assistant Professor'),
        ('Lecturer', 'Lecturer'),
        ('Teaching Assistant', 'Teaching Assistant'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    allowed_email = models.OneToOneField(AllowedEmail, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=4)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    designation = models.CharField(max_length=50, choices=DESIGNATION_CHOICES)
    phone_number = models.CharField(max_length=11, blank=True)

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    @property
    def access_level(self):
        # Give superusers the same access level as level 1 users
        if self.user.is_superuser:
            return 1
        return self.allowed_email.level

    def can_create_section(self):
        """General faculty and above can create sections"""
        return self.access_level <= 4

    def can_manage_courses(self):
        """Mid level faculty and above can manage courses"""
        return self.access_level <= 3

    def can_manage_allowed_emails(self):
        """High level faculty and above can manage allowed emails"""
        return self.access_level <= 2

    def can_access_dashboard(self):
        """Highest level faculty can access dashboard"""
        return self.access_level == 1

    def get_access_level_display(self):
        """Get the display name of the access level"""
        if self.user.is_superuser:
            return "Superuser"
        return dict(AllowedEmail.LEVEL_CHOICES).get(self.access_level, 'Unknown')


from django.db import models
from django.core.exceptions import ValidationError

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk and self.__class__.objects.exists():
            raise ValidationError(f"Only one instance of {self.__class__.__name__} is allowed.")
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class Holiday(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
