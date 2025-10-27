from django.db import models

# Create your models here.

class Product(models.Model):
    category = models.CharField(max_length=255)
    description = models.TextField()
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    limited = models.DecimalField(max_digits=10, decimal_places=2)
    add_link = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)






    def __str__(self):
        return self.category