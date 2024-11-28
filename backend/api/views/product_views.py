from general_imports import *

from rest_framework import generics
from ..models.models import Product
from ..serializers import ProductSerializer
from rest_framework.permissions import AllowAny
# from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from models import Product


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
        # if not Order.objects.filter(userID=user, productCode=product).exists():
        #     raise serializers.ValidationError("You can only review products you have purchased.")

        # check that the user has not already reviewed the product
        # if ProductReview.objects.filter(user=user, product=product).exists():
        #     raise serializers.ValidationError("You have already reviewed this product.")

        product.review_count += 1
        product.review_sum += rating
        product.save()
        serializer.save(user=user)


class ProductReviewDetailView(generics.RetrieveAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [AllowAny]

class ProductReviewsByProductCodeView(generics.ListAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        product_code = self.kwargs['product_code']
        return ProductReview.objects.filter(product__code=product_code)



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

