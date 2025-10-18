from django.contrib import admin
from .models import ContactUs
from . import models
# Register your models here.

class ContactModelAdmin(admin.ModelAdmin):
    list_display = ['email', 'Subject', 'Description']
admin.site.register(ContactUs, ContactModelAdmin)


# Register your models here.
admin.site.register(models.Review)
