from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique = True)
    username = models.CharField(max_length = 20, unique = True)
    password = models.CharField(max_length = 128)
    
    def __str__(self):
        return self.email

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, primary_key = True)
    name = models.CharField(max_length = 40)
    avatarUrl = models.URLField

    def __str__(self):
        return f"{self.username}'s Profile"