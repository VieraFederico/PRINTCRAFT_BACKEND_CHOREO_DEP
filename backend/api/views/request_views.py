import mercadopago
from ..models import PrintRequest, DesignRequest
from ..serializers import PrintRequestSerializer, DesignRequestSerializer
from .general_imports import *
from ..permissions import IsSeller

class CreatePrintRequestView(generics.CreateAPIView):
    queryset = PrintRequest.objects.all()
    serializer_class = PrintRequestSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TOD CAMBIAR !!

"""
class UserPrintRequestListView(generics.ListAPIView):
    serializer_class = PrintRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return PrintRequest.objects.filter(userID=user)
"""
class UserPrintRequestListView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def get(self, request):
        user = request.user
        # user = User.objects.get(id=5)
        # user = User.objects.get(id=29)
        print_requests = PrintRequest.objects.filter(userID=user)

        response_data = [
            {
                "requestID": print_request.requestID,
                "userID": print_request.userID.id,
                "sellerID": print_request.sellerID.userId.id if print_request.sellerID else None,
                "description": print_request.description,
                "quantity": print_request.quantity,
                "material": print_request.material,
                "stl_url": print_request.stl_url,
                "status": print_request.status,
                "price": print_request.price,
                "preference_id": print_request.preference_id,
                # "direccion_del_vendedor": print_request.sellerID.address,
                "direccion_del_vendedor": print_request.sellerID.address if print_request.sellerID else None,
                "seller_name": print_request.sellerID.store_name if print_request.sellerID else None

            }
            for print_request in print_requests
        ]
        return Response(response_data, status=status.HTTP_200_OK)
"""
    requestID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    sellerID = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True)
    stl_url = models.URLField(max_length=200, null=False)
    description = models.TextField()
    quantity = models.IntegerField(null=False)
    material = models.CharField(max_length=255, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=255, null=False, default="Pendiente",
                              choices=[("Pendiente", "Pendiente"), ("Rechazada", "Rechazada"),
                                       ("Cotizada", "Cotizada"), ("Cancelada", "Cancelada"),
                                       ("En proceso", "En proceso"), ("Realizada", "Realizada")]
                              )
    preference_id
"""

class SellerPrintRequestListView(generics.ListAPIView):
    serializer_class = PrintRequestSerializer
    permission_classes = [IsSeller]

    def get_queryset(self):
        seller = self.request.user.seller
        return PrintRequest.objects.filter(sellerID=seller)


class AcceptOrRejectPrintRequestView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def post(self, request, request_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=4) # TOD CAMBIAR

        try:
            print_request = PrintRequest.objects.get(requestID=request_id, sellerID=sellerID) # sacar sellerID
            # if print_request.sellerID != sellerID:
            #   return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if print_request.status != "Pendiente":
                return Response({"error": "Request has already been responded"}, status=status.HTTP_400_BAD_REQUEST)

            response = request.data.get('response')
            price = request.data.get('price')

            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

            if response == "Accept":
                if not price:
                    return Response({"error": "Price is required when accepting a request"}, status=status.HTTP_400_BAD_REQUEST)
                print_request.status = "Cotizada"
                print_request.price = price
            else:
                print_request.status = "Rechazada"

            print_request.save()
            return Response({"message": f"Request successfully {response.lower()}ed"}, status=status.HTTP_200_OK)
        except PrintRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)
        from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
