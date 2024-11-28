from rest_framework import permissions
from .models.models import Seller

class IsSeller(permissions.BasePermission):
    """
    Permiso personalizado para verificar si el usuario es un vendedor.
    """

    def has_permission(self, request, view):
        # Verificar si el usuario autenticado tiene un Seller asociado
        return Seller.objects.filter(userId=request.user).exists()