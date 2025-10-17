from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    


GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )


class User(AbstractUser):
    username = None  # Remove the username field
    Fullname = models.CharField(max_length=55)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()

    def __str__(self):
        return self.Fullname if self.Fullname else self.email

    




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    otp = models.CharField(max_length=4, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    Country = models.CharField(max_length=56, blank=True, null=True)
    City = models.CharField(max_length=35, blank=True, null=True)
    Province = models.CharField(max_length=35, blank=True, null=True)
    Gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    Bio = models.TextField(blank=True, null=True)
    social_auth_provider = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):  
        return self.user.Fullname if self.user.Fullname else self.user.email