from django.contrib import admin

# Register your models here.
from .models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = ('category', 'old_price', 'new_price', 'discounted_price', 'add_link', 'id')
    search_fields = ('category', 'description')
    list_filter = ('created_at',)

admin.site.register(Product, ProductAdmin)