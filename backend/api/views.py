"""
/api/seller-orders/
orderid
userid (se puede fletar)
orderdate
quantity
productcode
status

email del usuario
nombre del producto

"""

"""
/
cuando acepto reverse auction, cambiar el status

"""

from http.client import responses

import mercadopago
from django.shortcuts import render
from django.contrib.auth.models import User
from mercadopago import sdk
from pyexpat.errors import messages
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import *
from django.conf import settings
from django.http import JsonResponse
from api.services.supabase_client import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
import uuid  # Para generar el idempotency key
import ollama
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json####################
#### AUXILIARES ####
####################
def delete_product_image(product_image):
    try:
        remove_file_from_supabase('images', product_image.image_url.split('/')[-1])
        product_image.delete()
    except Exception as e:
        raise Exception(f"Error removing image: {str(e)}")

def delete_product_and_stl(product_code, seller_id):
    try:
        product = Product.objects.get(code=product_code)
        if product.seller.userId != seller_id:
            return Response({"error": "You do not own this product"}, status=status.HTTP_403_FORBIDDEN)
        if product.stl_file_url:
            stl_file_name = product.stl_file_url.split('/')[-1]
            try:
                remove_file_from_supabase('3d-archives', stl_file_name)
            except Exception as e:
                raise Exception(f"Error removing STL file: {str(e)}")

        for product_image in product.images.all():
            delete_product_image(product_image)

        product.delete()
        return Response({"message": "Product and associated STL file deleted successfully"}, status=status.HTTP_200_OK)

    except Product.DoesNotExist:
        return {"error": "Product not found"}
    except Exception as e:
        return {"error": str(e)}

