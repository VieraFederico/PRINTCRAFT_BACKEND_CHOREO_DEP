import mercadopago
from django.conf import settings
import logging

from h11 import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class MercadoPagoPreferenceService:

    @staticmethod
    def create_preference(product_id:int, quantity:int,transaction_amount:int, success_endpoint: str, notification_endpoint: str):
        try:
            access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
            if not access_token: return Response({"error": "Access token not configured."},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                    "success": success_endpoint,
                    "failure": "https://3dcapybara.vercel.app/api/mpresponse/failure",
                    "pending": "https://3dcapybara.vercel.app/api/mpresponse/pending"
                },
                "auto_return": "approved",
                "notification_url": notification_endpoint,
                "additional_info": {
                    "marketplace_fee": (int(quantity)*float(transaction_amount)*0.1)
                }
            }
            preference_response = sdk.preference().create(preference_data)
            return preference_response["response"]["id"]

        except Exception as e:
            logger.error(f"MercadoPago Preference Creation Error: {str(e)}")
            raise