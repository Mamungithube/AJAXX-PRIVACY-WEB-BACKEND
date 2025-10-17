from django.contrib import admin
from .models import ContactUs
# Register your models here.

class ContactModelAdmin(admin.ModelAdmin):
    list_display = ['email', 'Subject', 'Description']
admin.site.register(ContactUs, ContactModelAdmin)


from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Review)
class ContactModelAdmin(admin.ModelAdmin):
    list_display = ['email', 'Subject', 'Description']