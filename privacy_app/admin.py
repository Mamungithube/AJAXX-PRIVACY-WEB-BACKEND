from django.contrib import admin

# Register your models here.

from .models import OpteryScanHistory, OpteryMember
admin.site.register(OpteryScanHistory)
admin.site.register(OpteryMember)
