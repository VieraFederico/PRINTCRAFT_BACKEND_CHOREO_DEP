from django.db import models
from django.contrib.auth.models import User

class Seller(models.Model):
    userId = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    address = models.CharField(max_length=255, null=False)
    store_name = models.CharField(max_length=255, null=False)
    description = models.TextField()

    # rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    # total_sales = models.IntegerField(default=0)

    def __str__(self):
        return self.userId.username


class Product(models.Model):
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, null = False)
    material = models.CharField(max_length=255, null = False)
    stock = models.IntegerField(null=False)
    description = models.TextField()
    image_url = models.URLField(max_length=200)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False) # Placeholder for price

    def __str__(self):
        return self.name
class Order(models.Model):
    orderID = models.CharField(max_length=255, primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    orderDate = models.DateField(null=False)
    # totalAmount = models.FloatField(null=False)

    # ELIMINAR EN EL FUTURO
    quantity = models.IntegerField(null=False)
    productCode = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)

    status = models.CharField(max_length=255, null=False)

    # AGREGAR INFORMACIÓN DE PAGO!!!

    def __str__(self):
        return self.orderID
