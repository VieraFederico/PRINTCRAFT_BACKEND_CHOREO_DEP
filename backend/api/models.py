from django.db import models
from django.contrib.auth.models import User

class Seller(models.Model):
    userId = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    address = models.CharField(max_length=255, null=False)
    store_name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField()
    profile_picture = models.URLField(max_length=200, null=True, blank=True)
    materials = models.ManyToManyField('Material', related_name='sellers')  # Nueva relación muchos a muchos

    # TODO AGREGAR!!!
    mp_mail = models.EmailField(max_length=255, null=False)

    # rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    # total_sales = models.IntegerField(default=0)

    def __str__(self):
        return self.userId.username


class Material(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null = False)
    material = models.CharField(max_length=255, null = False)
    stock = models.IntegerField(null=False)
    description = models.TextField()
    stl_file_url = models.URLField(max_length=200, null=True, blank=True)  # URL del archivo STL
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False) # Placeholder for price
    # rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0) # todo agregar
    materials = models.ManyToManyField('Material', through='ProductMaterial')  # Relación muchos a muchos con Material
    categories = models.ManyToManyField('Category')  # Relación muchos a muchos con Category

    def __str__(self):
        return self.name

class ProductMaterial(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    class Meta:
        unique_together = ('product', 'material')

class PrintRequest(models.Model):
    requestID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    sellerID = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True)
    stl_url = models.URLField(max_length=200, null=False)
    description = models.TextField()
    quantity = models.IntegerField(null=False)
    material = models.CharField(max_length=255, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=255, null=False, default="Pendiente",
                              choices=[("Pendiente", "Pendiente"), ("Rechazada", "Rechazada"),
                                       ("Cotizada", "Cotizada"), ("Cancelada", "Cancelada"),
                                       ("En proceso", "En proceso"), ("Realizada", "Realizada")]
                              )

class DesignRequestImage(models.Model):
    image_url = models.URLField(max_length=200, primary_key=True)

    def __str__(self):
        return f"Image for {self.image_url}"


class DesignRequest(models.Model):
    requestID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    sellerID = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    design_images = models.ManyToManyField('DesignRequestImage')
    quantity = models.IntegerField(null=False)
    material = models.CharField(max_length=255, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=255, null=False, default="Pendiente",
                              choices=[("Pendiente", "Pendiente"), ("Rechazada", "Rechazada"),
                                       ("Cotizada", "Cotizada"), ("Cancelada", "Cancelada"),
                                       ("En proceso", "En proceso"), ("Realizada", "Realizada"),
                                       ("Aceptada", "Aceptada"), ("Entregada", "Entregada")]
                              )

# PLA, PETG, ABS, Nailon

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

    # totalAmount = models.FloatField(null=False)
    # AGREGAR INFORMACIÓN DE PAGO!!!

    # ELIMINAR EN EL FUTURO


class ProductImage(models.Model):
    product = models.ForeignKey('Product', related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField(max_length=200)

    def __str__(self):
        return f"Image for {self.product.name}"

# Crear modelo PrintInverseAuction
# Crear modelo PrintInverseAuctionResponse

# idem para DesignInverseAuction y DesignInverseAuctionResponse

class PrintReverseAuction(models.Model):
    requestID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    quantity = models.IntegerField(null=False)
    material = models.CharField(max_length=255, null=True)
    stl_file = models.URLField(max_length=200, null=False)
    status = models.CharField(max_length=255, null=False, default="Open",
                              choices=[("Open", "Open"), ("Closed", "Closed")])
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
