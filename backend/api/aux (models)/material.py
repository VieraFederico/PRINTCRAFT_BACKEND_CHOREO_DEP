# backend/api/models/request.py
from django.db import models
from django.contrib.auth.models import User

class PrintRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='print_requests')
    material = models.ForeignKey('Material', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    dimensions = models.CharField(max_length=100)  # e.g., "A4", "A3", "Custom"
    color = models.CharField(max_length=50)  # e.g., "Color", "Black and White"
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ], default='pending')
    additional_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"PrintRequest {self.id} by {self.user.username} - {self.status}"

class DesignRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='design_requests')
    design_file = models.FileField(upload_to='designs/')
    description = models.TextField()
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ], default='pending')

    def __str__(self):
        return f"DesignRequest {self.id} by {self.user.username} - {self.status}"