from typing import List

import mercadopago
from django.conf import settings
import logging

from h11 import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class MercadoPagoPreferenceService:


    @staticmethod
    def create_product_preference(product_id: int, quantity: int, transaction_amount: float, success_endpoint: str):
        try:
            access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
            if not access_token:
                logger.error("Access token for MercadoPago is missing.")
                raise RuntimeError("Access token is not configured.")

            sdk = mercadopago.SDK(access_token)

            # Generate seller ID
          #  seller_id = MercadoPagoPreferenceService.create_seller_id(seller_first_name, seller_last_name, email, sdk)

            # Build the preference payload
            preference_data = {
                "items": [
                    {
                        "product_id": int(product_id),
                        "title": "Product",
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
                
                "marketplace": "3D CAPYBARA",
                "marketplace_fee": round(int(quantity) * float(transaction_amount) * 0.1, 2),
            
            }

            # Create the preference
            logger.info(f"Creating MercadoPago preference with payload: {preference_data}")
            preference_response = sdk.preference().create(preference_data)
            logger.info(f"Preference created successfully: {preference_response}")
            
            if "response" not in preference_response or "id" not in preference_response["response"]:
                logger.error(f"Unexpected preference creation response: {preference_response}")
                raise RuntimeError("Failed to extract preference ID from response.")
                
            return preference_response["response"]["id"]

        except Exception as e:
            logger.error(f"MercadoPago Preference Creation Error: {str(e)}")
            raise RuntimeError("Failed to create MercadoPago preference.")

    @staticmethod
    def create_order_preference(items: List, transaction_amount: float, success_endpoint: str,notification_endpoint: str):
        try:
            access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
            if not access_token:
                logger.error("Access token for MercadoPago is missing.")
                raise RuntimeError("Access token is not configured.")
            logger.info(f"Using access token: {access_token}")

            sdk = mercadopago.SDK(access_token)

            # Prepare preference data
            preference_data = {
                "items": items,
                "back_urls": {
                    "success": success_endpoint,
                    "failure": "https://3dcapybara.vercel.app/api/mpresponse/failure",
                    "pending": "https://3dcapybara.vercel.app/api/mpresponse/pending"
                },
                "auto_return": "approved",
                "notification_url": notification_endpoint,
            
                "marketplace": "3D CAPYBARA",
                "marketplace_fee": round(float(transaction_amount) * 0.1, 2),
    
            }
            # Log the payload
            logger.info(f"Creating MercadoPago order preference with payload: {preference_data}")

            # Create the preference
            preference_response = sdk.preference().create(preference_data)
            logger.info(f"Preference created successfully: {preference_response}")

            if "body" not in preference_response or "id" not in preference_response["body"]:
                logger.error(f"Unexpected preference response: {preference_response}")
                raise RuntimeError("Failed to extract preference ID from response.")

            return preference_response["body"]["id"]

        except Exception as e:
            logger.error(f"Unexpected error while creating order preference: {str(e)}")
            raise RuntimeError("Failed to create MercadoPago order preference.")