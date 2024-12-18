import time

from django.core.mail import send_mail
import mercadopago
from django.db import transaction

from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import *
from api.services.supabase_client import *
from rest_framework import generics
from .serializers import ProductSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from django.conf import settings
from .models import Product
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.services.mercado_pago_service import MercadoPagoPreferenceService


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
    pagination_class = None

# /api/sellers/<int:userId>/materials/
class SellerMaterialListView(generics.ListAPIView):
    serializer_class = MaterialSerializer
    permission_classes = [AllowAny]
    pagination_class = None

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


class UpdateUserView(APIView):
    # permission_classes = [AllowAny]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = self.request.user
        # user = User.objects.get(id=144)
        data = request.data

        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']

        user.save()
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
    pagination_class = None

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

class SellerReviewsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            seller = Seller.objects.get(userId=user_id)
            reviews = ProductReview.objects.filter(product__seller=seller)
            review_data = [
                {
                    "product": review.product.name,
                    "rating": review.rating,
                    "comment": review.comment,
                    "user": review.user.username,
                    "created_at": review.created_at
                }
                for review in reviews
            ]
            return Response(review_data, status=status.HTTP_200_OK)
        except Seller.DoesNotExist:
            return Response({"error": "Seller not found"}, status=status.HTTP_404_NOT_FOUND)

class SellerRatingView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            seller = Seller.objects.get(userId=user_id)
            if seller.review_count > 0:
                rating = round(seller.review_sum / seller.review_count, 1)
            else:
                rating = 0.0
            return Response({"rating": rating}, status=status.HTTP_200_OK)
        except Seller.DoesNotExist:
            return Response({"error": "Seller not found"}, status=status.HTTP_404_NOT_FOUND)

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
    pagination_class = None

    def get_queryset(self):
        userId = self.kwargs['userId']
        # Obtener el vendedor a partir del userId
        seller = Seller.objects.get(userId=userId)
        # Filtrar productos por el vendedor
        return Product.objects.filter(seller=seller)

class RecommendedProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        # Obtener los productos más vendidos
        return Product.objects.order_by('?')[:4]
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

    def get(self, product_id):
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

class CanReviewProductView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_code):
        if not self.request.user.is_authenticated:
            return Response({"can_review": False}, status=status.HTTP_200_OK)

        user = self.request.user
        # user = User.objects.get(id=142) # TODO CAMBIAR
        has_purchased = OrderProduct.objects.filter(order__userID=user, product__code=product_code).exists()
        return Response({"can_review": has_purchased}, status=status.HTTP_200_OK)

