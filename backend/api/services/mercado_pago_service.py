from typing import List, Dict

import mercadopago
from django.conf import settings
import logging

from h11 import Response
from rest_framework import status

from backend.settings import MP_KEY_FEDE

logger = logging.getLogger(__name__)


class MercadoPagoPreferenceService:


    @staticmethod
    def create_seller_data(seller_email: str):
        # Construct seller data
        seller_data = {
            "email": seller_email,
            "first_name": "Seller",
            "last_name": "Account",
            "country_id": "BR"  # Adjust based on your primary market
        }

        try:
            # Mercado Pago SDK call (requires an instance of Mercado Pago SDK)
            access_token = str(settings.MP_KEY)
            sdk = mercadopago.SDK(access_token)  # Replace with your actual token
            seller_response = sdk.user().create(seller_data)
            return seller_response
        except Exception as e:
            # Log or handle the exception
            print(f"Error creating seller data: {str(e)}")
            return None
    

    @staticmethod
    def create_product_preference(product_id: int, quantity: int, transaction_amount: float, success_endpoint: str):
        try:
            access_token = str(settings.MP_KEY)

            sdk = mercadopago.SDK(access_token)

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
                "marketplace_seller_id": str(settings.MP_US_ID),

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
    def create_order_preference(items,total_amount, success_endpoint):
        try:
            access_token = str(settings.MP_KEY)
            sdk = mercadopago.SDK(access_token)

            # Construct preference payload
            preference_data = {
                "items": items,
                "back_urls": {
                    "success": success_endpoint,
                    "failure": "https://3dcapybara.vercel.app/api/mpresponse/failure",
                    "pending": "https://3dcapybara.vercel.app/api/mpresponse/pending"
                },
                "auto_return": "approved",
                "marketplace": "3D Capybara",
                "marketplace_fee": round(float(total_amount) * 0.1),
                "collector": {
                    "access_token": MP_KEY_FEDE  # This ensures payment goes to the seller
                }
            }

            logger.info(f"Creating MercadoPago preference with data: {preference_data}")
            
            # Call MercadoPago SDK to create the preference
            preference_response = sdk.preference().create(preference_data)
            return preference_response["response"]["id"]
        except Exception as e:
            logger.error(f"Error creating MercadoPago preference: {str(e)}")
            
