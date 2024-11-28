from general_imports import *

class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden crear órdenes


    def perform_create(self, serializer):
        # Obtenemos los datos del serializer
        quantity = serializer.validated_data['quantity']
        product = serializer.validated_data['productCode']

        # Verificamos si la cantidad solicitada es menor o igual al stock disponible
        if product.stock < quantity:
            raise serializers.ValidationError('La cantidad solicitada excede el stock disponible.')

        # Actualizamos el stock del producto
        product.stock -= quantity
        product.save()

        # Guardamos la orden
        order=serializer.save()
        return Response({"order_id": order.order_id}, status=status.HTTP_201_CREATED)

"""
class UserOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden ver sus órdenes

    def get_queryset(self):
        # Filtrar las órdenes por el usuario autenticado
        user = self.request.user
        return Order.objects.filter(userID=user)
"""
class CompleteOrderView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def post(self, request, order_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=142)
        try:
            order = Order.objects.get(orderID=order_id, productCode__seller=seller)
            order.status = "Completada"
            order.save()
            return Response({"message": "Order marked as completed successfully"}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class DeliverOrderView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def post(self, request, order_id):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=142)
        try:
            order = Order.objects.get(orderID=order_id, productCode__seller=seller)
            order.status = "Entregada"
            order.save()
            return Response({"message": "Order marked as delivered successfully"}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found or you do not have permission to modify it"}, status=status.HTTP_404_NOT_FOUND)

class UserOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        # user = User.objects.get(id=142)
        orders = Order.objects.filter(userID=user)

        response_data = [
            {
                "orderid": order.orderID,
                "productcode": order.productCode.code,
                "quantity": order.quantity,
                "total_price": order.productCode.price * order.quantity,
                "status": order.status,
                "orderdate": order.orderDate,
                "sellerid": order.productCode.seller.userId.id,
                # "seller_email": order.productCode.seller.userId.email,
                "product_name": order.productCode.name,
            }
            for order in orders
        ]
        return Response(response_data, status=status.HTTP_200_OK)

"""
nombre_producto
precio_total
"""


"""
class SellerOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    # permission_classes = [IsSeller]  # Solo vendedores pueden ver sus órdenes
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Filtrar las órdenes por el vendedor autenticado
        # seller = self.request.user.seller
        seller = Seller.objects.get(userId=29)  # TODO CAMBIAR

        return Order.objects.filter(productCode__seller=seller)
"""
class SellerOrderListView(APIView):
    permission_classes = [IsSeller]
    # permission_classes = [AllowAny]

    def get(self, request):
        seller = request.user.seller
        # seller = Seller.objects.get(userId=29)  # TODO CAMBIAR

        orders = Order.objects.filter(productCode__seller=seller)
        response_data = [
            {
                "orderid": order.orderID,
                "productcode": order.productCode.code,
                "quantity": order.quantity,
                "total_price": order.productCode.price * order.quantity,
                "status": order.status,
                "orderdate": order.orderDate,
                "userid" : order.userID.id,
                "user_email": order.userID.email,
                "product_name": order.productCode.name
            }
            for order in orders
        ]
        return Response(response_data, status=status.HTTP_200_OK)