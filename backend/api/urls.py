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
    path('payment/', CreatePaymentView.as_view(), name='create-payment'),  # Ruta para crear un pago
    path('products/<int:product_id>/seller/', ProductSellerDetailView.as_view(), name='product-seller-detail'),
    path('seller/update-profile-picture/', UpdateProfilePictureView.as_view(), name='update-profile-picture'),
    path('products/<int:product_id>/delete/', DeleteProductView.as_view(), name='delete-product'),
    path('print-requests/create/', CreatePrintRequestView.as_view(), name='create-print-request'),
    path('print-requests/mine/', UserPrintRequestListView.as_view(), name='user-print-requests'),
    path('print-requests/seller/', SellerPrintRequestListView.as_view(), name='seller-print-requests'),
    path('print-requests/<int:request_id>/accept-or-reject/', AcceptOrRejectPrintRequestView.as_view(), name='accept-or-reject-print-request'),
    path('print-requests/<int:request_id>/user-respond/', UserRespondToPrintRequestView.as_view(), name='user-respond-print-request'),
    path('print-requests/<int:request_id>/finalize-print-request/', FinalizePrintRequestView.as_view(), name='finalize-print-request'),
    path('print-requests/<int:request_id>/mark-as-delivered-print-request/', MarkAsDeliveredPrintRequestView.as_view(), name='mark-as-delivered-print-request'),
    path('products/<int:product_id>/is_owner/', IsProductOwnerView.as_view(), name='is_product_owner'),
    path('products/<int:product_id>/update_stock/', UpdateProductStockView.as_view(), name='update_product_stock'),
    path('design-requests/create/', DesignRequestCreateView.as_view(), name='design-request-create'),
    path('design-requests/mine/', UserDesignRequestListView.as_view(), name='user-design-requests'),
    path('design-requests/seller/', SellerDesignRequestListView.as_view(), name='seller-design-requests'),
    path('design-requests/<int:request_id>/accept-or-reject/', AcceptOrRejectDesignRequestView.as_view(), name='accept-or-reject-design-request'),
    path('design-requests/<int:request_id>/user-respond/', UserRespondToDesignRequestView.as_view(), name='user-respond-design-request'),
    path('design-requests/<int:request_id>/finalize-design-request/', FinalizeDesignRequestView.as_view(), name='finalize-design-request'),
    path('design-requests/<int:request_id>/mark-as-delivered-design-request/', MarkAsDeliveredDesignRequestView.as_view(), name='mark-as-delivered-design-request'),
    path('materials/', MaterialListView.as_view(), name='material-list'),
    path('sellers/<int:userId>/materials/', SellerMaterialListView.as_view(), name='seller-material-list'),
    path('products/detail/<str:code>/', ProductDetailWithSellerView.as_view(), name='product-detail-with-seller'),
    path('notifications/', MercadoPagoNotificationView.as_view(), name='mercado_pago_notifications'),

]
