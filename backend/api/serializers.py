from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *
from rest_framework import serializers



class UserSerializer(serializers.ModelSerializer):
    is_seller = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password", "is_seller"]
        extra_kwargs = {"password": {"write_only": True}, "id": {"read_only": True}, "is_seller": {"read_only": True}}

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user

    def get_is_seller(self, obj):
        return Seller.objects.filter(userId=obj).exists()

# serializers.py
class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['userId', 'address', 'store_name', 'description']
        extra_kwargs = {'userId': {'read_only': True}}  # El userId no se puede modificar
    def create(self, validated_data):
        user = self.context['request'].user # Agregar el userId a los datos validados
        if Seller.objects.filter(userId=user).exists():
            raise serializers.ValidationError("El usuario ya es un vendedor.")
        return Seller.objects.create(userId=user, **validated_data)

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['orderID', 'userID', 'orderDate', 'quantity', 'productCode', 'status']
        extra_kwargs = {'userID': {'read_only': True}}

    def create(self, validated_data):
        # TODO -> status siempre arranca en lo primero y después se va actualizando
        user = self.context['request'].user
        return Order.objects.create(userID=user, **validated_data)

## -------------------------------------------------------------------------------------  ##

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['code', 'name', 'material', 'stock', 'description', 'image_url', 'seller', 'price']
        extra_kwargs = {'code': {'read_only': True}, 'seller': {'read_only': True}} # TODO chequear
        # read_only_fields = ['code', 'seller']  # Hacemos el código y el vendedor de solo lectura

    def create(self, validated_data):
        seller = self.context['request'].user.seller  # Obtenemos el vendedor del usuario autenticado
        # TODO manejar error

        return Product.objects.create(seller=seller, **validated_data)



class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['orderID', 'userID', 'orderDate', 'quantity', 'productCode', 'status']
        extra_kwargs = {'orderID': {'read_only': True}, 'orderDate': {'read_only': True}, 'status': {'read_only': True}}
        #read_only_fields = ['order_id', 'order_date', 'status']  # El ID, la fecha y el estado no se pueden modificar

    def create(self, validated_data):
        # Al crear una orden, el estado siempre será "pendiente"
        return Order.objects.create(**validated_data)


