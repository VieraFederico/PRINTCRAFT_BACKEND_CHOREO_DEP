
from django.db import models
from django.contrib.auth.models import Product,User,Seller


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
    review_count = models.IntegerField(default=0)
    review_sum = models.IntegerField(default=0)

class ProductImage(models.Model):
    product = models.ForeignKey('Product', related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField(max_length=200)

    def __str__(self):
        return f"Image for {self.product.name}"

# Crear modelo PrintInverseAuction
# Crear modelo PrintInverseAuctionResponse

# idem para DesignInverseAuction y DesignInverseAuctionResponse

class ProductReview(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(null=False, choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(null=True, blank=True) # meter max_length de 255
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"