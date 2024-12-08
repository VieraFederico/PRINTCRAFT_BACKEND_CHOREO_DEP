from typing import List

import mercadopago
from django.conf import settings
import logging

from h11 import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class MercadoPagoPreferenceService:

    @staticmethod
    def create_seller_id(seller_first_name: str, seller_last_name: str, email: str, sdk: mercadopago.SDK):
        """
        Create a seller ID on Mercado Pago.
        """
        if not seller_first_name or not seller_last_name or not email:
            logger.error("Invalid seller data provided.")
            raise ValueError("Seller data is not valid.")

        seller_data = {
            "first_name": seller_first_name,
            "last_name": seller_last_name,
            "email": email,
            "type": "business"
        }

        try:
            seller_response = sdk.user().create(seller_data)
            logger.info(f"Seller created successfully: {seller_response}")
            return seller_response["body"]["id"]
        except Exception as e:
            logger.error(f"Error creating seller ID: {e}")
            raise RuntimeError("Failed to create seller ID.")

    @staticmethod
    def create_product_preference(product_id:int, quantity:int, transaction_amount:float, success_endpoint: str, seller_first_name:str, seller_last_name:str, email:str,):
        try:
            access_token = str(settings.MERCADOPAGO_ACCESS_TOKEN)
            if not access_token:
                logger.error("Access token for MercadoPago is missing.")
                return Response({"error": "Access token not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


            sdk = mercadopago.SDK(access_token)
            logger.info(f"Initializing MercadoPago SDK for seller {email}")

            seller_id = MercadoPagoPreferenceService.create_seller_id(seller_first_name, seller_last_name, email, sdk)

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
                    "pending": "https://www.3dcapybara.vercel.app/api/mpresponse/pending"
                },
                "auto_return": "approved",
                "additional_info": {
                    "marketplace": "3D CAPYBARA",
                    "marketplace_fee": round(int(quantity)*float(transaction_amount)*0.1,2),
                    "seller_id": seller_id
                }
            }
            preference_response = sdk.preference().create(preference_data)
            return preference_response["response"]["id"]

        except Exception as e:
            logger.error(f"MercadoPago Preference Creation Error: {str(e)}")
            raise

    @staticmethod
    def create_order_preference(items: List, transaction_amount: float, success_endpoint: str,
                                notification_endpoint: str, seller_first_name: str,
                                seller_last_name: str, email: str):
        try:
            access_token = settings.MERCADOPAGO_ACCESS_TOKEN
            if not access_token:
                logger.error("Access token for MercadoPago is missing.")
                raise RuntimeError("Access token is not configured.")

            sdk = mercadopago.SDK(access_token)
            logger.info(f"Initializing MercadoPago SDK for seller {email}")

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
                "payer": {
                    "email": email  # Payer email (ensure valid email)
                },
                "additional_info": {
                    "marketplace": "3D CAPYBARA",
                    "marketplace_fee": round(float(transaction_amount) * 0.1, 2),
                    "seller_id": f"{seller_first_name}-{seller_last_name}"  # Mock seller ID
                }
            }

            # Log the payload
            logger.info(f"Creating MercadoPago preference with payload: {preference_data}")

            # Create the preference
            preference_response = sdk.preference().create(preference_data)
            logger.info(f"Preference created successfully: {preference_response}")

            return preference_response["body"]["id"]

        except mercadopago.exceptions.MercadoPagoException as e:
            logger.error(f"MercadoPago API error: {e.message}")
            raise RuntimeError("MercadoPago API error occurred.")
        except Exception as e:
            logger.error(f"Unexpected error while creating preference: {str(e)}")
            raise RuntimeError("Failed to create MercadoPago preference.")
