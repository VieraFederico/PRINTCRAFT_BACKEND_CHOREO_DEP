from django.urls import path
from . import views

urlpatterns = [
    path("seller/", views.SellerCreateView.as_view(), name="seller_create"),
    path("user/data/", views.ReturnUserDataView.as_view(), name="user_data"),

]