from django.contrib import admin

# Register your models here.
from .models import Program,PLO, AllowedEmail, Department
admin.site.register(Program)
admin.site.register(PLO)
admin.site.register(AllowedEmail)
admin.site.register(Department)
