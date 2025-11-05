from django.db import models

# Create your models here.
from django.db import models

class OpteryLookup(models.Model):
    email = models.EmailField()
    response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
