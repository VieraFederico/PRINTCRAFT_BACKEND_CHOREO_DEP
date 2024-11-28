
# backend/api/models/category.py
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the category was created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp when the category was last updated

    def __str__(self):
        return self.name