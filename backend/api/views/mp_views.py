from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist

from .general_imports import *

import mercadopago
from ..models import Product,Order,PrintRequest,DesignRequest
from ..serializers import OrderSerializer


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
        seller_data ={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
                "type": "business"
            }
        seller_response = sdk.user().create_seller_payment(seller_data) #Generate data
        seller_id =  seller_response["body"]["id"]

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
            "additional_info": {
                "marketplace": "3D CAPYBARA",
                "marketplace_fee": 10,
                "seller_id": seller_id
            }
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

class BaseMercadoPagoNotificationView(APIView):
    model = None
    status_mapping = {
        "approved": "Aceptada",
        "cancelled": "Cancelada",
        "rejected": "Cancelada"
    }
    def post(self, request):
        if not self.model:
            return Response(
                {"error": "Model not configured for notification view"},status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        data = request.data
        payment_status = data.get("data", {}).get("status")
        preference_id = data.get("data", {}).get("id")

        try:
            instance = self.model.objects.get(preference_id=preference_id)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"{self.model.__name__} not found."}, status=status.HTTP_404_NOT_FOUND
            )
        instance.status = self.status_mapping.get(
            payment_status,
            payment_status
        )
        instance.save()

        return Response({"status": "success"}, status=status.HTTP_200_OK)


class MercadoPagoNotificationViewOrder(BaseMercadoPagoNotificationView):
    model = Order

class MercadoPagoNotificationViewPrintRequest(BaseMercadoPagoNotificationView):
    model = PrintRequest

class MercadoPagoNotificationViewDesignRequest(BaseMercadoPagoNotificationView):
    model = DesignRequest