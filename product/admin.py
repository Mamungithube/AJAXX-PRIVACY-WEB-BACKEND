from django.contrib import admin

# Register your models here.
from .models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = ('category', 'old_price', 'new_price', 'discounted_price', 'limited', 'add_link', 'created_at')
    search_fields = ('category', 'description')
    list_filter = ('created_at',)

admin.site.register(Product, ProductAdmin)