from django.urls import path
from . import views
from .views import ProductDetailView

urlpatterns = [
    path("seller/", views.SellerCreateView.as_view(), name="seller_create"),
    path("user/data/", views.ReturnUserDataView.as_view(), name="user_data"),
    path('seller/<int:userId>/', views.SellerDetailView.as_view(), name='seller-detail'),
    path('sellers/', views.SellerListView.as_view(), name='seller-list'),  # Nueva URL para listar todos los vendedores
    path('products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/', views.ProductListView.as_view(), name='product-list'),  # Nueva URL para listar todos los productos
    path('products/seller/<int:userId>/', views.SellerProductListView.as_view(), name='seller-product-list'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order-create'),  # Crear una orden
    path('orders/mine/', views.UserOrderListView.as_view(), name='user-order-list'),  # Ver mis órdenes
    path('products/recommended/', views.RecommendedProductListView.as_view(), name='recommended-product-list'),
    path('products/<int:code>/', ProductDetailView.as_view(), name='product-detail'),
]
