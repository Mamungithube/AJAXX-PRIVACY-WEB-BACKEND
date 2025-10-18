from django.contrib import admin
from .models import User, Profile
# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ( 'email', 'Fullname', 'is_staff', 'is_active','id')
    search_fields = ('email', 'Fullname')
    list_filter = ('is_staff', 'is_active')
    ordering = ('Fullname',)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'id')
    search_fields = ('user__email', 'user__Fullname')

    

admin.site.register(Profile, ProfileAdmin)
admin.site.register(User, UserAdmin)