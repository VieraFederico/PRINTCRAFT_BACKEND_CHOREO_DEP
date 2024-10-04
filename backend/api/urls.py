from django.urls import path
from . import views
from .views import *

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
    path('create_checkout_preference/', CreateCheckoutPreferenceView.as_view(), name='create_checkout_preference'),
    path('products/<int:product_id>/seller/', ProductSellerDetailView.as_view(), name='product-seller-detail'),
    path('seller/update-profile-picture/', UpdateProfilePictureView.as_view(), name='update-profile-picture'),

    # todo agregar
    #     path('products/<int:product_id>/is_owner/', IsProductOwnerView.as_view(), name='is_product_owner'),
    #     path('products/<int:product_id>/update_stock/', UpdateProductStockView.as_view(), name='update_product_stock'),
]