class MaterialListView(generics.ListAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [AllowAny]

# /api/sellers/<int:userId>/materials/
class SellerMaterialListView(generics.ListAPIView):
    serializer_class = MaterialSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        userId = self.kwargs['userId']
        seller = Seller.objects.get(userId=userId)
        return seller.materials.all()

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

class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    def delete(self, request):
        user = request.user
        # user = User.objects.get(id=50)
        try:

            # Check if the user is a seller
            if hasattr(user, 'seller'):
                seller = user.seller
                # Remove profile picture if exists
                """
                if seller.profile_picture:
                    file_name = seller.profile_picture.split('/')[-1]
                    remove_file_from_supabase('seller-pictures', file_name)
                """
                # Delete the seller
                seller.delete()

            # Delete the user
            user.delete()
            return Response({"message": "User successfully deleted"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#################
#### SELLERS ####
#################
class SellerCreateView(generics.CreateAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # todo CAMBIAR

class SellerDetailView(generics.RetrieveAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [AllowAny]
    lookup_field = 'userId'  # Usamos el campo userId para la búsqueda

class SellerListView(generics.ListAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [AllowAny]

class UpdateProfilePictureView(APIView):
    permission_classes = [IsSeller]

    def post(self, request):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4)
        new_profile_picture = request.FILES.get('profile_picture')

        if not new_profile_picture:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        bucket_name = 'seller-pictures'
        old_profile_picture_url = seller.profile_picture

        # Remove old profile picture if exists
        if old_profile_picture_url:
            old_file_name = old_profile_picture_url.split('/')[-1]
            # old_file_name = f"{seller.userId.id}_profile_picture"
            try:
                remove_file_from_supabase(bucket_name, old_file_name)
            except Exception as e:
                return Response({"error": f"Error removing old profile picture: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Upload new profile picture
        new_file_name = f"{seller.userId.id}_profile_picture"
        try:
            new_file = new_profile_picture.read()
            new_profile_picture_url = upload_file_to_supabase(new_file, bucket_name, new_file_name)
            seller.profile_picture = new_profile_picture_url
            seller.save()
            return Response({"message": "Profile picture updated successfully", "profile_picture_url": new_profile_picture_url}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error uploading new profile picture: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# {"error":"Error uploading new profile picture: expected str, bytes or os.PathLike object, not InMemoryUploadedFile"}
##################
#### PRODUCTS ####
##################
class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

class DeleteProductView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def delete(self, request, product_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4)
        try:
            product = Product.objects.get(code=product_id, seller=seller)
            product.delete()
            return Response({"message": "Product deleted successfully"}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found or you do not have permission to delete this product"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer
from rest_framework.permissions import AllowAny
# from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

class ProductSearchView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter] # DjangoFilterBackend
    # filterset_fields = ['material', 'categories__name']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name']

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
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Obtener los productos más vendidos
        return Product.objects.order_by('-stock')[:4]

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = 'code'  # Usamos el campo code para la búsqueda

class ProductDetailWithSellerView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'code'  # Usamos el campo code para la búsqueda

class ProductSellerDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        try:
            product = Product.objects.get(code=product_id)
            seller = product.seller
            seller_data = {
                "userId": seller.userId.id,
                # "username": seller.userId.username,
                "address": seller.address,
                "store_name": seller.store_name,
                "description": seller.description,
                "profile_picture": seller.profile_picture,
            }
            return Response(seller_data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
"""
class DeleteProductView(APIView):
    # permission_classes = [IsSeller]
    permission_classes = [IsSeller] # todo CAMBIAR

    def delete(self, request, product_id):
        try:
            product = Product.objects.get(code=product_id)
            if product.seller.userId == request.user:
            # if True:
                product.delete()
                # todo -> agregar que elimine las imagenes asociadas del bucket
                return Response({"message": "Product deleted successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "You do not own this product"}, status=status.HTTP_403_FORBIDDEN)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
"""

"""
class DeleteProductView(APIView):
    permission_classes = [IsSeller]

    def delete(self, request, product_id):
        try:
            return delete_product_and_stl(product_id, request.user)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    # tod agregar
"""

class IsProductOwnerView(APIView):
    permission_classes = [IsSeller]

    def get(self, request, product_id):
        try:
            product = Product.objects.get(code=product_id)
            user = request.user
            if product.seller.userId == user:
                return Response({"is_owner": True}, status=status.HTTP_200_OK)
            else:
                return Response({"is_owner": False}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)



class UpdateProductStockView(APIView):
    permission_classes = [IsSeller]
    def post(self, request, product_id):
        try:
            product = Product.objects.get(code=product_id)
            user = request.user
            if product.seller.userId == user:
                new_stock = request.data.get('stock')
                if new_stock is not None and isinstance(new_stock, int) and new_stock >= 0:
                    product.stock = new_stock
                    product.save()
                    return Response({"message": "Stock updated successfully"}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Invalid stock value"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "You do not own this product"}, status=status.HTTP_403_FORBIDDEN)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)


##################
#### REQUESTS ####
##################
class CreatePrintRequestView(generics.CreateAPIView):
    queryset = PrintRequest.objects.all()
    serializer_class = PrintRequestSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TOD CAMBIAR !!

"""
class UserPrintRequestListView(generics.ListAPIView):
    serializer_class = PrintRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return PrintRequest.objects.filter(userID=user)
"""
class UserPrintRequestListView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def get(self, request):
        user = request.user
        # user = User.objects.get(id=5)
        # user = User.objects.get(id=29)
        print_requests = PrintRequest.objects.filter(userID=user)

        response_data = [
            {
                "requestID": print_request.requestID,
                "userID": print_request.userID.id,
                "sellerID": print_request.sellerID.userId.id if print_request.sellerID else None,
                "description": print_request.description,
                "quantity": print_request.quantity,
                "material": print_request.material,
                "stl_url": print_request.stl_url,
                "status": print_request.status,
                "price": print_request.price,
                "preference_id": print_request.preference_id,
                # "direccion_del_vendedor": print_request.sellerID.address,
                "direccion_del_vendedor": print_request.sellerID.address if print_request.sellerID else None,
                "seller_name": print_request.sellerID.store_name if print_request.sellerID else None

            }
            for print_request in print_requests
        ]
        return Response(response_data, status=status.HTTP_200_OK)
"""
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
    preference_id
"""

class SellerPrintRequestListView(generics.ListAPIView):
    serializer_class = PrintRequestSerializer
    permission_classes = [IsSeller]

    def get_queryset(self):
        seller = self.request.user.seller
        return PrintRequest.objects.filter(sellerID=seller)


class AcceptOrRejectPrintRequestView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def post(self, request, request_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=4) # TOD CAMBIAR

        try:
            print_request = PrintRequest.objects.get(requestID=request_id, sellerID=sellerID) # sacar sellerID
            # if print_request.sellerID != sellerID:
            #   return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if print_request.status != "Pendiente":
                return Response({"error": "Request has already been responded"}, status=status.HTTP_400_BAD_REQUEST)

            response = request.data.get('response')
            price = request.data.get('price')

            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

            if response == "Accept":
                if not price:
                    return Response({"error": "Price is required when accepting a request"}, status=status.HTTP_400_BAD_REQUEST)
                print_request.status = "Cotizada"
                print_request.price = price
            else:
                print_request.status = "Rechazada"

            print_request.save()
            return Response({"message": f"Request successfully {response.lower()}ed"}, status=status.HTTP_200_OK)
        except PrintRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
import uuid
# TODO!!!
class UserRespondToPrintRequestView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TOD CAMBIAR
    def post(self, request, request_id):
        userID = request.user
        # userID = User.objects.get(id=8) # TOD CAMBIAR

        try:
            print_request = PrintRequest.objects.get(requestID=request_id, userID=userID) # cambiar lo de userID -> manejarlo con un if
            if print_request.status != "Cotizada":
                return Response({"error": "Request is not in a quotable state"}, status=status.HTTP_400_BAD_REQUEST)

            response = request.data.get('response')
            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid response"}, status=status.HTTP_400_BAD_REQUEST)

            if response == "Accept":
                print_request.status = "En Proceso"
                product_id = request_id
                quantity = print_request.quantity
                # quantity = request.get("quantity")
                transaction_amount = print_request.price
                # transaction_amount = request.get("price")
                access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
                sdk = mercadopago.SDK(access_token)
                preference_data = {
                    "items": [
                        {
                            "product_id": int(product_id),
                            "quantity": int(quantity),
                            "unit_price": float(transaction_amount)
                        }
                    ],
                    "back_urls": {
                        "success": "https://3dcapybara.vercel.app/api/sucess",
                        "failure": "https://3dcapybara.vercel.app/api/failure",
                        "pending": "https://www.3dcapybara.vercel.app/api/pending"
                    },
                    "auto_return": "approved",
                    "notification_url": "https://3dcapybara.vercel.app/api/notifications/printrequest",

                }
                try:
                    preference_response = sdk.preference().create(preference_data)
                    preference_id = preference_response["response"]["id"]

                    return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

                except Exception as e:
                    return Response({"error": f"An error occurred while creating the payment preference: {str(e)}"},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                print_request.status = "Cancelada"

            print_request.save()
            return Response({"message": f"Request successfully {response.lower()}ed"}, status=status.HTTP_200_OK)
        except PrintRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class FinalizePrintRequestView(APIView):
    permission_classes = [IsSeller]

    def post(self, request, request_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=4) # TODO CAMBIAR

        try:
            print_request = PrintRequest.objects.get(requestID=request_id, sellerID=sellerID)
            # if print_request.sellerID != sellerID:
            #     return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if print_request.status != "Aceptada":
                return Response({"error": "Request is not in an accepted state"}, status=status.HTTP_400_BAD_REQUEST)

            print_request.status = "Realizada"
            print_request.save()
            return Response({"message": "Request successfully finalized"}, status=status.HTTP_200_OK)
        except PrintRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class MarkAsDeliveredPrintRequestView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def post(self, request, request_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=4) # TODO CAMBIAR

        try:
            print_request = PrintRequest.objects.get(requestID=request_id, sellerID=sellerID)
            if print_request.status != "Realizada":
                return Response({"error": "Request is not in a completed state"}, status=status.HTTP_400_BAD_REQUEST)

            print_request.status = "Entregada"
            print_request.save()
            return Response({"message": "Request successfully marked as delivered"}, status=status.HTTP_200_OK)
        except PrintRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)


class DesignRequestCreateView(generics.CreateAPIView):
    queryset = DesignRequest.objects.all()
    serializer_class = DesignRequestSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

"""
class UserDesignRequestListView(generics.ListAPIView):
    serializer_class = DesignRequestSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def get_queryset(self):
        user = self.request.user
        # user = User.objects.get(id=5)
        return DesignRequest.objects.filter(userID=user)
"""
class UserDesignRequestListView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def get(self, request):
        user = request.user
        # user = User.objects.get(id=5)
        design_requests = DesignRequest.objects.filter(userID=user)

        response_data = [
            {
                "requestID": design_request.requestID,
                "userID": design_request.userID.id,
                "sellerID": design_request.sellerID.userId.id if design_request.sellerID else None,
                "description": design_request.description,
                "quantity": design_request.quantity,
                "material": design_request.material,
                "status": design_request.status,
                "price": design_request.price,
                "preference_id": design_request.preference_id,
                "direccion_del_vendedor": design_request.sellerID.address if design_request.sellerID else None,
                "seller_name": design_request.sellerID.store_name if design_request.sellerID else None,
                "images": [image.image_url for image in design_request.design_images.all()]
            }
            for design_request in design_requests
        ]
        return Response(response_data, status=status.HTTP_200_OK)
"""
class DesignRequest(models.Model):
    sellerID = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True)
    design_images = models.ManyToManyField('DesignRequestImage')
    material = models.CharField(max_length=255, null=True)
   

"""


"""
class UserPrintRequestListView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def get(self, request):
        user = request.user
        # user = User.objects.get(id=5)
        print_requests = PrintRequest.objects.filter(userID=user)

        response_data = [
            {
                "requestID": print_request.requestID,
                "userID": print_request.userID.id,
                "description": print_request.description,
                "quantity": print_request.quantity,
                "material": print_request.material,
                "stl_url": print_request.stl_url,
                "status": print_request.status,
                "price": print_request.price,
                "preference_id": print_request.preference_id,
                "direccion_del_vendedor": print_request.sellerID.address,
                "seller_name": print_request.sellerID.store_name
            
            }
            for print_request in print_requests
        ]
        return Response(response_data, status=status.HTTP_200_OK)
"""

class SellerDesignRequestListView(generics.ListAPIView):
    serializer_class = DesignRequestSerializer
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def get_queryset(self):
        seller = self.request.user.seller
        # seller = Seller.objects.get(userId=18) # TOD CAMBIAR
        return DesignRequest.objects.filter(sellerID=seller)

# TODO
"""
descripción
cantidad
material
"""
"""
necesito que cambies está vista para que a la respuesta se le unan las DesignReverseAuctionResponse x DesignReverseAuction que el seller haya cotizado

campo       | -> |  donde lo consigo
requestID   | -> |  DesignRequest
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
"""

"""
class SellerDesignOrdersListView(generics.ListAPIView)

tiene que hacer una UNION entre las DesignRequests y las DesignReverseAuctions del seller

en SQL sería algo así:
SELECT *
FROM DesignRequests
WHERE sellerID = 1
UNION
SELECT *
FROM DesignReverseAuctions
WHERE sellerID = 1

# falta juntar DesignReverseAuctions con DesignReverseAuctionResponse
# falta renombrar

"""

class AcceptOrRejectDesignRequestView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, request_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=18) # TODO CAMBIAR

        try:
            design_request = DesignRequest.objects.get(requestID=request_id, sellerID=sellerID)
            # if design_request.sellerID != sellerID:
            #     return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if design_request.status != "Pendiente":
                return Response({"error": "Request is not pending"}, status=status.HTTP_400_BAD_REQUEST)

            response = request.data.get('response')
            price = request.data.get('price')

            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid response"}, status=status.HTTP_400_BAD_REQUEST)

            if response == "Accept":
                if not price:
                    return Response({"error": "Price is required when accepting a request"}, status=status.HTTP_400_BAD_REQUEST)
                design_request.status = "Cotizada"
                design_request.price = price
            else:
                design_request.status = "Rechazada"

            design_request.save()
            return Response({"message": f"Request successfully {response.lower()}ed"}, status=status.HTTP_200_OK)
        except DesignRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class UserRespondToDesignRequestView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def post(self, request, request_id):
        userID = request.user
        # userID = User.objects.get(id=8) # TODO CAMBIAR

        try:
            design_request = DesignRequest.objects.get(requestID=request_id, userID=userID)
            if design_request.status != "Cotizada":
                return Response({"error": "Request is not in a quotable state"}, status=status.HTTP_400_BAD_REQUEST)

            response = request.data.get('response')
            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid response"}, status=status.HTTP_400_BAD_REQUEST)

            if response == "Accept":
                design_request.status = "En Proceso"
                product_id = request_id
                quantity = design_request.quantity
                # quantity = request.get("quantity")
                transaction_amount = design_request.price
                # transaction_amount = request.get("price")
                access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
                sdk = mercadopago.SDK(access_token)
                preference_data = {
                    "items": [
                        {
                            "product_id": int(product_id),
                            "quantity": int(quantity),
                            "unit_price": float(transaction_amount)
                        }
                    ],
                    "back_urls": {
                        "success": "https://3dcapybara.vercel.app/api/sucess",
                        "failure": "https://3dcapybara.vercel.app/api/failure",
                        "pending": "https://www.3dcapybara.vercel.app/api/pending"
                    },
                    "auto_return": "approved",
                    "notification_url": "https://3dcapybara.vercel.app/api/notifications/designrequest",

                }
                try:
                    preference_response = sdk.preference().create(preference_data)
                    preference_id = preference_response["response"]["id"]

                    return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

                except Exception as e:
                    return Response({"error": f"An error occurred while creating the payment preference: {str(e)}"},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                design_request.status = "Cancelada"

            design_request.save()
            return Response({"message": f"Request successfully {response.lower()}ed"}, status=status.HTTP_200_OK)
        except DesignRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)


class FinalizeDesignRequestView(APIView):
    permission_classes = [IsSeller]

    def post(self, request, request_id):
        sellerID = request.user.seller

        try:
            design_request = DesignRequest.objects.get(requestID=request_id, sellerID=sellerID)
            # if design_request.sellerID != sellerID:
            #     return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if design_request.status != "Aceptada":
                return Response({"error": "Request is not in an accepted state"}, status=status.HTTP_400_BAD_REQUEST)

            design_request.status = "Realizada"
            design_request.save()
            return Response({"message": "Request successfully finalized"}, status=status.HTTP_200_OK)
        except DesignRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class MarkAsDeliveredDesignRequestView(APIView):
    permission_classes = [IsSeller]

    def post(self, request, request_id):
        sellerID = request.user.seller

        try:
            design_request = DesignRequest.objects.get(requestID=request_id, sellerID=sellerID)
            # if design_request.sellerID != sellerID:
            #     return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if design_request.status != "Realizada":
                return Response({"error": "Request is not in a completed state"}, status=status.HTTP_400_BAD_REQUEST)

            design_request.status = "Entregada"
            design_request.save()
            return Response({"message": "Request successfully marked as delivered"}, status=status.HTTP_200_OK)
        except DesignRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

##########################
#### INVERSE AUCTIONS ####
##########################

class PrintReverseAuctionCreateView(generics.CreateAPIView):
    queryset = PrintReverseAuction.objects.all()
    serializer_class = PrintReverseAuctionSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TODO CAMBIAR

class UserPrintReverseAuctionListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def get_queryset(self):
        user = self.request.user
        # user = User.objects.get(id=142)
        return PrintReverseAuction.objects.filter(userID=user, status="Open")

class OpenPrintReverseAuctionListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return PrintReverseAuction.objects.filter(status="Open")

class CreatePrintReverseAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, auction_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=4) # TODO CAMBIAR
        try:
            auction = PrintReverseAuction.objects.get(requestID=auction_id, status="Open")
        except PrintReverseAuction.DoesNotExist:
            return Response({'error': 'Auction not found or not open'}, status=status.HTTP_404_NOT_FOUND)

        response = request.data.get('response')
        price = request.data.get('price')
        if not price:
            return Response({'error': 'Price is required'}, status=status.HTTP_400_BAD_REQUEST)

        auction.response_count += 1
        auction.save()

        response = PrintReverseAuctionResponse.objects.create(auction=auction, seller=sellerID, price=price)
        return Response({'message': 'Response created successfully', 'response_id': response.responseID}, status=status.HTTP_201_CREATED)

"""
class QuotizedPrintReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionResponseCombinedSerializer
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def get_queryset(self):
        seller = self.request.user.seller
        # seller = Seller.objects.get(userId=4) # TODO CAMBIAR
        return PrintReverseAuctionResponse.objects.select_related('auction').filter(seller=seller, status="Pending")
"""

# class QuotatedPrintOrdersListView(APIView):
class QuotizedPrintReverseAuctionResponseListView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def get(self, request):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=142) # TODO CAMBIAR
        quotated_responses = PrintReverseAuctionResponse.objects.filter(seller=seller, status="Pending")
        printed_requests = PrintRequest.objects.filter(sellerID=seller, status="Cotizada")

        response_data = [
            {
                "userID": response.auction.userID.id,
                "description": response.auction.description,
                "quantity": response.auction.quantity,
                "material": response.auction.material,
                "price": response.price,
                "status": response.status,
                "stl_url": response.auction.stl_file_url,
            }
            for response in quotated_responses
        ]

        response_data += [
            {
                "userID": request.userID.id,
                "description": request.description,
                "quantity": request.quantity,
                "material": request.material,
                "price": request.price,
                "status": request.status,
                "stl_url": request.stl_url,
            }
            for request in printed_requests
        ]

        return Response(response_data, status=status.HTTP_200_OK)


"""
nueva view que retorne las design/print-requests cotizadas, join design/print-reverse-auction

{
    
}


"""


class PrintReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionResponseSerializer
    permission_classes = [AllowAny] # TODO -> ¿lo puede ver cualquiera?

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        return PrintReverseAuctionResponse.objects.filter(auction__requestID=auction_id)

# TODO: Cambiar nombre de la vista a AcceptPrintReverseAuctionResponseView
class AcceptAuctionResponseView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, auction_id, response_id):
        userID = request.user
        # userID = User.objects.get(id=8) # TODO CAMBIAR
        try:
            auction = PrintReverseAuction.objects.get(requestID=auction_id, status="Open", userID=userID)
            response = PrintReverseAuctionResponse.objects.get(responseID=response_id, auction=auction)

            # Aceptar la respuesta indicada
            response.status = "Accepted"
            response.save()

            # Actualizar el accepted_response en la subasta
            auction.accepted_response = response
            auction.status = "Closed"
            auction.save()

            # Rechazar todas las demás respuestas
            PrintReverseAuctionResponse.objects.filter(auction=auction).exclude(responseID=response_id).update(status="Rejected")

            PrintRequest.objects.create(
                userID=auction.userID,
                sellerID=response.seller,
                stl_url=auction.stl_file_url,
                description=auction.description,
                quantity=auction.quantity,
                material=auction.material,
                price=response.price,
                status="Aceptada"
            )

            product_id = auction.requestID
            quantity =  auction.quantity
            transaction_amount = response.price
            access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
            sdk = mercadopago.SDK(access_token)
            preference_data = {
                "items": [
                    {
                        "product_id": int(product_id),
                        "quantity": int(quantity),
                        "unit_price": float(transaction_amount)
                    }
                ],
                "back_urls": {
                    "success": "https://3dcapybara.vercel.app/api/sucess",
                    "failure": "https://3dcapybara.vercel.app/api/failure",
                    "pending": "https://www.3dcapybara.vercel.app/api/pending"
                },
                "auto_return": "approved",
                "notification_url": "https://3dcapybara.vercel.app/api/notifications/printrequest",

            }
            try:
                preference_response = sdk.preference().create(preference_data)
                preference_id = preference_response["response"]["id"]

                return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": f"An error occurred while creating the payment preference: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            #return Response({"message": "Auction response accepted successfully"}, status=status.HTTP_200_OK)
        except PrintReverseAuction.DoesNotExist:
            return Response({"error": "Auction not found or not open"}, status=status.HTTP_404_NOT_FOUND)
        except PrintReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Auction response not found"}, status=status.HTTP_404_NOT_FOUND)


# TODO: Cambiar nombre de la vista a CompletePrintReverseAuctionResponseView
class CompleteAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, response_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4)
        try:
            response = PrintReverseAuctionResponse.objects.get(responseID=response_id, seller=seller, status="Accepted")
            response.status = "Completed"
            response.save()
            response.auction.status = "Completed"
            response.auction.save()
            return Response({"message": "Auction response marked as completed successfully"}, status=status.HTTP_200_OK)
        except PrintReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Accepted auction response not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

# TODO: Cambiar nombre de la vista a DeliverPrintReverseAuctionResponseView
class DeliverAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, response_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4) # TODO CAMBIAR
        try:
            response = PrintReverseAuctionResponse.objects.get(responseID=response_id, seller=seller, status="Completed")
            response.status = "Delivered"
            response.save()
            response.auction.status = "Delivered"
            response.auction.save()

            return Response({"message": "Auction response marked as delivered successfully"}, status=status.HTTP_200_OK)
        except PrintReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Completed auction response not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)


class DesignReverseAuctionCreateView(generics.CreateAPIView):
    queryset = DesignReverseAuction.objects.all()
    serializer_class = DesignReverseAuctionSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TODO CAMBIAR

class UserDesignReverseAuctionListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def get_queryset(self):
        user = self.request.user
        # user = User.objects.get(id=142)
        return DesignReverseAuction.objects.filter(userID=user, status="Open")

class OpenDesignReverseAuctionListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return DesignReverseAuction.objects.filter(status="Open")


class CreateDesignReverseAuctionResponseView(APIView):
    permission_classes = [IsAuthenticated, IsSeller]

    def post(self, request, auction_id):
        sellerID = request.user.seller
        try:
            auction = DesignReverseAuction.objects.get(requestID=auction_id, status="Open")
        except DesignReverseAuction.DoesNotExist:
            return Response({'error': 'Auction not found or not open'}, status=status.HTTP_404_NOT_FOUND)

        response = request.data.get('response')
        price = request.data.get('price')
        if not price:
            return Response({'error': 'Price is required'}, status=status.HTTP_400_BAD_REQUEST)

        auction.response_count += 1
        auction.save()

        response = DesignReverseAuctionResponse.objects.create(auction=auction, seller=sellerID, price=price)
        return Response({'message': 'Response created successfully', 'response_id': response.responseID}, status=status.HTTP_201_CREATED)

class QuotizedDesignReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionResponseCombinedSerializer
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def get_queryset(self):
        seller = self.request.user.seller
        # seller = Seller.objects.get(userId=4)  # TODO CAMBIAR
        # return DesignReverseAuctionResponse.objects.select_related('auction').filter(seller=seller) # TODO CAMBIAR
        return DesignReverseAuctionResponse.objects.select_related('auction').filter(seller=seller, status="Pending")


class DesignReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionResponseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        return DesignReverseAuctionResponse.objects.filter(auction__requestID=auction_id)


class AcceptDesignReverseAuctionResponseView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def post(self, request, auction_id, response_id):
        userID = request.user
        # userID = User.objects.get(id=8) # TOD CAMBIAR
        try:
            auction = DesignReverseAuction.objects.get(requestID=auction_id, status="Open", userID=userID)
            response = DesignReverseAuctionResponse.objects.get(responseID=response_id, auction=auction)

            response.status = "Accepted"
            response.save()

            auction.accepted_response = response
            auction.status = "Closed"
            auction.save()

            DesignReverseAuctionResponse.objects.filter(auction=auction).exclude(responseID=response_id).update(status="Rejected")

            design_request = DesignRequest.objects.create(
                userID=auction.userID,
                sellerID=response.seller,
                description=auction.description,
                quantity=auction.quantity,
                material=auction.material,
                price=response.price,
                status="Aceptada"
            )

            design_request.design_images.set(auction.design_images.all())

            product_id = auction.requestID
            quantity =  auction.quantity
            transaction_amount = response.price
            access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
            sdk = mercadopago.SDK(access_token)
            preference_data = {
                "items": [
                    {
                        "product_id": int(product_id),
                        "quantity": int(quantity),
                        "unit_price": float(transaction_amount)
                    }
                ],
                "back_urls": {
                    "success": "https://3dcapybara.vercel.app/api/sucess",
                    "failure": "https://3dcapybara.vercel.app/api/failure",
                    "pending": "https://www.3dcapybara.vercel.app/api/pending"
                },
                "auto_return": "approved",
                "notification_url": "https://3dcapybara.vercel.app/api/notifications/designrequest",

            }
            try:
                preference_response = sdk.preference().create(preference_data)
                preference_id = preference_response["response"]["id"]

                return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": f"An error occurred while creating the payment preference: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"message": "Auction response accepted successfully"}, status=status.HTTP_200_OK)
        except DesignReverseAuction.DoesNotExist:
            return Response({"error": "Auction not found or not open"}, status=status.HTTP_404_NOT_FOUND)
        except DesignReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Auction response not found"}, status=status.HTTP_404_NOT_FOUND)


class CompleteDesignReverseAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def post(self, request, response_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4) # TOD CAMBIAR
        try:
            response = DesignReverseAuctionResponse.objects.get(responseID=response_id, seller=seller, status="Accepted")
            response.status = "Completed"
            response.save()
            response.auction.status = "Completed"
            response.auction.save()
            return Response({"message": "Auction response marked as completed successfully"}, status=status.HTTP_200_OK)
        except DesignReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Accepted auction response not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class DeliverDesignReverseAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def post(self, request, response_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4) # TOD CAMBIAR
        try:
            response = DesignReverseAuctionResponse.objects.get(responseID=response_id, seller=seller, status="Completed")
            response.status = "Delivered"
            response.save()
            response.auction.status = "Delivered"
            response.auction.save()

            return Response({"message": "Auction response marked as delivered successfully"}, status=status.HTTP_200_OK)
        except DesignReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Completed auction response not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

"""
Crear subasta inversa
/api/print-reverse-auction/create/
POST
JSON a enviar
{
  description,
  quantity,
  material,
}
y archivo STL
"""
"""
Mirar las subastas inversas para impresión que inicie
/api/print-reverse-auction/mine/
GET
te da
{
  requestID,
  description (string/text),
  quantity,
  material, 
  stl_url,
  responses, // cantidad de vendedores que mandaron cotización 
  userID
}
"""

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
        order=serializer.save()
        return Response({"order_id": order.order_id}, status=status.HTTP_201_CREATED)

"""
class UserOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden ver sus órdenes

    def get_queryset(self):
        # Filtrar las órdenes por el usuario autenticado
        user = self.request.user
        return Order.objects.filter(userID=user)
"""

class UserOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        # user = User.objects.get(id=142)
        orders = Order.objects.filter(userID=user)

        response_data = [
            {
                "orderid": order.orderID,
                "productcode": order.productCode.code,
                "quantity": order.quantity,
                "total_price": order.productCode.price * order.quantity,
                "status": order.status,
                "orderdate": order.orderDate,
                "sellerid": order.productCode.seller.userId.id,
                # "seller_email": order.productCode.seller.userId.email,
                "product_name": order.productCode.name,
            }
            for order in orders
        ]
        return Response(response_data, status=status.HTTP_200_OK)

"""
nombre_producto
precio_total
"""

"""
class SellerOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    # permission_classes = [IsSeller]  # Solo vendedores pueden ver sus órdenes
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Filtrar las órdenes por el vendedor autenticado
        # seller = self.request.user.seller
        seller = Seller.objects.get(userId=29)  # TODO CAMBIAR

        return Order.objects.filter(productCode__seller=seller)
"""
class SellerOrderListView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def get(self, request):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=29)  # TODO CAMBIAR

        orders = Order.objects.filter(productCode__seller=seller)
        response_data = [
            {
                "orderid": order.orderID,
                "productcode": order.productCode.code,
                "quantity": order.quantity,
                "total_price": order.productCode.price * order.quantity,
                "status": order.status,
                "orderdate": order.orderDate,
                "userid" : order.userID.id,
                "user_email": order.userID.email,
                "product_name": order.productCode.name
            }
            for order in orders
        ]
        return Response(response_data, status=status.HTTP_200_OK)


