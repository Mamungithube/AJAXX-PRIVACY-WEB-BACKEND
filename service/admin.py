from django.contrib import admin
from .models import ContactUs
from . import models


class ContactModelAdmin(admin.ModelAdmin):
    list_display = ['email', 'Subject', 'Description']
admin.site.register(ContactUs, ContactModelAdmin)


admin.site.register(models.Review)
