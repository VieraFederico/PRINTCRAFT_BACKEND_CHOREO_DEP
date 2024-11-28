import mercadopago
from backend.api.permissions import IsSeller
from general_imports import *

from models import DesignRequest, DesignReverseAuction, DesignReverseAuctionResponse, PrintReverseAuction,PrintReverseAuctionResponse,PrintRequest
from serializers import DesignReverseAuctionSerializer, PrintReverseAuctionSerializer

class PrintReverseAuctionCreateView(generics.CreateAPIView):
    queryset = PrintReverseAuction.objects.all()
    serializer_class = PrintReverseAuctionSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TODO CAMBIAR

class UserPrintReverseAuctionListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def get_queryset(self):
        user = self.request.user
        # user = User.objects.get(id=142)
        return PrintReverseAuction.objects.filter(userID=user, status="Open")

class OpenPrintReverseAuctionListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return PrintReverseAuction.objects.filter(status="Open")

class CreatePrintReverseAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, auction_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=4) # TODO CAMBIAR
        try:
            auction = PrintReverseAuction.objects.get(requestID=auction_id, status="Open")
        except PrintReverseAuction.DoesNotExist:
            return Response({'error': 'Auction not found or not open'}, status=status.HTTP_404_NOT_FOUND)

        response = request.data.get('response')
        price = request.data.get('price')
        if not price:
            return Response({'error': 'Price is required'}, status=status.HTTP_400_BAD_REQUEST)

        auction.response_count += 1
        auction.save()

        response = PrintReverseAuctionResponse.objects.create(auction=auction, seller=sellerID, price=price)
        return Response({'message': 'Response created successfully', 'response_id': response.responseID}, status=status.HTTP_201_CREATED)

"""
class QuotizedPrintReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionResponseCombinedSerializer
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def get_queryset(self):
        seller = self.request.user.seller
        # seller = Seller.objects.get(userId=4) # TODO CAMBIAR
        return PrintReverseAuctionResponse.objects.select_related('auction').filter(seller=seller, status="Pending")
"""

# class QuotatedPrintOrdersListView(APIView):
class QuotizedPrintReverseAuctionResponseListView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def get(self, request):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=142) # TODO CAMBIAR
        quotated_responses = PrintReverseAuctionResponse.objects.filter(seller=seller, status="Pending")
        printed_requests = PrintRequest.objects.filter(sellerID=seller, status="Cotizada")

        response_data = [
            {
                "userID": response.auction.userID.id,
                "description": response.auction.description,
                "quantity": response.auction.quantity,
                "material": response.auction.material,
                "price": response.price,
                "status": response.status,
                "stl_url": response.auction.stl_file_url,
            }
            for response in quotated_responses
        ]

        response_data += [
            {
                "userID": request.userID.id,
                "description": request.description,
                "quantity": request.quantity,
                "material": request.material,
                "price": request.price,
                "status": request.status,
                "stl_url": request.stl_url,
            }
            for request in printed_requests
        ]

        return Response(response_data, status=status.HTTP_200_OK)


"""
nueva view que retorne las design/print-requests cotizadas, join design/print-reverse-auction

{
    
}


"""

"""
class PrintReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = PrintReverseAuctionResponseSerializer
    permission_classes = [AllowAny] # TODO -> ¿lo puede ver cualquiera?

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        return PrintReverseAuctionResponse.objects.filter(auction__requestID=auction_id)
"""
class PrintReverseAuctionResponseListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, auction_id):
        responses = PrintReverseAuctionResponse.objects.filter(auction__requestID=auction_id)

        response_data = [
            {
                "responseID": response.responseID,
                "seller": response.seller.userId.id,
                "price": response.price,
                "status": response.status,
                "created_at": response.created_at,
                # "auction": response.auction.requestID,
                "sellerName": response.seller.store_name,
                "sellerAddress": response.seller.address
            }
            for response in responses
        ]
        return Response(response_data, status=status.HTTP_200_OK)

