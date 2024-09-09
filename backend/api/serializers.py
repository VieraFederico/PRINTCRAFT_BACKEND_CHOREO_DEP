from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Seller,Product,Order

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username", "password"]
        extra_kwargs = {
            "password": {"write_only":True}
            }
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ["userId","address","store_name","description"]
        #todo add kwargs

class ProducSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['code', 'name', 'description', 'image_url', 'seller', 'price']

class OrderSerializer(serializers.ModelSerilizer):
    class Meta:
        model = Order
        fields = ['orderID', 'userID', 'orderDate', 'quantity', 'productCode', 'status']
