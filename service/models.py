from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model


# Create your models here.
class ContactUs(models.Model):
    email = models.CharField(max_length = 30)
    Subject = models.CharField(max_length = 30)
    Description = models.TextField()
    

STAR_CHOICES = [
    ('⭐', '⭐'),
    ('⭐⭐', '⭐⭐'),
    ('⭐⭐⭐', '⭐⭐⭐'),
    ('⭐⭐⭐⭐', '⭐⭐⭐⭐'),
    ('⭐⭐⭐⭐⭐', '⭐⭐⭐⭐⭐'),
]
class Review(models.Model):
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add = True)
    rating = models.CharField(choices = STAR_CHOICES, max_length = 10)
    
    def __str__(self):
        return f"gust : {self.reviewer.Fullname if self.reviewer.Fullname else self.reviewer.email} - Rating: {self.rating}"