# TODO: Cambiar nombre de la vista a AcceptPrintReverseAuctionResponseView
class AcceptAuctionResponseView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, auction_id, response_id):
        userID = request.user
        # userID = User.objects.get(id=8) # TODO CAMBIAR
        try:
            auction = PrintReverseAuction.objects.get(requestID=auction_id, status="Open", userID=userID)
            response = PrintReverseAuctionResponse.objects.get(responseID=response_id, auction=auction)

            # Aceptar la respuesta indicada
            response.status = "Accepted"
            response.save()

            # Actualizar el accepted_response en la subasta
            auction.accepted_response = response
            auction.status = "Closed"
            auction.save()

            # Rechazar todas las demás respuestas
            PrintReverseAuctionResponse.objects.filter(auction=auction).exclude(responseID=response_id).update(status="Rejected")

            PrintRequest.objects.create(
                userID=auction.userID,
                sellerID=response.seller,
                stl_url=auction.stl_file_url,
                description=auction.description,
                quantity=auction.quantity,
                material=auction.material,
                price=response.price,
            )

            product_id = auction.requestID
            quantity =  auction.quantity
            transaction_amount = response.price
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
                    "success": "https://3dcapybara.vercel.app/api/mpresponse/sucess",
                    "failure": "https://3dcapybara.vercel.app/api/mpresponse/failure",
                    "pending": "https://www.3dcapybara.vercel.app/api/mpresponse/pending"
                },
                "auto_return": "approved",
                "notification_url": "https://3dcapybara.vercel.app/api/notifications/printrequest",
                "additional_info": {
                    "marketplace_fee":10
                }
            }
            try:
                preference_response = sdk.preference().create(preference_data)
                preference_id = preference_response["response"]["id"]

                return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": f"An error occurred while creating the payment preference: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            #return Response({"message": "Auction response accepted successfully"}, status=status.HTTP_200_OK)
        except PrintReverseAuction.DoesNotExist:
            return Response({"error": "Auction not found or not open"}, status=status.HTTP_404_NOT_FOUND)
        except PrintReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Auction response not found"}, status=status.HTTP_404_NOT_FOUND)


# TODO: Cambiar nombre de la vista a CompletePrintReverseAuctionResponseView
class CompleteAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, response_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4)
        try:
            response = PrintReverseAuctionResponse.objects.get(responseID=response_id, seller=seller, status="Accepted")
            response.status = "Completed"
            response.save()
            response.auction.status = "Completed"
            response.auction.save()
            return Response({"message": "Auction response marked as completed successfully"}, status=status.HTTP_200_OK)
        except PrintReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Accepted auction response not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

# TODO: Cambiar nombre de la vista a DeliverPrintReverseAuctionResponseView
class DeliverAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, response_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4) # TODO CAMBIAR
        try:
            response = PrintReverseAuctionResponse.objects.get(responseID=response_id, seller=seller, status="Completed")
            response.status = "Delivered"
            response.save()
            response.auction.status = "Delivered"
            response.auction.save()

            return Response({"message": "Auction response marked as delivered successfully"}, status=status.HTTP_200_OK)
        except PrintReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Completed auction response not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)


class DesignReverseAuctionCreateView(generics.CreateAPIView):
    queryset = DesignReverseAuction.objects.all()
    serializer_class = DesignReverseAuctionSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TODO CAMBIAR

class UserDesignReverseAuctionListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def get_queryset(self):
        user = self.request.user
        # user = User.objects.get(id=142)
        return DesignReverseAuction.objects.filter(userID=user, status="Open")

class OpenDesignReverseAuctionListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return DesignReverseAuction.objects.filter(status="Open")


class CreateDesignReverseAuctionResponseView(APIView):
    permission_classes = [IsAuthenticated, IsSeller]

    def post(self, request, auction_id):
        sellerID = request.user.seller
        try:
            auction = DesignReverseAuction.objects.get(requestID=auction_id, status="Open")
        except DesignReverseAuction.DoesNotExist:
            return Response({'error': 'Auction not found or not open'}, status=status.HTTP_404_NOT_FOUND)

        response = request.data.get('response')
        price = request.data.get('price')
        if not price:
            return Response({'error': 'Price is required'}, status=status.HTTP_400_BAD_REQUEST)

        auction.response_count += 1
        auction.save()

        response = DesignReverseAuctionResponse.objects.create(auction=auction, seller=sellerID, price=price)
        return Response({'message': 'Response created successfully', 'response_id': response.responseID}, status=status.HTTP_201_CREATED)

"""
class QuotizedDesignReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionResponseCombinedSerializer
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def get_queryset(self):
        seller = self.request.user.seller
        # seller = Seller.objects.get(userId=4)  # TODO CAMBIAR
        # return DesignReverseAuctionResponse.objects.select_related('auction').filter(seller=seller) # TODO CAMBIAR
        return DesignReverseAuctionResponse.objects.select_related('auction').filter(seller=seller, status="Pending")
"""
class QuotizedDesignReverseAuctionResponseListView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def get(self, request):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=142) # TODO CAMBIAR
        quotated_responses = DesignReverseAuctionResponse.objects.filter(seller=seller, status="Pending")
        quotated_requests = DesignRequest.objects.filter(sellerID=seller, status="Cotizada")

        response_data = [
            {
                "userID": response.auction.userID.id,
                "description": response.auction.description,
                "quantity": response.auction.quantity,
                "material": response.auction.material,
                "price": response.price,
                "status": response.status,
                "images": [image.image_url for image in response.auction.design_images.all()]
            }
            for response in quotated_responses
        ]

        response_data += [
            {
                "userID": request.userID.id,
                "description": request.description,
                "quantity": request.quantity,
                "material": request.material,
                "price": request.price,
                "status": request.status,
                "images": [image.image_url for image in request.design_images.all()]
            }
            for request in quotated_requests
        ]

        return Response(response_data, status=status.HTTP_200_OK)