###############
#### FILES ####
###############

"""
class FileUploadView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        # file = request.FILES['file']
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_name = "matiasferreroelcolorado"
        bucket_name = 'images'

        try:
            file_url = upload_file_to_supabase(file, bucket_name, file_name)
            return Response({"url": file_url}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_201_CREATED)
            # return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
"""

class FileUploadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get('file')
        # file = request.FILES['file']
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_name = "matiasferreroelcolorado2"
        bucket_name = 'images'

        try:
            # Read the file content
            file_content = file.read()
            file_url = upload_file_to_supabase(file_content, bucket_name, file_name)
            return Response({"url": file_url}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):


        product_id=request.data.get("product_id")
        quantity=request.data.get("quantity")

        product_selected = Product.objects.get(code=product_id)
        transaction_amount = Decimal(product_selected.price) * int(quantity)
        if int(quantity) > product_selected.stock:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)
        if not all([product_id, quantity, transaction_amount]):
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)
        access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
        if not access_token:
            return Response({"error": "Access token must be a valid string."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        sdk = mercadopago.SDK(access_token)

        preference_data = {
            "items": [
                {
                    "product_id": int(product_id),
                    "quantity": int(quantity),
                    "unit_price": float(transaction_amount)
                }
            ],
            "back_urls": {
                "success": "https://3dcapybara.vercel.app/api/mpresponse/sucess",
                "failure": "https://3dcapybara.vercel.app/api/mpresponse/failure",
                "pending": "https://www.3dcapybara.vercel.app/api/mpresponse/pending"
            },
            "auto_return": "approved",
            "notification_url": "https://3dcapybara.vercel.app/api/notifications/order",

        }

        try:
            preference_response = sdk.preference().create(preference_data)
            preference_id = preference_response["response"]["id"]

            order_data = {
                "quantity": quantity,
                "productCode": product_id,
                "preference_id": preference_id
            }

            serializer = OrderSerializer(data=order_data, context={'request': request})
            if serializer.is_valid(raise_exception=True):
                serializer.save()

            return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"An error occurred while creating the payment preference: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MercadoPagoNotificationViewOrder(APIView):
    def post(self, request):
        data = request.data

        payment_status = data.get("data", {}).get("status")
        preference_id = data.get("data", {}).get("id")

        try:
            order = Order.objects.get(preference_id=preference_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        order.status = payment_status
        order.save()

        return Response({"status": "success"}, status=status.HTTP_200_OK)

class MercadoPagoNotificationViewPrintRequest(APIView):
    def post(self, request):
        data = request.data

        payment_status = data.get("data", {}).get("status")
        preference_id = data.get("data", {}).get("id")

        try:
            request = PrintRequest.objects.get(preference_id=preference_id)
        except Order.DoesNotExist:
            return Response({"error": "Request not found."}, status=status.HTTP_404_NOT_FOUND)
        #saracatunga
        request.status="Aceptada"
        request.save()

        return Response({"status": "success"}, status=status.HTTP_200_OK)

class MercadoPagoNotificationViewDesignRequest(APIView):
    def post(self, request):
        data = request.data

        payment_status = data.get("data", {}).get("status")
        preference_id = data.get("data", {}).get("id")

        try:
            request = DesignRequest.objects.get(preference_id=preference_id)
        except Order.DoesNotExist:
            return Response({"error": "Request not found."}, status=status.HTTP_404_NOT_FOUND)

        request.status="Aceptada"
        request.save()

        return Response({"status": "success"}, status=status.HTTP_200_OK)

from ollama import chat

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import ollama  # Ensure the import is correct

import openai


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import openai
from django.conf import settings

class CositoAI(APIView):
    permission_classes = [AllowAny]  # Allow any access to this view

    def post(self, request):
        try:
            user_input = request.data.get('input')

            openai.api_key = settings.OPENAI_API_KEY
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",  # Specify the model
                messages=[
                    {
                        "role": "user",
                        "content": f"¿Cuál es el nombre del producto para la descripción: '{user_input}'?"
                    }
                ],
            )

            product_name = response.choices[0].message['content'].strip()
            return Response({'response': product_name}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