class ProductReviewListCreateView(generics.ListCreateAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # user = User.objects.get(id=142)
        user = self.request.user
        product = serializer.validated_data['product']
        rating = serializer.validated_data['rating']

        # Check if the user has bought the product
        # if not OrderProduct.objects.filter(order__userID=user, product=product).exists():
        #     raise serializers.ValidationError("You can only review products you have purchased.")

        # check that the user has not already reviewed the product
        # if ProductReview.objects.filter(user=user, product=product).exists():
        #     raise serializers.ValidationError("You have already reviewed this product.")

        product.review_count += 1
        product.review_sum += rating
        product.save()

        seller = product.seller
        seller.review_count += 1
        seller.review_sum += rating
        seller.save()
        serializer.save(user=user)


class ProductReviewDetailView(generics.RetrieveAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [AllowAny]

class ProductReviewsByProductCodeView(generics.ListAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        product_code = self.kwargs['product_code']
        return ProductReview.objects.filter(product__code=product_code)


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

class DeletePrintRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, request_id):
        try:
            print_request = PrintRequest.objects.get(requestID=request_id)
            if print_request.userID != self.request.user:
                return Response({"error": "You do not have permission to delete this print request"}, status=status.HTTP_403_FORBIDDEN)

            print_request.delete()
            return Response({"message": "Print request deleted successfully"}, status=status.HTTP_200_OK)

        except PrintRequest.DoesNotExist:
            return Response({"error": "Print request not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


class SellerPrintRequestListView(generics.ListAPIView):
    serializer_class = PrintRequestSerializer
    permission_classes = [IsSeller]
    pagination_class = None

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


# TODO!!!
class UserRespondToPrintRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def refresh_mp_access_token(self,refresh_token):
        url = "https://api.mercadopago.com/oauth/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            'client_id': str(settings.CLIENT_ID),  # Ensure these are set in settings
            'client_secret': str(settings.SECRET_CLIENT),
            "refresh_token": refresh_token
        }
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token", refresh_token)  # Use new refresh token if available

            return access_token, refresh_token
        else:
            print("Error refreshing access token:", response.text)
            return None, None

    def post(self, request, request_id):
        userID = request.user

        try:
            # Retrieve the print request
            print_request = PrintRequest.objects.get(requestID=request_id, userID=userID)

            # Validate the request status
            if print_request.status != "Cotizada":
                return Response({"error": "Request is not in a quotable state"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate the response
            response = request.data.get('response')
            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid response"}, status=status.HTTP_400_BAD_REQUEST)

            # Handle acceptance of the print request
            if response == "Accept":
                try:
                    items = [{
                        "title" : "Print Request",
                        "id": request_id,
                        "quantity": print_request.quantity,
                        "unit_price": float(print_request.price)
                    }]

                    seller = print_request.sellerID
                    access_token, refresh_token = self.refresh_mp_access_token(seller.mp_refresh_token)
                    if not access_token:
                        return Response({"error": "Error refreshing access token."},
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    seller.mp_refresh_token = refresh_token
                    seller.mp_access_token = access_token
                    seller.save()
                    total_amount = print_request.price * print_request.quantity

                    result = MercadoPagoPreferenceService.create_order_preference(
                        items,
                        total_amount,
                        "https://3dcapybara.vercel.app/mpresponse/success_printrequest",
                        access_token
                    )
                    if result:
                        payment_link = result['init_point']
                        preference_id = result['preference_id']

                    print_request.preference_id = preference_id
                    print_request.save()

                    return Response({"payment_link": payment_link}, status=status.HTTP_201_CREATED)

                except Exception as e:
                    return Response(
                        {"error": "An error occurred while creating the payment preference"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            else:
                print_request.status = "Cancelada"
                print_request.save()
                return Response({"message": "Request successfully rejected"}, status=status.HTTP_200_OK)

        except PrintRequest.DoesNotExist:
            return Response(
                {"error": "Request not found or you do not have permission to modify it"},
                status=status.HTTP_404_NOT_FOUND
            )
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


class DeleteDesignRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, request_id):
        try:
            design_request = DesignRequest.objects.get(requestID=request_id, userID=self.request.user)
            design_request.delete()
            return Response({"message": "Design request deleted successfully"}, status=status.HTTP_200_OK)
        except DesignRequest.DoesNotExist:
            return Response({"error": "Design request not found or you do not have permission to delete it"}, status=status.HTTP_404_NOT_FOUND)


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
    pagination_class = None
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

    def refresh_mp_access_token(self,refresh_token):
        url = "https://api.mercadopago.com/oauth/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            'client_id': str(settings.CLIENT_ID),  # Ensure these are set in settings
            'client_secret': str(settings.SECRET_CLIENT),
            "refresh_token": refresh_token
        }
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token", refresh_token)  # Use new refresh token if available

            return access_token, refresh_token
        else:
            print("Error refreshing access token:", response.text)
            return None, None

    def post(self, request, request_id):
        """
        Handle user response to a design request, including payment preference creation.

        This view allows authenticated users to:
        1. Accept or reject a design request
        2. Create a MercadoPago payment preference if accepted
        3. Update the request status accordingly
        """
        # Retrieve the current authenticated user
        userID = request.user

        try:
            # Retrieve the specific design request
            design_request = DesignRequest.objects.get(requestID=request_id, userID=userID)

            # Validate request is in a quotable state
            if design_request.status != "Cotizada":
                return Response(
                    {"error": "Request is not in a quotable state"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate the response type
            response = request.data.get('response')
            if response not in ["Accept", "Reject"]:
                return Response(
                    {"error": "Invalid response"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Handle acceptance of the design request
            if response == "Accept":
                try:
                    items = [{
                        "title": "Design Request",
                        "id": request_id,
                        "quantity": design_request.quantity,
                        "unit_price": float(design_request.price)
                    }]

                    seller = design_request.sellerID

                    access_token, refresh_token = self.refresh_mp_access_token(seller.mp_refresh_token)
                    if not access_token:
                        return Response({"error": "Error refreshing access token."},
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    seller.mp_refresh_token = refresh_token
                    seller.mp_access_token = access_token
                    seller.save()
                    total_amount = design_request.price * design_request.quantity

                    result = MercadoPagoPreferenceService.create_order_preference(
                        items,
                        total_amount,
                        "https://3dcapybara.vercel.app/mpresponse/success_designrequest",
                        access_token
                    )
                    if result:
                        payment_link = result['init_point']
                        preference_id = result['preference_id']

                    design_request.preference_id = preference_id
                    design_request.save()

                    return Response({"payment_link": payment_link}, status=status.HTTP_201_CREATED)

                except Exception as e:
                    # Log the error and return a generic error response
                    return Response(
                        {"error": "An error occurred while creating the payment preference"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # Handle rejection of the design request
            else:
                design_request.status = "Cancelada"
                design_request.save()
                return Response(
                    {"message": "Request successfully rejected"},
                    status=status.HTTP_200_OK
                )

        except DesignRequest.DoesNotExist:
            return Response(
                {"error": "Request not found or you do not have permission to modify it"},
                status=status.HTTP_404_NOT_FOUND
            )

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
    pagination_class = None
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def get_queryset(self):
        user = self.request.user
        # user = User.objects.get(id=142)
        return PrintReverseAuction.objects.filter(userID=user, status="Open")

class OpenPrintReverseAuctionListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionSerializer
    permission_classes = [AllowAny]
    pagination_class = None

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

class DeletePrintReverseAuctionView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, auction_id):
        try:
            auction = PrintReverseAuction.objects.get(requestID=auction_id, userID=self.request.user)
            auction.delete()
            return Response({"message": "Print reverse auction deleted successfully"}, status=status.HTTP_200_OK)
        except PrintReverseAuction.DoesNotExist:
            return Response({"error": "Print reverse auction not found or you do not have permission to delete it"},
                            status=status.HTTP_404_NOT_FOUND)

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

"""
class PrintReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionResponseSerializer
    permission_classes = [AllowAny] # TODO -> ¿lo puede ver cualquiera?

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        return PrintReverseAuctionResponse.objects.filter(auction__requestID=auction_id)
"""
class PrintReverseAuctionResponseListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, auction_id):
        responses = PrintReverseAuctionResponse.objects.filter(auction__requestID=auction_id)

        response_data = [
            {
                "responseID": response.responseID,
                "seller": response.seller.userId.id,
                "price": response.price,
                "status": response.status,
                "created_at": response.created_at,
                # "auction": response.auction.requestID,
                "sellerName": response.seller.store_name,
                "sellerAddress": response.seller.address
            }
            for response in responses
        ]
        return Response(response_data, status=status.HTTP_200_OK)

# TODO: Cambiar nombre de la vista a AcceptPrintReverseAuctionResponseView
class AcceptAuctionResponseView(APIView):
    permission_classes = [IsAuthenticated]
    def refresh_mp_access_token(self,refresh_token):
        url = "https://api.mercadopago.com/oauth/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            'client_id': str(settings.CLIENT_ID),  # Ensure these are set in settings
            'client_secret': str(settings.SECRET_CLIENT),
            "refresh_token": refresh_token
        }
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token", refresh_token)  # Use new refresh token if available

            return access_token, refresh_token
        else:
            print("Error refreshing access token:", response.text)
            return None, None

    def post(self, request, auction_id, response_id):
        try:

            auction = PrintReverseAuction.objects.get(
                requestID=auction_id,
                status="Open",
                userID=request.user
            )

            # Retrieve the specific auction response
            response = PrintReverseAuctionResponse.objects.get(
                responseID=response_id,
                auction=auction
            )

            # Transaction to ensure atomic updates
            with transaction.atomic():
                # Update the accepted response status
                response.status = "Accepted"
                response.save()

                # Update the auction
                auction.accepted_response = response
                auction.status = "Closed"
                auction.save()

                # Reject all other responses for this auction
                PrintReverseAuctionResponse.objects.filter(
                    auction=auction
                ).exclude(
                    responseID=response_id
                ).update(status="Rejected")

                # Create a print request based on the accepted response
                print_request = PrintRequest.objects.create(
                    userID=auction.userID,
                    sellerID=response.seller,
                    stl_url=auction.stl_file_url,
                    description=auction.description,
                    quantity=auction.quantity,
                    status="Cotizada",
                    material=auction.material,
                    price=response.price,
                )

            # Prepare items for MercadoPago preference
            items = [{
                "title": "Dummy Title",
                "id": print_request.requestID,
                "quantity": auction.quantity,
                "unit_price": float(response.price)
            }]


            try:
                print_request = auction.print_request
                seller = print_request.sellerID

                access_token, refresh_token = self.refresh_mp_access_token(seller.mp_refresh_token)
                if not access_token:
                    return Response({"error": "Error refreshing access token."},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                seller.mp_refresh_token = refresh_token
                seller.mp_access_token = access_token
                seller.save()
                total_amount = auction.price * auction.quantity

                result = MercadoPagoPreferenceService.create_order_preference(
                    items,
                    total_amount,
                    "https://3dcapybara.vercel.app/mpresponse/success_printrequest",
                    access_token
                )
                if result:
                    payment_link = result['init_point']
                    preference_id = result['preference_id']

                print_request.preference_id = preference_id
                print_request.save()

                return Response({"payment_link": payment_link}, status=status.HTTP_201_CREATED)

            except Exception as e:
                # Log the error and return a generic error response
                return Response(
                    {"error": "An error occurred while creating the payment preference"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except PrintReverseAuction.DoesNotExist:
            return Response(
                {"error": "Auction not found or not open"},
                status=status.HTTP_404_NOT_FOUND
            )
        except PrintReverseAuctionResponse.DoesNotExist:
            return Response(
                {"error": "Auction response not found"},
                status=status.HTTP_404_NOT_FOUND
            )
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

class DeleteDesignReverseAuctionView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, auction_id):
        try:
            auction = DesignReverseAuction.objects.get(requestID=auction_id, userID=self.request.user)
            auction.delete()
            return Response({"message": "Design reverse auction deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except DesignReverseAuction.DoesNotExist:
            return Response({"error": "Design reverse auction not found or you do not have permission to delete it"}, status=status.HTTP_404_NOT_FOUND)

class UserDesignReverseAuctionListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def get_queryset(self):
        user = self.request.user
        return DesignReverseAuction.objects.filter(userID=user, status="Open")

class OpenDesignReverseAuctionListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionSerializer
    permission_classes = [AllowAny]
    pagination_class = None

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

"""
class QuotizedDesignReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionResponseCombinedSerializer
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def get_queryset(self):
        seller = self.request.user.seller
        # seller = Seller.objects.get(userId=4)  # TODO CAMBIAR
        # return DesignReverseAuctionResponse.objects.select_related('auction').filter(seller=seller) # TODO CAMBIAR
        return DesignReverseAuctionResponse.objects.select_related('auction').filter(seller=seller, status="Pending")
"""
class QuotizedDesignReverseAuctionResponseListView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def get(self, request):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=142) # TODO CAMBIAR
        quotated_responses = DesignReverseAuctionResponse.objects.filter(seller=seller, status="Pending")
        quotated_requests = DesignRequest.objects.filter(sellerID=seller, status="Cotizada")

        response_data = [
            {
                "userID": response.auction.userID.id,
                "description": response.auction.description,
                "quantity": response.auction.quantity,
                "material": response.auction.material,
                "price": response.price,
                "status": response.status,
                "images": [image.image_url for image in response.auction.design_images.all()]
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
                "images": [image.image_url for image in request.design_images.all()]
            }
            for request in quotated_requests
        ]

        return Response(response_data, status=status.HTTP_200_OK)

"""
class DesignReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionResponseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        return DesignReverseAuctionResponse.objects.filter(auction__requestID=auction_id)

"""
class DesignReverseAuctionResponseListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, auction_id):
        responses = DesignReverseAuctionResponse.objects.filter(auction__requestID=auction_id)

        response_data = [
            {
                "responseID": response.responseID,
                "seller": response.seller.userId.id,
                "price": response.price,
                "status": response.status,
                "created_at": response.created_at,
                # "auction": response.auction.requestID,
                "sellerName": response.seller.store_name,
                "sellerAddress": response.seller.address
            }
            for response in responses
        ]
        return Response(response_data, status=status.HTTP_200_OK)


class AcceptDesignReverseAuctionResponseView(APIView):
    permission_classes = [IsAuthenticated]
    def refresh_mp_access_token(self,refresh_token):
        url = "https://api.mercadopago.com/oauth/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            'client_id': str(settings.CLIENT_ID),  # Ensure these are set in settings
            'client_secret': str(settings.SECRET_CLIENT),
            "refresh_token": refresh_token
        }
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token", refresh_token)  # Use new refresh token if available

            return access_token, refresh_token
        else:
            print("Error refreshing access token:", response.text)
            return None, None

    def post(self, request, auction_id, response_id):
        """
        Handle the acceptance of a design reverse auction response.

        This view provides a comprehensive workflow for:
        1. Validating the auction and response
        2. Updating auction and response statuses
        3. Creating a design request
        4. Generating a MercadoPago payment preference

        Key steps involve:
        - Ensuring the auction is open and belongs to the current user
        - Accepting the chosen response
        - Rejecting other responses
        - Creating a design request with associated images
        - Generating a payment preference
        """
        try:
            # Retrieve the auction, ensuring it's open and belongs to the current user
            auction = DesignReverseAuction.objects.get(
                requestID=auction_id,
                status="Open",
                userID=request.user
            )

            # Retrieve the specific auction response
            response = DesignReverseAuctionResponse.objects.get(
                responseID=response_id,
                auction=auction
            )

            # Use atomic transaction to ensure database consistency
            with transaction.atomic():
                # Update the accepted response status
                response.status = "Accepted"
                response.save()

                # Close the auction and set the accepted response
                auction.accepted_response = response
                auction.status = "Closed"
                auction.save()

                # Reject all other responses for this auction
                DesignReverseAuctionResponse.objects.filter(
                    auction=auction
                ).exclude(
                    responseID=response_id
                ).update(status="Rejected")

                # Create a design request based on the accepted response
                design_request = DesignRequest.objects.create(
                    userID=auction.userID,
                    sellerID=response.seller,
                    description=auction.description,
                    quantity=auction.quantity,
                    material=auction.material,
                    status="Cotizada",
                    price=response.price,
                )

                # Copy design images from the auction to the design request
                design_request.design_images.set(auction.design_images.all())

            # Prepare items for MercadoPago preference

            items = [
            {
                "title": "Nombre del producto",
                "id": auction.requestID,
                "quantity": auction.quantity,  # Cantidad del producto
                "unit_price": float(response.price),  # Precio unitario
                "currency_id": "ARS"  # Moneda
            }
            ]

            try:
                design_request = auction.design_request
                seller = design_request.sellerID

                access_token, refresh_token = self.refresh_mp_access_token(seller.mp_refresh_token)
                if not access_token:
                    return Response({"error": "Error refreshing access token."},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                seller.mp_refresh_token = refresh_token
                seller.mp_access_token = access_token
                seller.save()
                total_amount = auction.price * auction.quantity

                result = MercadoPagoPreferenceService.create_order_preference(
                    items,
                    total_amount,
                    "https://3dcapybara.vercel.app/mpresponse/success_designrequest",
                    access_token
                )

                if result:
                    payment_link = result['init_point']
                    preference_id = result['preference_id']

                design_request.preference_id = preference_id
                design_request.save()

                return Response({"payment_link": payment_link}, status=status.HTTP_201_CREATED)

            except Exception as e:
                # Log the error and return a generic error response
                return Response(
                    {"error": "An error occurred while creating the payment preference"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except DesignReverseAuction.DoesNotExist:
            return Response(
                {"error": "Auction not found or not open"},
                status=status.HTTP_404_NOT_FOUND
            )
        except DesignReverseAuctionResponse.DoesNotExist:
            return Response(
                {"error": "Auction response not found"},
                status=status.HTTP_404_NOT_FOUND
            )
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


################
#### ORDERS ####
################
class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # user = User.objects.get(id=142)
        user = self.request.user
        serializer.save(userID=user)




"""
class UserOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden ver sus órdenes

    def get_queryset(self):
        # Filtrar las órdenes por el usuario autenticado
        user = self.request.user
        return Order.objects.filter(userID=user)
"""
class CompleteOrderView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def post(self, request, order_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=142)


        try:
            order = Order.objects.get(orderID=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found or you do not have permission to modify it"},
                status=status.HTTP_404_NOT_FOUND
            )

        order_product_exists = OrderProduct.objects.filter(
            order=order,
            product__seller=seller
        ).exists()

        if not order_product_exists:
            return Response(
                {"error": "Order not found or you do not have permission to modify it"},
                status=status.HTTP_404_NOT_FOUND
            )

        order.status = "Completada"
        order.save()
        return Response({"message": "Order marked as completed successfully"}, status=status.HTTP_200_OK)

class DeliverOrderView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def post(self, request, order_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=142)
        try:
            order = Order.objects.get(orderID=order_id)
            if not OrderProduct.objects.filter(order=order, product__seller=seller).exists():
                return Response( {"error": "Order not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND )
            order.status = "Entregada"
            order.save()
            return Response({"message": "Order marked as delivered successfully"}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

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
class UserOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        orders = Order.objects.filter(userID=user)

        response_data = []
        for order in orders:
            first_order_product = order.order_products.first()
            seller = first_order_product.product.seller if first_order_product else None

            order_data = {
                "orderid": order.orderID,
                "status": order.status,
                "orderdate": order.orderDate,
                "store_name": seller.store_name if seller else None,
                "address": seller.address if seller else None,
                "total_price": sum(
                    op.product.price * op.quantity for op in order.order_products.all()
                ),
                "products": [
                    {
                        "productcode": op.product.code,
                        "product_name": op.product.name,
                        "quantity": op.quantity,
                        "price_per_unit": op.product.price,
                    }
                    for op in order.order_products.all()
                ],
            }
            response_data.append(order_data)

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
"""
class SellerOrderListView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def get(self, request):
        # Obtener el vendedor del usuario autenticado
        seller = request.user.seller
        # seller = Seller.objects.get(userId=156)  # TODO CAMBIAR

        # Filtrar las órdenes que contienen productos del vendedor
        orders = Order.objects.filter(order_products__product__seller=seller).exclude(status="En proceso").distinct().select_related("userID")

        # Crear la respuesta
        response_data = []
        for order in orders:
            # Obtener los productos asociados a esta orden
            products = order.order_products.select_related("product").all()

            # Crear la lista de productos
            product_list = [
                {
                    "productcode": product.product.code,
                    "product_name": product.product.name,
                    "quantity": product.quantity,
                    "price": product.product.price,
                    "total_price": product.product.price * product.quantity,
                }
                for product in products
            ]

            # Agregar los datos de la orden con la lista de productos
            response_data.append({
                "orderid": order.orderID,
                "orderdate": order.orderDate,
                "status": order.status,
                "userid": order.userID.id if order.userID else None,
                "user_email": order.userID.email if order.userID else None,
                "products": product_list,
            })

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


import logging
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

class CreateOrderPaymentView(APIView):
    permission_classes = [AllowAny]

    def refresh_mp_access_token(self,refresh_token):
        url = "https://api.mercadopago.com/oauth/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            'client_id': str(settings.CLIENT_ID),  # Ensure these are set in settings
            'client_secret': str(settings.SECRET_CLIENT),
            "refresh_token": refresh_token
        }
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token", refresh_token)  # Use new refresh token if available

            return access_token, refresh_token
        else:
            print("Error refreshing access token:", response.text)
            return None, None

    def post(self, request):
        order_products = request.data.get("order_products")
        if not order_products:
            return Response({"error": "The order must contain at least one product."},status=status.HTTP_400_BAD_REQUEST)
        items = []
        total_amount = 0
        seller = None
        
        for item in order_products:
            quantity = item.get('quantity')
            id = item.get('product')
            
            if not quantity or not id:
                return Response({"error": "The order must contain at least one product with quantity and id."},status=status.HTTP_400_BAD_REQUEST)
            try:
                product = Product.objects.get(code=id)
            except Product.DoesNotExist:
                return Response({"error": f"Product with ID {id} not found."},status=status.HTTP_404_NOT_FOUND)

            if product.stock < int(quantity):
                return Response({"error": f"Not enough stock for product {product.name}."},status=status.HTTP_400_BAD_REQUEST)

            if seller is None:
                seller = product.seller

            items.append(
                {
                    "title": product.name,
                    "quantity": quantity,
                    "currency_id": "ARS",
                    "unit_price": float(product.price),
                }
            )
            total_amount += product.price * quantity

        access_token, refresh_token = self.refresh_mp_access_token(seller.mp_refresh_token)
        if not access_token:
            return Response({"error": "Error refreshing access token."},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        seller.mp_refresh_token=refresh_token
        seller.mp_access_token=access_token
        seller.save()

        result  = MercadoPagoPreferenceService.create_order_preference(items,total_amount,"https://3dcapybara.vercel.app/mpresponse/success_order/",access_token)
        if result:
            payment_link = result['init_point']
            preference_id = result['preference_id']
        order_data = {
                "order_products": order_products,
                "preference_id": preference_id,
                "price": total_amount,
                "sellerID": seller,
        }
        serializer = OrderSerializer(data=order_data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response({"payment_link": payment_link, 'preference_id': preference_id}, status=status.HTTP_201_CREATED)


class BaseMercadoPagoSuccessView(APIView):
    permission_classes = [AllowAny]
    model = None
    status_mapping = {
        "approved": "Aceptada",
        "cancelled": "Cancelada",
        "rejected": "Cancelada"
    }

    def send_notifications(self, request, instance):
        seller = instance.sellerID
        print(seller)
        seller_email = seller.mp_mail
        print(seller_email)
        if self.model == Order:
            return self.send_order_notifications(instance,seller_email)
        elif self.model in [PrintRequest, DesignRequest]:
            return self.send_request_notifications(instance, seller_email)
        else:
            return Response(
                {"error": "Unknown model for notification"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    def send_email_notification(self, email, subject, message):
        send_mail(
            subject=subject,
            message=message,
            from_email='3dcapybararesponse@gmail.com',
            recipient_list=[email],
            fail_silently=False,
    )

    def send_order_notifications(self, instance, seller_email):
        print("Entre al order notification!")
        seller_message = f"¡Felicidades! Uno o más productos tuyos han sido vendidos. ID de orden: {instance.orderID}. Total ganado: ${instance.price}.\n"
        print(seller_message)
        self.send_email_notification(seller_email, "Nueva venta confirmada", seller_message)
        return Response({"message": "Order notifications sent successfully"}, status=status.HTTP_200_OK)

    def send_request_notifications(self, instance, seller_email):
        seller_message = f"Tienes una nueva solicitud. ID: {instance.id}.\n\nDescripción: {instance.description}\nPrecio: ${instance.price}"
        if self.model == PrintRequest:
            self.send_email_notification(seller_email, "Nueva solicitud de impresión", seller_message)
        else:
            self.send_email_notification(seller_email, "Nueva solicitud de diseño", seller_message)

        return Response({"message": "Request notifications sent successfully"}, status=status.HTTP_200_OK)

    def post(self,request):
        if not self.model:
            return Response(
                {"error": "Model not configured for notification view"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        data = request.data
        payment_status = data.get("data", {}).get("status")
        preference_id = data.get("data", {}).get("id")
        try:
            instance = self.model.objects.get(preference_id=preference_id)
            instance.status = self.status_mapping.get(
                payment_status,
                payment_status
            )
            instance.save()
            self.send_notifications(request, instance)
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except self.model.DoesNotExist:
            return Response({"error": "No matching request or order found."}, status=status.HTTP_404_NOT_FOUND)


class MercadoPagoSuccessViewOrder(BaseMercadoPagoSuccessView):
    model = Order

class MercadoPagoSuccessViewPrintRequest(BaseMercadoPagoSuccessView):
    model = PrintRequest

class MercadoPagoSuccessViewDesignRequest(BaseMercadoPagoSuccessView):
    model = DesignRequest


import cohere

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import logging
import requests

from api.models import Product, Category


class RecommendationEngine:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.huggingface_token = settings.HUGGINGFACE_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.huggingface_token}",
            "Content-Type": "application/json"
        }
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.logger = logging.getLogger('recommendation_system')
        self.metrics = RecommendationMetrics()
        self._test_model_access()

    def _test_model_access(self):
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Hugging Face model or token validation failed: {e}")
            raise ValueError("Invalid Hugging Face API Token or Model Name.")

    def get_similarity_score(self, key, item):
        try:
            payload = {
                "inputs": {
                    "source_sentence": key,
                    "sentences": [item]
                }
            }
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 400:
                self.logger.error(f"Bad Request: {response.text}")
                return None

            response.raise_for_status()
            result = response.json()

            print(f"Input: {key} vs {item}")
            print(f"Result: {result}")

            if isinstance(result, list) and len(result) > 0:
                similarity_score = result[0]
                print(f"Similarity score between '{key}' and '{item}': {similarity_score}")
                return similarity_score

            self.logger.error(f"Unexpected response format: {result}")
            return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error during similarity calculation: {e}")
            return None

    def calculate_semantic_similarity(self, query_embedding, item_embedding):
        return np.dot(query_embedding, item_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(item_embedding))

    def find_best_category(self, user_input):
        categories = Category.objects.all()
        products = Product.objects.all()
        print(f"Total Categories: {categories.count()}")
        print(f"Total Product: {products.count()}")

        if not categories.exists():
            return None

        user_embedding = self.get_embedding(user_input)

        category_similarities = []
        for category in categories:
            try:
                category_embedding = self.get_embedding(category)
                similarity = self.calculate_semantic_similarity(user_embedding, category_embedding)
                category_similarities.append((category, similarity))
            except Exception as e:
                print(f"Error processing category {category.name}: {e}")

        if not category_similarities:
            print("No category similarities calculated!")
            return None

        return max(category_similarities, key=lambda x: x[1])[0]

    def recommend_products(self, user_input, confidence_threshold=0.2):
        try:
            #selected_category = self.find_best_category(user_input)

            products = Product.objects.all()

            product_scores = []
            for product in products:
                similarity = self.get_similarity_score(user_input,product.name)
                product_scores.append((product, similarity))

            confident_recommendations = [
                (product, similarity)

                for product, similarity in product_scores
                if similarity > confidence_threshold
            ]

            sorted_recommendations = sorted(
                confident_recommendations,
                key=lambda x: x[1],
                reverse=True
            )

            recommendation_result = {
                'top_recommendation': sorted_recommendations[0][0] if sorted_recommendations else None,
                'alternatives': [rec[0] for rec in sorted_recommendations[1:10]] if len(sorted_recommendations) > 1 else [],
                'confidence_level': (len(confident_recommendations) / len(product_scores) if product_scores else 0)
            }

            # Update metrics
            self.metrics.update_metrics(recommendation_result['confidence_level'])

            return recommendation_result

        except Exception as e:
            self.logger.error(f"Recommendation error: {str(e)}")
            return None

class RecommendationMetrics:
    CONFIDENCE_THRESHOLD = 0.2

    def __init__(self):
        self.total_recommendations = 0
        self.successful_recommendations = 0
        self.average_confidence = 0

    def update_metrics(self, confidence_score):
        if not isinstance(confidence_score, (int, float)):
            self.logger.error(f"Invalid confidence score: {confidence_score}")
        self.total_recommendations += 1
        self.successful_recommendations += 1 if confidence_score > self.CONFIDENCE_THRESHOLD else 0

        # Running average of confidence
        self.average_confidence = (self.average_confidence * (
                self.total_recommendations - 1) + confidence_score) / self.total_recommendations

        # Running average of confidence
        self.average_confidence = (self.average_confidence * (
                    self.total_recommendations - 1) + confidence_score) / self.total_recommendations


class CositoAIView(APIView):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recommendation_engine = RecommendationEngine()

    def post(self, request):
        try:
            user_input = request.data.get('input')
            co = cohere.Client(settings.COHERE_API_KEY)

            if not user_input:
                return Response({'error': 'No input provided'}, status=status.HTTP_400_BAD_REQUEST)

            prompt_mode = (
                f"You are a versatile assistant. Your first task is to determine the user's intent. "
                f"If the user input is requesting a product recommendation, respond only with the word 'recomend'. "
                f"If the user input is simply trying to chat or engage in conversation, respond only with the word 'chatbot'. "
                f"The user has described their query as: '{user_input}'. "
                f"Determine the intent concisely and respond accordingly."
            )

            cohere_response = co.generate(
                model='command-xlarge-nightly',
                prompt=prompt_mode,
                max_tokens=100,
                temperature=0.5
            )

            cosito_mode = cohere_response.generations[0].text.strip()
            if cosito_mode=='recomend':
                recommendations = self.recommendation_engine.recommend_products(user_input)

                if recommendations:
                    prompt = (
                        f"You are a product recommendation system. Your task is to identify the most relevant product from the following list: {recommendations}. "
                        f"The user has described what they are looking for as: '{user_input}'. "
                        f"Match the user's description to the listed products based solely on their name, description, or material. "
                        f"If none of the products in the list exactly match the user's description, prioritize products that belong to the same general category as the user's input. "
                        f"Do not recommend products, categories, or options that are not explicitly listed. "
                        f"Avoid selecting irrelevant products or names that do not have any clear connection to the user's request. "
                        f"If no products match even by category, respond with: 'No suitable match found.' "
                        f"Do not suggest searching for other categories or products outside this list. "
                        f"Respond in the same language as the user's input. "
                        f"Keep your response concise and factual."
                        f"Additionally, if the user asks for family relationships (like 'son of X'), focus on the most likely individual based on those relationships, not on general descriptors."
                    )
                    print(recommendations)
                    cohere_response = co.generate(
                        model='command-xlarge-nightly',
                        prompt=prompt,
                        max_tokens=100,
                        temperature=0.5
                    )

                    generated_text = cohere_response.generations[0].text.strip()

                    prompt_name = (
                        f"Your Task is to Look at this look of recommendations: {recommendations} and extract the name of the product from '{generated_text}' that is in both things."
                        f"You will ONLY answer the name of the product, case and space sensitive, nothing else."
                    )

                    product_name_response = co.generate(
                        model='command-xlarge-nightly',
                        prompt=prompt_name,
                        max_tokens=100,
                        temperature=0.5
                    )
                    product_name = product_name_response.generations[0].text.strip()

                    print(product_name)

                    return Response(
                    {
                            'output': generated_text,
                            'product_id': Product.objects.filter(name=product_name).values_list('code', flat=True).first()
                        },
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {'message': 'No matching products found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                prompt = (
                    f"You are a friendly and engaging chatbot. Your purpose is to have a natural, free-flowing conversation with the user. "
                    f"Respond to the user input: '{user_input}' with curiosity, humor, or thoughtful remarks, as appropriate to the tone. "
                    f"Focus on making the interaction enjoyable and human-like. "
                    f"Do not recommend products or services unless explicitly asked for. "
                    f"Keep your responses concise but engaging, and respond in the same language as the user."
                )
                cohere_response = co.generate(
                    model='command-xlarge-nightly',
                    prompt=prompt,
                    max_tokens=100,
                    temperature=0.5
                )

                generated_text = cohere_response.generations[0].text.strip()

                return Response(
                    {'output': generated_text},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            # Log unexpected errors
            logging.error(f"Recommendation system error: {str(e)}")
            return Response(
                {'error': 'Internal recommendation error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from django.views import View
from django.http import HttpResponse
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

class TestEmailView(View):
    def get(self, request):
        try:
            send_mail(
                'Test Email Subject',
                'This is a test email from Django.',
                '3dcapybararesponse@gmail.com',  # Use the email from settings
                ['estebanthequito@gmail.com'],  # Replace with an email you can check
                fail_silently=False
            )
            return HttpResponse("Email sent successfully!")
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return HttpResponse(f"Error sending email: {str(e)}")