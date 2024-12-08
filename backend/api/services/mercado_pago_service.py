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

            sdk = mercadopago.SDK(access_token)

            # Generate seller ID
            #  seller_id = MercadoPagoPreferenceService.create_seller_id(seller_first_name, seller_last_name, email, sdk)

            # Build the preference payload
            preference_data = {
                "items": [
                    {
                        "id": int(product_id),
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

            preference_response = sdk.preference().create(preference_data)
            
            if "response" not in preference_response or "id" not in preference_response["response"]:
                logger.error(f"Unexpected preference creation response: {preference_response}")
                raise RuntimeError("Failed to extract preference ID from response.")
                
            return preference_response["response"]["id"]

        except Exception as e:
            logger.error(f"MercadoPago Preference Creation Error: {str(e)}")
            raise RuntimeError("Failed to create MercadoPago preference.")

    @staticmethod
    def create_order_preference(items: List[Dict[str, object]], transaction_amount: float, success_endpoint: str, notification_endpoint: str) -> str:

        try:
            # Fetch and validate access token
            access_token = getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", None)
            if not access_token:
                logger.error("Access token for MercadoPago is missing.")
                raise RuntimeError("Access token is not configured or missing.")
            
            logger.info(f"Using access token: {access_token}")
            sdk = mercadopago.SDK(access_token)

            # Validate input items
            if not items or not all(
                "title" in item and "quantity" in item and "unit_price" in item for item in items
            ):
                raise ValueError("Items must contain 'title', 'quantity', and 'unit_price' for each item.")

            if transaction_amount <= 0:
                raise ValueError("Transaction amount must be a positive value.")

            # Prepare preference payload
            marketplace_fee = round(transaction_amount * 0.1, 2)
            preference_data = {
                "items": items,
                "back_urls": {
                    "success": success_endpoint,
                    "failure": "https://3dcapybara.vercel.app/api/mpresponse/failure",
                    "pending": "https://3dcapybara.vercel.app/api/mpresponse/pending",
                },
                "auto_return": "approved",
                "notification_url": notification_endpoint,
                "marketplace": "3D CAPYBARA",
                "marketplace_fee": marketplace_fee,
            }

            # Log the payload for debugging
            logger.info(f"Creating MercadoPago order preference with payload: {preference_data}")

            # Make the SDK call
            preference_response = sdk.preference().create(preference_data)
            logger.debug(f"MercadoPago API response: {preference_response}")

            # Validate response
            body = preference_response.get("body", {})
            preference_id = body.get("id")
            if not preference_id:
                logger.error(f"Invalid preference response body: {body}")
                raise RuntimeError("Failed to extract preference ID from response.")

            return preference_id

        except ValueError as ve:
            logger.error(f"Validation error: {str(ve)}")
            raise RuntimeError("Invalid input data.") from ve

        except Exception as e:
            logger.error(f"Unexpected error while creating order preference: {str(e)}")
            raise RuntimeError("Failed to create MercadoPago order preference.") from e