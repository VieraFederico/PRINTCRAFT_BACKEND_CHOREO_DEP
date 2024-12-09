from typing import List, Dict

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
    def create_order_preference(items, transaction_amount, success_endpoint, notification_endpoint):

        try:
            # Validar token de acceso
            access_token = getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", None)
            if not access_token:
                logger.error("Access token para MercadoPago no está configurado.")
                raise RuntimeError("Falta el token de acceso.")

            # Inicializar el SDK de MercadoPago
            sdk = mercadopago.SDK(access_token)

            # Construir la carga de la preferencia
            preference_data = {
                "items": [
                    {
                        "title": "Test Product",
                        "description": "Test Description",
                        "quantity": 1,
                        "currency_id": "USD",
                        "unit_price": 100.0
                    }
                ],
                "back_urls": {
                    "success": success_endpoint,
                    "failure": "https://3dcapybara.vercel.app/api/mpresponse/failure",
                    "pending": "https://3dcapybara.vercel.app/api/mpresponse/pending"
                },
                "auto_return": "approved",
                "notification_url": notification_endpoint,  # URL para notificaciones
                #"marketplace": "3D CAPYBARA",
                #"marketplace_fee": round(transaction_amount * 0.1, 2),  # Comisión
            }

            # Log del payload
            logger.info(f"Creando preferencia en MercadoPago con datos: {preference_data}")

            # Llamar al SDK para crear la preferencia
            logger.info(f"Datos enviados al SDK: {preference_data}")
            preference_response = sdk.preference().create(preference_data)
            logger.info(f"Respuesta del SDK de MercadoPago: {preference_response}")

            # Log del resultado
            logger.info(f"Respuesta de la preferencia: {preference_response}")

            # Validar respuesta
            response_body = preference_response.get("body", {})
            preference_id = response_body.get("id")
            if not preference_id:
                logger.error(f"Respuesta inválida: {response_body}")
                raise RuntimeError("No se pudo obtener el ID de la preferencia.")

            return preference_id

        except Exception as e:
            logger.error(f"Error al crear la preferencia: {str(e)}")
            raise RuntimeError("Error interno al crear la preferencia en MercadoPago.") from e