import uuid
# TODO!!!
class UserRespondToPrintRequestView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TOD CAMBIAR
    def post(self, request, request_id):
        userID = request.user
        # userID = User.objects.get(id=8) # TOD CAMBIAR

        try:
            print_request = PrintRequest.objects.get(requestID=request_id, userID=userID) # cambiar lo de userID -> manejarlo con un if
            if print_request.status != "Cotizada":
                return Response({"error": "Request is not in a quotable state"}, status=status.HTTP_400_BAD_REQUEST)

            response = request.data.get('response')
            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid response"}, status=status.HTTP_400_BAD_REQUEST)

            if response == "Accept":
                product_id = request_id
                quantity = print_request.quantity
                # quantity = request.get("quantity")
                transaction_amount = print_request.price
                # transaction_amount = request.get("price")
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
                        "marketplace_fee": 10
                    }
                }
                try:
                    preference_response = sdk.preference().create(preference_data)
                    preference_id = preference_response["response"]["id"]

                    return Response({"preference_id": preference_id}, status=status.HTTP_201_CREATED)

                except Exception as e:
                    return Response({"error": f"An error occurred while creating the payment preference: {str(e)}"},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                print_request.status = "Cancelada"

            print_request.save()
            return Response({"message": f"Request successfully {response.lower()}ed"}, status=status.HTTP_200_OK)
        except PrintRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class FinalizePrintRequestView(APIView):
    permission_classes = [IsSeller]

    def post(self, request, request_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=4) # TODO CAMBIAR

        try:
            print_request = PrintRequest.objects.get(requestID=request_id, sellerID=sellerID)
            # if print_request.sellerID != sellerID:
            #     return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if print_request.status != "Aceptada":
                return Response({"error": "Request is not in an accepted state"}, status=status.HTTP_400_BAD_REQUEST)

            print_request.status = "Realizada"
            print_request.save()
            return Response({"message": "Request successfully finalized"}, status=status.HTTP_200_OK)
        except PrintRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class MarkAsDeliveredPrintRequestView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def post(self, request, request_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=4) # TODO CAMBIAR

        try:
            print_request = PrintRequest.objects.get(requestID=request_id, sellerID=sellerID)
            if print_request.status != "Realizada":
                return Response({"error": "Request is not in a completed state"}, status=status.HTTP_400_BAD_REQUEST)

            print_request.status = "Entregada"
            print_request.save()
            return Response({"message": "Request successfully marked as delivered"}, status=status.HTTP_200_OK)
        except PrintRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)


class DesignRequestCreateView(generics.CreateAPIView):
    queryset = DesignRequest.objects.all()
    serializer_class = DesignRequestSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

"""
class UserDesignRequestListView(generics.ListAPIView):
    serializer_class = DesignRequestSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def get_queryset(self):
        user = self.request.user
        # user = User.objects.get(id=5)
        return DesignRequest.objects.filter(userID=user)
"""
class UserDesignRequestListView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def get(self, request):
        user = request.user
        # user = User.objects.get(id=5)
        design_requests = DesignRequest.objects.filter(userID=user)

        response_data = [
            {
                "requestID": design_request.requestID,
                "userID": design_request.userID.id,
                "sellerID": design_request.sellerID.userId.id if design_request.sellerID else None,
                "description": design_request.description,
                "quantity": design_request.quantity,
                "material": design_request.material,
                "status": design_request.status,
                "price": design_request.price,
                "preference_id": design_request.preference_id,
                "direccion_del_vendedor": design_request.sellerID.address if design_request.sellerID else None,
                "seller_name": design_request.sellerID.store_name if design_request.sellerID else None,
                "images": [image.image_url for image in design_request.design_images.all()]
            }
            for design_request in design_requests
        ]
        return Response(response_data, status=status.HTTP_200_OK)
"""
class DesignRequest(models.Model):
    sellerID = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True)
    design_images = models.ManyToManyField('DesignRequestImage')
    material = models.CharField(max_length=255, null=True)
   

"""


"""
class UserPrintRequestListView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def get(self, request):
        user = request.user
        # user = User.objects.get(id=5)
        print_requests = PrintRequest.objects.filter(userID=user)

        response_data = [
            {
                "requestID": print_request.requestID,
                "userID": print_request.userID.id,
                "description": print_request.description,
                "quantity": print_request.quantity,
                "material": print_request.material,
                "stl_url": print_request.stl_url,
                "status": print_request.status,
                "price": print_request.price,
                "preference_id": print_request.preference_id,
                "direccion_del_vendedor": print_request.sellerID.address,
                "seller_name": print_request.sellerID.store_name
            
            }
            for print_request in print_requests
        ]
        return Response(response_data, status=status.HTTP_200_OK)
"""

class SellerDesignRequestListView(generics.ListAPIView):
    serializer_class = DesignRequestSerializer
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TOD CAMBIAR

    def get_queryset(self):
        seller = self.request.user.seller
        # seller = Seller.objects.get(userId=18) # TOD CAMBIAR
        return DesignRequest.objects.filter(sellerID=seller)

