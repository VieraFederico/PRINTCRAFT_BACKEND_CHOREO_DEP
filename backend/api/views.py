from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics, permissions

from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import *



###############
#### USERS ####
###############
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class ReturnUserDataView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


#################
#### SELLERS ####
#################
class SellerCreateView(generics.CreateAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [permissions.IsAuthenticated]

class SellerDetailView(generics.RetrieveAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [AllowAny]
    lookup_field = 'userId'  # Usamos el campo userId para la búsqueda

class SellerListView(generics.ListAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [AllowAny]


##################
#### PRODUCTS ####
##################
class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsSeller]  # Solo vendedores pueden publicar productos

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

class SellerProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        userId = self.kwargs['userId']
        # Obtener el vendedor a partir del userId
        seller = Seller.objects.get(userId=userId)
        # Filtrar productos por el vendedor
        return Product.objects.filter(seller=seller)

class RecommendedProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        # Obtener los productos más vendidos
        return Product.objects.order_by('-stock')[:3]

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'code'  # Usamos el campo code para la búsqueda

################
#### ORDERS ####
################
class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden crear órdenes


    def perform_create(self, serializer):
        # Obtenemos los datos del serializer
        quantity = serializer.validated_data['quantity']
        product = serializer.validated_data['productCode']

        # Verificamos si la cantidad solicitada es menor o igual al stock disponible
        if product.stock < quantity:
            raise serializers.ValidationError('La cantidad solicitada excede el stock disponible.')

        # Actualizamos el stock del producto
        product.stock -= quantity
        product.save()

        # Guardamos la orden
        serializer.save()

class UserOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden ver sus órdenes

    def get_queryset(self):
        # Filtrar las órdenes por el usuario autenticado
        user = self.request.user
        return Order.objects.filter(userID=user)