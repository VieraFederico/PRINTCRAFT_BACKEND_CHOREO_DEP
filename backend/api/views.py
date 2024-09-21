from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics, permissions

from .models import Seller
from .serializers import UserSerializer, SellerSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

# Create your views here.

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

# views.py
class SellerCreateView(generics.CreateAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(userId=self.request.user)

# Ver detalles de un vendedor (solo para el mismo usuario o admin)
class SellerDetailView(generics.RetrieveAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Seller.objects.get(userId=self.request.user)
