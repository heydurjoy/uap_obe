from django.contrib import admin

# Register your models here.
from .models import Faculty, User, Holiday

admin.site.register(Faculty)
admin.site.register(User)
admin.site.register(Holiday)