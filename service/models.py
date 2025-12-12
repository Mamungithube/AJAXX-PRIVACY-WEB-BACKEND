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



class FAQ(models.Model):
    question = models.CharField(max_length=250)
    answer = models.TextField(max_length=100,blank=True,null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question
    
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['-created_at']