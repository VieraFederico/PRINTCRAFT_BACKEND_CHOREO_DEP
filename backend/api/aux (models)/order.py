from django.db import models
from django.contrib.auth.models import User, Product


class Order(models.Model):
    orderID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    orderDate = models.DateTimeField(auto_now_add=True, null=False)
    quantity = models.IntegerField(null=False)
    productCode = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)
    status = models.CharField(max_length=255, null=False, default="En proceso")
    preference_id = models.CharField(max_length=255, null=True, blank=True)  # New field for payment ID

    # status = models.CharField(max_length=10, choices=[("En proceso", "En proceso"), ("Pendiente", "Pendiente"), ("Realizada", "Realizada"), ("Rechazada", "Rechazada"), ("Cancelada", "Cancelada")], default="En proceso")

    def __str__(self):
        return self.orderID