from django.urls import path

from .views.cosito_views import CositoAIView
from .views.inverse_auction_views import DesignReverseAuctionCreateView, PrintReverseAuctionCreateView, QuotizedDesignReverseAuctionResponseListView, QuotizedPrintReverseAuctionResponseListView, UserDesignReverseAuctionListView, UserPrintReverseAuctionListView
from .views.mp_views import CreatePaymentView, MercadoPagoNotificationViewDesignRequest, MercadoPagoNotificationViewOrder, MercadoPagoNotificationViewPrintRequest
from .views.orders_views import CompleteOrderView, DeliverOrderView, SellerOrderListView, UserOrderListView, \
    OrderCreateView
from .views.product_views import DeleteProductView, IsProductOwnerView, ProductDetailWithSellerView, \
    ProductReviewDetailView, ProductReviewListCreateView, ProductReviewsByProductCodeView, ProductSearchView, \
    UpdateProductStockView, RecommendedProductListView, SellerProductListView, ProductListView, ProductCreateView
from .views.request_views import AcceptOrRejectDesignRequestView, AcceptOrRejectPrintRequestView, CreatePrintRequestView, DesignRequestCreateView, FinalizeDesignRequestView, FinalizePrintRequestView, MarkAsDeliveredDesignRequestView, MarkAsDeliveredPrintRequestView, SellerDesignRequestListView, SellerPrintRequestListView, UserDesignRequestListView, UserPrintRequestListView, UserRespondToDesignRequestView, UserRespondToPrintRequestView
from .views.seller_views import SellerCreateView, SellerDetailView, UpdateProfilePictureView, SellerListView
from .views.toolbox_views import MaterialListView, SellerMaterialListView
from .views.user_views import DeleteUserView, ReturnUserDataView
from . import views
from .views import *


urlpatterns = [
    # Seller-related URLs
    path("seller/", SellerCreateView.as_view(), name="seller_create"),
    path("seller/<int:userId>/", SellerDetailView.as_view(), name="seller-detail"),
    path("sellers/", SellerListView.as_view(), name="seller-list"),
    path("sellers/<int:userId>/materials/", SellerMaterialListView.as_view(), name="seller-material-list"),
    path("seller/update-profile-picture/", UpdateProfilePictureView.as_view(), name="update-profile-picture"),

    # User-related URLs
    path("user/data/", ReturnUserDataView.as_view(), name="user_data"),
    path("delete-user/", DeleteUserView.as_view(), name="delete-user"),

    # Product-related URLs
    path("products/create/", ProductCreateView.as_view(), name="product-create"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:product_id>/", DeleteProductView.as_view(), name="delete-product"),
    path("products/<int:product_id>/update_stock/", UpdateProductStockView.as_view(), name="update_product_stock"),
    path("products/seller/<int:userId>/", SellerProductListView.as_view(), name="seller-product-list"),
    path("products/recommended/", RecommendedProductListView.as_view(), name="recommended-product-list"),
    path("products/<int:code>/", ProductSearchView.as_view(), name="product-detail"),
    path("products/search/", ProductSearchView.as_view(), name="product-search"),
    path("products/detail/<str:code>/", ProductDetailWithSellerView.as_view(), name="product-detail-with-seller"),
    path("products/<int:product_id>/is_owner/", IsProductOwnerView.as_view(), name="is_product_owner"),

    # Order-related URLs
    path("orders/create/", OrderCreateView.as_view(), name="order-create"),
    path("orders/complete/<int:order_id>/", CompleteOrderView.as_view(), name="complete-order"),
    path("orders/deliver/<int:order_id>/", DeliverOrderView.as_view(), name="deliver-order"),
    path("orders/mine/", UserOrderListView.as_view(), name="user-order-list"),
    path("seller-orders/", SellerOrderListView.as_view(), name="seller-orders"),

    # Print Request URLs
    path("print-requests/create/", CreatePrintRequestView.as_view(), name="create-print-request"),
    path("print-requests/mine/", UserPrintRequestListView.as_view(), name="user-print-requests"),
    path("print-requests/seller/", SellerPrintRequestListView.as_view(), name="seller-print-requests"),
    path("print-requests/<int:request_id>/accept-or-reject/", AcceptOrRejectPrintRequestView.as_view(), name="accept-or-reject-print-request"),
    path("print-requests/<int:request_id>/user-respond/", UserRespondToPrintRequestView.as_view(), name="user-respond-print-request"),
    path("print-requests/<int:request_id>/finalize/", FinalizePrintRequestView.as_view(), name="finalize-print-request"),
    path("print-requests/<int:request_id>/mark-as-delivered/", MarkAsDeliveredPrintRequestView.as_view(), name="mark-as-delivered-print-request"),

    # Design Request URLs
    path("design-requests/create/", DesignRequestCreateView.as_view(), name="design-request-create"),
    path("design-requests/mine/", UserDesignRequestListView.as_view(), name="user-design-requests"),
    path("design-requests/seller/", SellerDesignRequestListView.as_view(), name="seller-design-requests"),
    path("design-requests/<int:request_id>/accept-or-reject/", AcceptOrRejectDesignRequestView.as_view(), name="accept-or-reject-design-request"),
    path("design-requests/<int:request_id>/user-respond/", UserRespondToDesignRequestView.as_view(), name="user-respond-design-request"),
    path("design-requests/<int:request_id>/finalize/", FinalizeDesignRequestView.as_view(), name="finalize-design-request"),
    path("design-requests/<int:request_id>/mark-as-delivered/", MarkAsDeliveredDesignRequestView.as_view(), name="mark-as-delivered-design-request"),

    # Reverse Auction URLs
    path("print-reverse-auction/create/", PrintReverseAuctionCreateView.as_view(), name="print-reverse-auction-create"),
    path("print-reverse-auction/mine/", UserPrintReverseAuctionListView.as_view(), name="user-print-reverse-auctions"),
    path("print-reverse-auction/seller/", QuotizedPrintReverseAuctionResponseListView.as_view(), name="seller-print-reverse-auctions"),
    path("design-reverse-auction/create/", DesignReverseAuctionCreateView.as_view(), name="design-reverse-auction-create"),
    path("design-reverse-auctions/mine/", UserDesignReverseAuctionListView.as_view(), name="user-design-reverse-auctions"),
    path("design-reverse-auctions/seller/", QuotizedDesignReverseAuctionResponseListView.as_view(), name="seller-design-reverse-auctions"),

    # Miscellaneous URLs
    path("payment/", CreatePaymentView.as_view(), name="create-payment"),
    path("materials/", MaterialListView.as_view(), name="material-list"),
    path("notifications/order/", MercadoPagoNotificationViewOrder.as_view(), name="mercado_pago_notifications"),
    path("notifications/printrequest/", MercadoPagoNotificationViewPrintRequest.as_view(), name="mercado_pago_notifications"),
    path("notifications/designrequest/", MercadoPagoNotificationViewDesignRequest.as_view(), name="mercado_pago_notifications"),
    path("cosito/", CositoAIView.as_view(), name="cosito_ai"),
    #path("cosito-id/", CositoAIID.as_view(), name="cosito_ai"),
    path("reviews/", ProductReviewListCreateView.as_view(), name="product-review-list-create"),
    path("reviews/<int:pk>/", ProductReviewDetailView.as_view(), name="product-review-detail"),
    path("reviews/product/<int:product_code>/", ProductReviewsByProductCodeView.as_view(), name="product-reviews-by-product-code"),
]
