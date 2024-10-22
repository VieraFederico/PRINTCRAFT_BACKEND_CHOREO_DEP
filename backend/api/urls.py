from django.urls import path
from . import views
from .views import *
urlpatterns = [
    path("seller/", views.SellerCreateView.as_view(), name="seller_create"),
    path("user/data/", views.ReturnUserDataView.as_view(), name="user_data"),
    path('delete-user/', DeleteUserView.as_view(), name='delete-user'),
    path('seller/<int:userId>/', views.SellerDetailView.as_view(), name='seller-detail'),
    path('sellers/', views.SellerListView.as_view(), name='seller-list'),  # Nueva URL para listar todos los vendedores
    path('products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/delete/<int:product_id>/', DeleteProductView.as_view(), name='delete-product'),
    path('products/', views.ProductListView.as_view(), name='product-list'),  # Nueva URL para listar todos los productos
    path('products/seller/<int:userId>/', views.SellerProductListView.as_view(), name='seller-product-list'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order-create'),  # Crear una orden
    path('orders/complete/<int:order_id>/', CompleteOrderView.as_view(), name='complete-order'),
    path('orders/deliver/<int:order_id>/', DeliverOrderView.as_view(), name='deliver-order'),
    path('orders/mine/', views.UserOrderListView.as_view(), name='user-order-list'),  # Ver mis órdenes
    path('seller-orders/', SellerOrderListView.as_view(), name='seller-orders'),
    path('products/recommended/', views.RecommendedProductListView.as_view(), name='recommended-product-list'),
    path('products/<int:code>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    path('payment/', CreatePaymentView.as_view(), name='create-payment'),  # Ruta para crear un pago
    path('products/<int:product_id>/seller/', ProductSellerDetailView.as_view(), name='product-seller-detail'),
    path('seller/update-profile-picture/', UpdateProfilePictureView.as_view(), name='update-profile-picture'),
    path('products/<int:product_id>/delete/', DeleteProductView.as_view(), name='delete-product'),
    path('print-requests/create/', CreatePrintRequestView.as_view(), name='create-print-request'),
    path('print-requests/mine/', UserPrintRequestListView.as_view(), name='user-print-requests'),
    path('print-requests/seller/', SellerPrintRequestListView.as_view(), name='seller-print-requests'),
    path('print-requests/<int:request_id>/accept-or-reject/', AcceptOrRejectPrintRequestView.as_view(), name='accept-or-reject-print-request'),
    path('print-requests/<int:request_id>/user-respond/', UserRespondToPrintRequestView.as_view(), name='user-respond-print-request'),
    path('print-requests/<int:request_id>/finalize/', FinalizePrintRequestView.as_view(), name='finalize-print-request'),
    path('print-requests/<int:request_id>/mark-as-delivered/', MarkAsDeliveredPrintRequestView.as_view(), name='mark-as-delivered-print-request'),
    path('products/<int:product_id>/is_owner/', IsProductOwnerView.as_view(), name='is_product_owner'),
    path('products/<int:product_id>/update_stock/', UpdateProductStockView.as_view(), name='update_product_stock'),
    path('design-requests/create/', DesignRequestCreateView.as_view(), name='design-request-create'),
    path('design-requests/mine/', UserDesignRequestListView.as_view(), name='user-design-requests'),
    path('design-requests/seller/', SellerDesignRequestListView.as_view(), name='seller-design-requests'),
    path('design-requests/<int:request_id>/accept-or-reject/', AcceptOrRejectDesignRequestView.as_view(), name='accept-or-reject-design-request'),
    path('design-requests/<int:request_id>/user-respond/', UserRespondToDesignRequestView.as_view(), name='user-respond-design-request'),
    path('design-requests/<int:request_id>/finalize/', FinalizeDesignRequestView.as_view(), name='finalize-design-request'),
    path('design-requests/<int:request_id>/mark-as-delivered/', MarkAsDeliveredDesignRequestView.as_view(), name='mark-as-delivered-design-request'),
    path('print-reverse-auction/create/', PrintReverseAuctionCreateView.as_view(), name='print-reverse-auction-create'),
    path('print-reverse-auction/mine/', UserPrintReverseAuctionListView.as_view(), name='user-print-reverse-auctions'),
    path('print-reverse-auction/seller/', QuotizedPrintReverseAuctionResponseListView.as_view(), name='seller-print-reverse-auctions'),
    path('print-reverse-auction/open/', OpenPrintReverseAuctionListView.as_view(), name='open-print-reverse-auction-list'),
    path('print-reverse-auction/<int:auction_id>/create-response/', CreatePrintReverseAuctionResponseView.as_view(), name='create-print-reverse-auction-response'),
    path('print-reverse-auction/<int:auction_id>/responses/', PrintReverseAuctionResponseListView.as_view(), name='print-reverse-auction-responses'),
    path('print-reverse-auction/<int:auction_id>/accept-response/<int:response_id>/', AcceptAuctionResponseView.as_view(), name='accept-auction-response'), # TODO: Cambiar nombre de la vista a AcceptPrintReverseAuctionResponseView
    path('print-reverse-auction/response/<int:response_id>/complete/', CompleteAuctionResponseView.as_view(), name='complete-auction-response'), # TODO: Cambiar nombre de la vista a CompletePrintReverseAuctionResponseView
    path('print-reverse-auction/response/<int:response_id>/deliver/', DeliverAuctionResponseView.as_view(), name='deliver-auction-response'), # TODO: Cambiar nombre de la vista a DeliverPrintReverseAuctionResponseView
    path('design-reverse-auction/create/', DesignReverseAuctionCreateView.as_view(), name='design-reverse-auction-create'),
    path('design-reverse-auctions/mine/', UserDesignReverseAuctionListView.as_view(), name='user-design-reverse-auctions'),
    path('design-reverse-auctions/seller/', QuotizedDesignReverseAuctionResponseListView.as_view(), name='seller-design-reverse-auctions'),
    path('design-reverse-auctions/open/', OpenDesignReverseAuctionListView.as_view(), name='open-design-reverse-auctions'),
    path('design-reverse-auctions/<int:auction_id>/create-response/', CreateDesignReverseAuctionResponseView.as_view(), name='create-design-reverse-auction-response'),
    path('design-reverse-auctions/<int:auction_id>/responses/', DesignReverseAuctionResponseListView.as_view(), name='design-reverse-auction-responses'),
    path('design-reverse-auctions/<int:auction_id>/accept-response/<int:response_id>/', AcceptDesignReverseAuctionResponseView.as_view(), name='accept-design-reverse-auction-response'),
    path('design-reverse-auctions/response/<int:response_id>/complete/', CompleteDesignReverseAuctionResponseView.as_view(), name='complete-design-reverse-auction-response'),
    path('design-reverse-auctions/response/<int:response_id>/deliver/', DeliverDesignReverseAuctionResponseView.as_view(), name='deliver-design-reverse-auction-response'),
    path('materials/', MaterialListView.as_view(), name='material-list'),
    path('sellers/<int:userId>/materials/', SellerMaterialListView.as_view(), name='seller-material-list'),
    path('products/detail/<str:code>/', ProductDetailWithSellerView.as_view(), name='product-detail-with-seller'),
    path('notifications/order/', MercadoPagoNotificationViewOrder.as_view(), name='mercado_pago_notifications'),
    path('notifications/printrequest/', MercadoPagoNotificationViewPrintRequest.as_view(), name='mercado_pago_notifications'),
    path('notifications/designrequest/', MercadoPagoNotificationViewDesignRequest.as_view(), name='mercado_pago_notifications'),
    path('cosito/', CositoAI.as_view(), name='cosito_ai'),

    path('cosito-id/', CositoAIID.as_view(), name='cosito_ai'),

]
#