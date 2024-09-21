from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Seller,Product,Order

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name","password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user


# serializers.py
class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['userId', 'address', 'store_name', 'description']
        read_only_fields = ['userId']

    def create(self, validated_data):
        user = self.context['request'].user
        if Seller.objects.filter(userId=user).exists():
            raise serializers.ValidationError("El usuario ya es un vendedor.")
        return Seller.objects.create(userId=user, **validated_data)

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['code', 'name', 'description', 'image_url', 'seller', 'price']
        #todo add kwargs
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['orderID', 'userID', 'orderDate', 'quantity', 'productCode', 'status']
        #todo add kwargs

