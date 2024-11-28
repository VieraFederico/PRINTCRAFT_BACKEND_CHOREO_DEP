from django.db import models
from django.contrib.auth.models import User

class PrintReverseAuction(models.Model):
    requestID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    quantity = models.IntegerField(null=False)
    material = models.CharField(max_length=255, null=True)
    stl_file_url = models.URLField(max_length=200, null=False)
    status = models.CharField(max_length=255, null=False, default="Open",
                              choices=[("Open", "Open"), ("Closed", "Closed")])
    response_count = models.IntegerField(null=False, default=0)
    accepted_response = models.OneToOneField('PrintReverseAuctionResponse', on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_auction')


    def __str__(self):
        return f"Reverse Auction {self.requestID} by {self.userID.username}"