from django.db import models
from django.contrib.auth.models import User

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