import mercadopago
from django.shortcuts import render
from django.contrib.auth.models import User
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

####################
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


class DeleteProductView(APIView):
    permission_classes = [IsSeller]

    def delete(self, request, product_id):
        try:
            return delete_product_and_stl(product_id, request.user)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    # tod agregar


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

class UserPrintRequestListView(generics.ListAPIView):
    serializer_class = PrintRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return PrintRequest.objects.filter(userID=user)

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

class UserRespondToPrintRequestView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TOD CAMBIAR

    def post(self, request, request_id):
        userID = request.user
        # userID = User.objects.get(id=5) # TOD CAMBIAR

        try:
            print_request = PrintRequest.objects.get(requestID=request_id, userID=userID) # cambiar lo de userID -> manejarlo con un if
            if print_request.status != "Cotizada":
                return Response({"error": "Request is not in a quotable state"}, status=status.HTTP_400_BAD_REQUEST)

            response = request.data.get('response')
            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid response"}, status=status.HTTP_400_BAD_REQUEST)

            if response == "Accept":
                print_request.status = "Aceptada"
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


class UserOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden ver sus órdenes

    def get_queryset(self):
        # Filtrar las órdenes por el usuario autenticado
        user = self.request.user
        return Order.objects.filter(userID=user)


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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
import uuid  # Para generar el idempotency key

class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):


        product_id=request.data.get('product_id')
        quantity=request.data.get('quantity')

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
                "success": "https://3dcapybara.vercel.app/api/sucess",
                "failure": "https://3dcapybara.vercel.app/api/failure",
                "pending": "https://www.3dcapybara.vercel.app/api/pending"
            },
            "auto_return": "approved",
            "notification_url": "https://3dcapybara.vercel.app/api/notifications",

        }

        try:
            preference_response = sdk.preference().create(preference_data)
            preference_id = preference_response["response"]["id"]

            order = Order.objects.create(
                userID=request.user,
                quantity=quantity,
                productCode=product_id,
                preference_id = preference_id
            )
            order.save()

            return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": "An error occurred while creating the payment preference."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MercadoPagoNotificationView(APIView):
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