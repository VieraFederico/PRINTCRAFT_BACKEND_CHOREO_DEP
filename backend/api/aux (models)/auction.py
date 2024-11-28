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

class PrintReverseAuctionResponse(models.Model):
    responseID = models.AutoField(primary_key=True)
    auction = models.ForeignKey(PrintReverseAuction, related_name='responses', on_delete=models.CASCADE)
    seller = models.ForeignKey('Seller', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, null=False, default="Pending",
                              choices=[("Pending", "Pending"), ("Accepted", "Accepted"), ("Rejected", "Rejected")])
# pendiente, aceptada, rechazada, realizada, entregada

    def __str__(self):
        return f"Response {self.responseID} for Auction {self.auction.requestID} by {self.seller.store_name}"


class DesignReverseAuction(models.Model):
    requestID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    quantity = models.IntegerField(null=False)
    material = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=255, null=False, default="Open",
                              choices=[("Open", "Open"), ("Closed", "Closed")])
    response_count = models.IntegerField(null=False, default=0)
    accepted_response = models.OneToOneField('DesignReverseAuctionResponse', on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_auction')
    design_images = models.ManyToManyField('DesignRequestImage')

    def __str__(self):
        return f"Reverse Auction {self.requestID} by {self.userID.username}"


class DesignReverseAuctionResponse(models.Model):
    responseID = models.AutoField(primary_key=True)
    auction = models.ForeignKey(DesignReverseAuction, related_name='responses', on_delete=models.CASCADE)
    seller = models.ForeignKey('Seller', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, null=False, default="Pending",
                              choices=[("Pending", "Pending"), ("Accepted", "Accepted"), ("Rejected", "Rejected")])

    def __str__(self):
        return f"Response {self.responseID} for Auction {self.auction.requestID} by {self.seller.store_name}"