"""
class DesignReverseAuctionResponseListView(generics.ListAPIView):
    serializer_class = DesignReverseAuctionResponseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        return DesignReverseAuctionResponse.objects.filter(auction__requestID=auction_id)

"""
class DesignReverseAuctionResponseListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, auction_id):
        responses = DesignReverseAuctionResponse.objects.filter(auction__requestID=auction_id)

        response_data = [
            {
                "responseID": response.responseID,
                "seller": response.seller.userId.id,
                "price": response.price,
                "status": response.status,
                "created_at": response.created_at,
                # "auction": response.auction.requestID,
                "sellerName": response.seller.store_name,
                "sellerAddress": response.seller.address
            }
            for response in responses
        ]
        return Response(response_data, status=status.HTTP_200_OK)


class AcceptDesignReverseAuctionResponseView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def post(self, request, auction_id, response_id):
        userID = request.user
        # userID = User.objects.get(id=8) # TOD CAMBIAR
        try:
            auction = DesignReverseAuction.objects.get(requestID=auction_id, status="Open", userID=userID)
            response = DesignReverseAuctionResponse.objects.get(responseID=response_id, auction=auction)

            response.status = "Accepted"
            response.save()

            auction.accepted_response = response
            auction.status = "Closed"
            auction.save()

            DesignReverseAuctionResponse.objects.filter(auction=auction).exclude(responseID=response_id).update(status="Rejected")

            design_request = DesignRequest.objects.create(
                userID=auction.userID,
                sellerID=response.seller,
                description=auction.description,
                quantity=auction.quantity,
                material=auction.material,
                price=response.price,
            )

            design_request.design_images.set(auction.design_images.all())

            product_id = auction.requestID
            quantity =  auction.quantity
            transaction_amount = response.price
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
                    "success": "https://3dcapybara.vercel.app/api/mpresponse/sucess",
                    "failure": "https://3dcapybara.vercel.app/api/mpresponse/failure",
                    "pending": "https://www.3dcapybara.vercel.app/api/mpresponse/pending"
                },
                "auto_return": "approved",
                "notification_url": "https://3dcapybara.vercel.app/api/notifications/designrequest",
                "additional_info": {
                    "marketplace_fee":10
                }
            }
            try:
                preference_response = sdk.preference().create(preference_data)
                preference_id = preference_response["response"]["id"]

                return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": f"An error occurred while creating the payment preference: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"message": "Auction response accepted successfully"}, status=status.HTTP_200_OK)
        except DesignReverseAuction.DoesNotExist:
            return Response({"error": "Auction not found or not open"}, status=status.HTTP_404_NOT_FOUND)
        except DesignReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Auction response not found"}, status=status.HTTP_404_NOT_FOUND)


class CompleteDesignReverseAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def post(self, request, response_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4) # TOD CAMBIAR
        try:
            response = DesignReverseAuctionResponse.objects.get(responseID=response_id, seller=seller, status="Accepted")
            response.status = "Completed"
            response.save()
            response.auction.status = "Completed"
            response.auction.save()
            return Response({"message": "Auction response marked as completed successfully"}, status=status.HTTP_200_OK)
        except DesignReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Accepted auction response not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class DeliverDesignReverseAuctionResponseView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def post(self, request, response_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=4) # TOD CAMBIAR
        try:
            response = DesignReverseAuctionResponse.objects.get(responseID=response_id, seller=seller, status="Completed")
            response.status = "Delivered"
            response.save()
            response.auction.status = "Delivered"
            response.auction.save()

            return Response({"message": "Auction response marked as delivered successfully"}, status=status.HTTP_200_OK)
        except DesignReverseAuctionResponse.DoesNotExist:
            return Response({"error": "Completed auction response not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

"""
Crear subasta inversa
/api/print-reverse-auction/create/
POST
JSON a enviar
{
  description,
  quantity,
  material,
}
y archivo STL
"""
"""
Mirar las subastas inversas para impresión que inicie
/api/print-reverse-auction/mine/
GET
te da
{
  requestID,
  description (string/text),
  quantity,
  material, 
  stl_url,
  responses, // cantidad de vendedores que mandaron cotización 
  userID
}
"""
