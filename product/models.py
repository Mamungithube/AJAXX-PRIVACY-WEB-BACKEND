from django.db import models

# Create your models here.

class Product(models.Model):
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
        


    category = models.CharField(max_length=255)
    description = models.TextField()
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)
    add_link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return self.category
    

