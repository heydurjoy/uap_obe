from django.db import models
from ckeditor.fields import RichTextField  # If you're using CKEditor for RichTextField

DEPARTMENT_CHOICES = [
    ('CSE', 'Computer Science and Engineering'),
    ('CE', 'Civil Engineering'),
    ('EEE', 'Electrical and Electronic Engineering'),
    # Add other departments as needed
]


class Department(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.short_name


class Program(models.Model):
    name = models.CharField(max_length=255)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,  # set FK to NULL when department deleted
        null=True,
        blank=True
    )
    department_name = models.CharField(max_length=100, blank=True, default='will be auto set')
    description = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # If FK is set, keep the department name in the text field synced
        if self.department:
            self.department_name = self.department.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PLO(models.Model):
    numberic_sl = models.PositiveIntegerField(unique=True, default=1)  # e.g., "PLO1", "PLO2"
    alphabatic_sl = models.CharField(unique=True, default='a', max_length=1)  # e.g., "PLO1", "PLO2"
    description = models.TextField(null=True, blank=True)
    # program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='plos')

    def __str__(self):
        return f"{self.numberic_sl}. {self.alphabatic_sl} - {self.description}"


class AllowedEmail(models.Model):
    LEVEL_CHOICES = [
        (1, '1. Highest Access Faculty'),
        (2, '2. High Access Faculty '),
        (3, '3. Mid Access Faculty'),
        (4, '4. General Faculty'),  # default
    ]

    email = models.EmailField(unique=True)
    level = models.IntegerField(choices=LEVEL_CHOICES, default=4)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,  # set FK to NULL when department deleted
        null=True,
        blank=True
    )
    department_name = models.CharField(max_length=100, blank=True, default='will be auto set')

    def save(self, *args, **kwargs):
        # If FK is set, keep the department name in the text field synced
        if self.department:
            self.department_name = self.department.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.get_level_display()})"