# TODO
"""
descripción
cantidad
material
"""
"""
necesito que cambies está vista para que a la respuesta se le unan las DesignReverseAuctionResponse x DesignReverseAuction que el seller haya cotizado

campo       | -> |  donde lo consigo
requestID   | -> |  DesignRequest
userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    sellerID = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    design_images = models.ManyToManyField('DesignRequestImage')
    quantity = models.IntegerField(null=False)
    material = models.CharField(max_length=255, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=255, null=False, default="Pendiente",
                              choices=[("Pendiente", "Pendiente"), ("Rechazada", "Rechazada"),
                                       ("Cotizada", "Cotizada"), ("Cancelada", "Cancelada"),
                                       ("En proceso", "En proceso"), ("Realizada", "Realizada"),
                                       ("Aceptada", "Aceptada"), ("Entregada", "Entregada")]
                              )
"""

"""
class SellerDesignOrdersListView(generics.ListAPIView)

tiene que hacer una UNION entre las DesignRequests y las DesignReverseAuctions del seller

en SQL sería algo así:
SELECT *
FROM DesignRequests
WHERE sellerID = 1
UNION
SELECT *
FROM DesignReverseAuctions
WHERE sellerID = 1

# falta juntar DesignReverseAuctions con DesignReverseAuctionResponse
# falta renombrar

"""

class AcceptOrRejectDesignRequestView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny] # TODO CAMBIAR

    def post(self, request, request_id):
        sellerID = request.user.seller
        # sellerID = Seller.objects.get(userId=18) # TODO CAMBIAR

        try:
            design_request = DesignRequest.objects.get(requestID=request_id, sellerID=sellerID)
            # if design_request.sellerID != sellerID:
            #     return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if design_request.status != "Pendiente":
                return Response({"error": "Request is not pending"}, status=status.HTTP_400_BAD_REQUEST)

            response = request.data.get('response')
            price = request.data.get('price')

            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid response"}, status=status.HTTP_400_BAD_REQUEST)

            if response == "Accept":
                if not price:
                    return Response({"error": "Price is required when accepting a request"}, status=status.HTTP_400_BAD_REQUEST)
                design_request.status = "Cotizada"
                design_request.price = price
            else:
                design_request.status = "Rechazada"

            design_request.save()
            return Response({"message": f"Request successfully {response.lower()}ed"}, status=status.HTTP_200_OK)
        except DesignRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class UserRespondToDesignRequestView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]  # TODO CAMBIAR

    def post(self, request, request_id):
        userID = request.user
        # userID = User.objects.get(id=8) # TODO CAMBIAR

        try:
            design_request = DesignRequest.objects.get(requestID=request_id, userID=userID)
            if design_request.status != "Cotizada":
                return Response({"error": "Request is not in a quotable state"}, status=status.HTTP_400_BAD_REQUEST)

            response = request.data.get('response')
            if response not in ["Accept", "Reject"]:
                return Response({"error": "Invalid response"}, status=status.HTTP_400_BAD_REQUEST)

            if response == "Accept":
                product_id = request_id
                quantity = design_request.quantity
                # quantity = request.get("quantity")
                transaction_amount = design_request.price
                # transaction_amount = request.get("price")
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
            else:
                design_request.status = "Cancelada"

            design_request.save()
            return Response({"message": f"Request successfully {response.lower()}ed"}, status=status.HTTP_200_OK)
        except DesignRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)


class FinalizeDesignRequestView(APIView):
    permission_classes = [IsSeller]

    def post(self, request, request_id):
        sellerID = request.user.seller

        try:
            design_request = DesignRequest.objects.get(requestID=request_id, sellerID=sellerID)
            # if design_request.sellerID != sellerID:
            #     return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if design_request.status != "Aceptada":
                return Response({"error": "Request is not in an accepted state"}, status=status.HTTP_400_BAD_REQUEST)

            design_request.status = "Realizada"
            design_request.save()
            return Response({"message": "Request successfully finalized"}, status=status.HTTP_200_OK)
        except DesignRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class MarkAsDeliveredDesignRequestView(APIView):
    permission_classes = [IsSeller]

    def post(self, request, request_id):
        sellerID = request.user.seller

        try:
            design_request = DesignRequest.objects.get(requestID=request_id, sellerID=sellerID)
            # if design_request.sellerID != sellerID:
            #     return Response({"error": "You do not have permission to modify this request"}, status=status.HTTP_403_FORBIDDEN)
            if design_request.status != "Realizada":
                return Response({"error": "Request is not in a completed state"}, status=status.HTTP_400_BAD_REQUEST)

            design_request.status = "Entregada"
            design_request.save()
            return Response({"message": "Request successfully marked as delivered"}, status=status.HTTP_200_OK)
        except DesignRequest.DoesNotExist:
            return Response({"error": "Request not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)
