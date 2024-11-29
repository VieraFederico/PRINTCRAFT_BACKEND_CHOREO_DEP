from decimal import Decimal
from .general_imports import *

import mercadopago # type: ignore
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
                "marketplace_fee":10
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

class MercadoPagoNotificationViewOrder(APIView):
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

class MercadoPagoNotificationViewPrintRequest(APIView):
    def post(self, request):
        data = request.data

        payment_status = data.get("data", {}).get("status")
        preference_id = data.get("data", {}).get("id")

        try:
            request = PrintRequest.objects.get(preference_id=preference_id)
        except Order.DoesNotExist:
            return Response({"error": "Request not found."}, status=status.HTTP_404_NOT_FOUND)
        #saracatunga
        if payment_status == "approved":
            request.status="Aceptada"
        request.save()

        return Response({"status": "success"}, status=status.HTTP_200_OK)

class MercadoPagoNotificationViewDesignRequest(APIView):
    def post(self, request):
        data = request.data

        payment_status = data.get("data", {}).get("status")
        preference_id = data.get("data", {}).get("id")

        try:
            request = DesignRequest.objects.get(preference_id=preference_id)
        except Order.DoesNotExist:
            return Response({"error": "Request not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment_status == "approved":
            request.status="Aceptada"
        request.save()

        return Response({"status": "success"}, status=status.HTTP_200_OK)
