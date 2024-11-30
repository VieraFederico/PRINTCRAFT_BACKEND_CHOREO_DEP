import mercadopago
from django.conf import settings
import logging
logger = logging.getLogger(__name__)


class MercadoPagoPreferenceService:

    @staticmethod
    def create_preference(product_id:int, quantity:int,transaction_amount:int, notification_endpoint: str):
        try:
            access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
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
                    "success": "https://3dcapybara.vercel.app/api/mpresponse/success",
                    "failure": "https://3dcapybara.vercel.app/api/mpresponse/failure",
                    "pending": "https://3dcapybara.vercel.app/api/mpresponse/pending"
                },
                "auto_return": "approved",
                "notification_url": notification_endpoint,
                "additional_info": {
                    "marketplace_fee": 10  # Consistent marketplace fee
                }
            }
            preference_response = sdk.preference().create(preference_data)
            return preference_response["response"]["id"]

        except Exception as e:
            logger.error(f"MercadoPago Preference Creation Error: {str(e)}")
            raise