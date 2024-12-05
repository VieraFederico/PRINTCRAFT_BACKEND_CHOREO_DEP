from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist

from .general_imports import *

import mercadopago
from ..models import Product,Order,PrintRequest,DesignRequest
from ..serializers import OrderSerializer
from ..services.mercado_pago_service import MercadoPagoPreferenceService


class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Extract and validate input data
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")

        # Validate product availability and input data
        try:
            product_selected = Product.objects.get(code=product_id)
            transaction_amount = Decimal(product_selected.price) * int(quantity)

            # Stock and input validation
            if int(quantity) > product_selected.stock:
                return Response(
                    {"error": "Insufficient stock"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not all([product_id, quantity, transaction_amount]):
                return Response(
                    {"error": "Missing required fields"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Use the new service for preference creation
            preference_id = MercadoPagoPreferenceService.create_product_preference(
                product_id=product_id,
                quantity=int(quantity),
                transaction_amount=float(transaction_amount),
                success_endpoint="https://3dcapybara.vercel.app/api/mpresponse/success",
                seller_first_name=request.user.first_name,
                seller_last_name=request.user.last_name,
                email=request.user.email
            )

            # Create order with preference ID
            order_data = {
                "quantity": quantity,
                "productCode": product_id,
                "preference_id": preference_id
            }

            serializer = OrderSerializer(data=order_data, context={'request': request})
            if serializer.is_valid(raise_exception=True):
                serializer.save()

            return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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