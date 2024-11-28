from backend.api.serializers import UserSerializer
from general_imports import *


###############
#### USERS ####
###############
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class ReturnUserDataView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    def delete(self, request):
        user = request.user
        # user = User.objects.get(id=50)
        try:

            # Check if the user is a seller
            if hasattr(user, 'seller'):
                seller = user.seller
                # Remove profile picture if exists
                """
                if seller.profile_picture:
                    file_name = seller.profile_picture.split('/')[-1]
                    remove_file_from_supabase('seller-pictures', file_name)
                """
                # Delete the seller
                seller.delete()

            # Delete the user
            user.delete()
            return Response({"message": "User successfully deleted"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
