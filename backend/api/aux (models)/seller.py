from django.db import models
from django.contrib.auth.models import User

class Seller(models.Model):
    userId = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    address = models.CharField(max_length=255, null=False)
    store_name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField()
    profile_picture = models.URLField(max_length=200, null=True, blank=True)
    materials = models.ManyToManyField('Material', related_name='sellers')
    mp_mail = models.EmailField(max_length=255, null=False)

    def __str__(self):
        return self.userId.username