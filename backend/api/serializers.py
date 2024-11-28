import uuid
from itertools import product

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *
from rest_framework import serializers
from api.services.supabase_client import *


class UserSerializer(serializers.ModelSerializer):
    is_seller = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password", "is_seller"]
        extra_kwargs = {"password": {"write_only": True}, "id": {"read_only": True}, "is_seller": {"read_only": True}}

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user

    def get_is_seller(self, obj):
        return Seller.objects.filter(userId=obj).exists()

"""
class SellerSerializer(serializers.ModelSerializer):
    profile_picture_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Seller
        fields = ['userId', 'address', 'store_name', 'description', 'profile_picture', 'profile_picture_file']
        extra_kwargs = {'userId': {'read_only': True}, 'profile_picture':{'read_only': True}}  # El userId no se puede modificar
    def create(self, validated_data):
        user = self.context['request'].user # Agregar el userId a los datos validados
        if Seller.objects.filter(userId=user).exists():
            raise serializers.ValidationError("El usuario ya es un vendedor.")
        return Seller.objects.create(userId=user, **validated_data)
"""

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['name']

class SellerSerializer(serializers.ModelSerializer):
    profile_picture_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    materials = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all(), many=True, required=False)
    # materials = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all(), many=True, required=False)

    class Meta:
        model = Seller
        fields = ['userId', 'address', 'store_name', 'description', 'profile_picture', 'profile_picture_file', 'mp_mail', 'materials'] # TODO agregar 'mp_mail'
        extra_kwargs = {'userId': {'read_only': True}, 'profile_picture':{'read_only': True}}  # El userId no se puede modificar

    def create(self, validated_data):

        profile_picture_file = validated_data.pop('profile_picture_file', None)
        materials = validated_data.pop('materials', [])
        user = self.context['request'].user
        # user = User.objects.get(id=5)


        if profile_picture_file:
            try:
                file_content = profile_picture_file.read()
                # file_name = f"{validated_data.get('store_name', 'default_store_name')}_profile_picture"
                file_name = f"{user.id}_profile_picture"
                bucket_name = 'seller-pictures'
                profile_picture_url = upload_file_to_supabase(file_content, bucket_name, file_name)
                validated_data['profile_picture'] = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/{bucket_name}/{profile_picture_url}"
            except Exception as e:
                raise serializers.ValidationError(f"Error al subir la imagen: {str(e)}")
        else:
            validated_data['profile_picture'] = None
        seller = Seller.objects.create(userId=user, **validated_data)
        seller.materials.set(materials)
        return seller
        # return Seller.objects.create(userId=4, **validated_data)

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['orderID', 'userID', 'orderDate', 'quantity', 'productCode', 'status']
        extra_kwargs = {'userID': {'read_only': True}, 'orderID': {'read_only': True}, 'orderDate': {'read_only': True}, 'status': {'read_only': True}}
        #read_only_fields = ['order_id', 'order_date', 'status']  # El ID, la fecha y el estado no se pueden modificar

    def create(self, validated_data):
        # Al crear una orden, el estado siempre será "pendiente"
        user = self.context['request'].user
        validated_data['userID'] = user
        return Order.objects.create(**validated_data)


class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

"""
class PrintRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintRequest
        fields = ['requestID', 'userID', 'sellerID', 'stl_url', 'description', 'quantity', 'material', 'status']
        extra_kwargs = {'userID': {'read_only': True}, 'status': {'read_only': True}}

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['userID'] = user
        return PrintRequest.objects.create(**validated_data)
"""

class PrintRequestSerializer(serializers.ModelSerializer):
    stl_file = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = PrintRequest
        fields = ['requestID', 'userID', 'quantity', 'sellerID', 'stl_url', 'description', 'material', 'status', 'stl_file', 'price']
        extra_kwargs = {'requestID':{'read_only':True}, 'userID': {'read_only': True}, 'status': {'read_only': True}, 'stl_url': {'read_only': True}, 'price':{'read_only':True}}

    def create(self, validated_data):
        stl_file = validated_data.pop('stl_file', None)
        user = self.context['request'].user
        # user = User.objects.get(id=7)  # TODO CAMBIARRRR

        """
        try:
            user = User.objects.get(id=4)  # TODO CAMBIARRRR
        except User.DoesNotExist:
            raise serializers.ValidationError("El usuario no existe.")
        """
        img_id = uuid.uuid4()  # Generar un requestID único

        if stl_file:
            try:
                stl_file_content = stl_file.read()
                stl_file_url = upload_file_to_supabase(stl_file_content, 'request-stl', f"{img_id}_stl", content_type="model/stl")
                stl_file_url = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/request-stl/{stl_file_url}"
                # validated_data['stl_url'] = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/stl_files/{stl_file_url}"
            except Exception as e:
                raise serializers.ValidationError(f"Error al subir el archivo STL: {str(e)}")
        else:
            return serializers.ValidationError("No se ha proporcionado un archivo STL.")

        # validated_data['userID'] = user
        # return PrintRequest.objects.create(**validated_data)
        return PrintRequest.objects.create(userID=user, stl_url=stl_file_url, **validated_data)


class DesignRequestImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignRequestImage
        fields = ['image_url']


class DesignRequestSerializer(serializers.ModelSerializer):
    design_images = DesignRequestImageSerializer(many=True, read_only=True, required=False)
    design_images_files = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)


    class Meta:
        model = DesignRequest
        fields = ['requestID', 'userID', 'sellerID', 'description', 'design_images', 'design_images_files', 'quantity', 'material', 'price',
                  'status']
        extra_kwargs = {
            'requestID': {'read_only': True},
            'userID': {'read_only': True},
            'status': {'read_only': True},
            'design_images': {'read_only': True},
            'design_images_files': {'write_only': True},
            'price': {'read_only': True}
        }

    def create(self, validated_data):
        design_images_files = validated_data.pop('design_images_files', [])
        user = self.context['request'].user
        # user = User.objects.get(id=5)
        design_request = DesignRequest.objects.create(userID=user, **validated_data)

        for index, image_file in enumerate(design_images_files, start=1):
            try:
                file_content = image_file.read()
                file_name = f"{design_request.requestID}_{index}"
                bucket_name = 'design_request_images'
                image_url = upload_file_to_supabase(file_content, bucket_name, file_name)
                image_url = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/{bucket_name}/{image_url}"
                DesignRequestImage.objects.create(image_url=image_url)
                design_request.design_images.add(DesignRequestImage.objects.get(image_url=image_url))
            except Exception as e:
                raise serializers.ValidationError(f"Error al subir la imagen: {str(e)}")

        return design_request

## -------------------------------------------------------------------------------------  ##

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['product', 'image_url']

class ProductMaterialSerializer(serializers.ModelSerializer):
    material = serializers.SlugRelatedField(slug_field='name', queryset=Material.objects.all())

    class Meta:
        model = ProductMaterial
        fields = ['material', 'price']

# TODO: update serializer to include reviews
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)  # Relación con las imágenes a través de la ForeignKey
    image_files = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)
    stl_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    materials = ProductMaterialSerializer(many=True, source='productmaterial_set', required=False) # TODO required=False

    categories = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Category.objects.all()
    )

    class Meta:
        model = Product
        fields = [
            'code', 'name', 'material', 'stock', 'description',
            'stl_file_url', 'seller', 'price', 'image_files', 'images', 'stl_file', 'categories', 'materials', 'review_sum', 'review_count'
        ]
        extra_kwargs = {
            'code': {'read_only': True},  # Solo lectura
            'seller': {'read_only': True},  # Solo lectura
            'stl_file_url': {'read_only': True},  # Solo escritura
            'review_sum': {'read_only': True},
            'review_count': {'read_only': True}
            # 'stl_file': {'write_only': True},  # Solo escritura
        }

    # TODO ARREGLAR PARA QUE SE PUEDA NO SUBIR UN ARCHIVO STL !!!
    def create(self, validated_data):
        product_name = validated_data['name']
        # Extraer archivos de imagen del campo de solo escritura
        image_files = validated_data.pop('image_files', [])
        stl_file = validated_data.pop('stl_file', None)
        materials_data = validated_data.pop('productmaterial_set', [])
        categories = validated_data.pop('categories', [])



        # Asignar el vendedor desde el contexto del request
        seller = self.context['request'].user.seller
        # seller = Seller.objects.get(userId=4) # TODO CAMBIARR

        if stl_file:
            # Leer el contenido del archivo STL antes de subirlo
            stl_file_content = stl_file.read()

            # Subir el archivo STL a Supabase y obtener la URL
            stl_file_url = upload_file_to_supabase(stl_file_content, '3d-archives', f"{product_name}_stl", content_type="model/stl")

            stl_file_url = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/3d-archives/{stl_file_url}"
        else:
            stl_file_url = None

        # Crear el producto con los datos restantes
        product = Product.objects.create(seller=seller, stl_file_url=stl_file_url, **validated_data)


        for material_data in materials_data:
            ProductMaterial.objects.create(product=product, **material_data)

        product.categories.set(categories)



        for index, image_file in enumerate(image_files, start=1):
            file_name = f"{product.name}_{index}"
            # todo IMPORTANTE
            # file_name = f"{product.code}_{index}"
            bucket_name = 'images'

            try:
                # Leer el contenido del archivo antes de subirlo
                file_content = image_file.read()


                # Subir el archivo a Supabase y obtener la URL
                image_url = upload_file_to_supabase(file_content, bucket_name, file_name)
                # todo agregar la URL base a image_url
                # https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/images/
                image_url = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/images/{image_url}"

                # Guardar la URL en el modelo ProductImage asociado al producto
                ProductImage.objects.create(product=product, image_url=image_url)
            except Exception as e:
                # Manejar cualquier error durante la subida
                raise serializers.ValidationError(f"Error al subir la imagen: {str(e)}")

        return product

# TO-DO: update serializer to include reviews
class ProductDetailSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.store_name', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    materials = ProductMaterialSerializer(many=True, source='productmaterial_set')
    categories = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Category.objects.all()
    )
    # reviews = ProductReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'code', 'name', 'material', 'stock', 'description',
            'stl_file_url', 'seller', 'price', 'images', 'categories', 'materials', 'seller_name', 'review_sum', 'review_count' #'reviews'
        ]
        extra_kwargs = {
            'code': {'read_only': True},  # Solo lectura
            'seller': {'read_only': True},  # Solo lectura
            'stl_file_url': {'read_only': True},  # Solo escritura
            'review_sum': {'read_only': True},
            'review_count': {'read_only': True}
        }


class PrintReverseAuctionSerializer(serializers.ModelSerializer):
    stl_file = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = PrintReverseAuction
        fields = ['requestID', 'userID', 'description', 'quantity', 'material', 'stl_file', 'stl_file_url', 'status', 'accepted_response', 'response_count']
        extra_kwargs = {'requestID': {'read_only': True}, 'userID': {'read_only': True}, 'stl_file_url':{'read_only':True}, 'status': {'read_only': True}, 'accepted_response': {'read_only': True}, 'response_count': {'read_only': True}}

    def create(self, validated_data):
        user = self.context['request'].user
        # user = User.objects.get(id=8) # TODO CAMBIAR

        stl_file = validated_data.pop('stl_file', None)

        if not stl_file:
            raise serializers.ValidationError("No se ha proporcionado un archivo STL.")

        stl_file_content = stl_file.read()
        stl_file_url = upload_file_to_supabase(stl_file_content, 'reverse-auction-stl', f"{uuid.uuid4()}_stl", content_type="model/stl")
        stl_file_url = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/reverse-auction-stl/{stl_file_url}"

        # reverse-auction-stl
        return PrintReverseAuction.objects.create(userID=user, stl_file_url=stl_file_url, **validated_data)


class PrintReverseAuctionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintReverseAuctionResponse
        fields = ['responseID', 'auction', 'seller', 'price', 'created_at', 'status']
        extra_kwargs = {'responseID': {'read_only': True}, 'seller': {'read_only': True}, 'created_at': {'read_only': True}, 'status': {'read_only': True}}




class DesignReverseAuctionSerializer(serializers.ModelSerializer):
    design_images = DesignRequestImageSerializer(many=True, read_only=True)  # Relación con las imágenes a través de la ForeignKey
    image_files = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)

    class Meta:
        model = DesignReverseAuction
        fields = ['requestID', 'userID', 'description', 'quantity', 'material', 'image_files', 'design_images', 'status', 'accepted_response', 'response_count']
        extra_kwargs = {'requestID': {'read_only': True}, 'userID': {'read_only': True}, 'image_files': {'write_only':True}, 'design_images':{'read_only':True}, 'status': {'read_only': True}, 'accepted_response': {'read_only': True}, 'response_count': {'read_only': True}}

    def create(self, validated_data):
        user = self.context['request'].user
        # user = User.objects.get(id=8) # TODO CAMBIAR
        image_files = validated_data.pop('image_files', [])
        design_reverse_auction = DesignReverseAuction.objects.create(userID=user, **validated_data)

        for index, image_file in enumerate(image_files, start=1):
            try:
                file_content = image_file.read()
                file_name = f"reverse_auction_image_{design_reverse_auction.requestID}_{index}"
                bucket_name = 'reverse-auction-image'
                image_url = upload_file_to_supabase(file_content, bucket_name, file_name)
                image_url = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/{bucket_name}/{image_url}"
                DesignRequestImage.objects.create(image_url=image_url)
                design_reverse_auction.design_images.add(DesignRequestImage.objects.get(image_url=image_url))
            except Exception as e:
                raise serializers.ValidationError(f"Error al subir la imagen: {str(e)}")

        return design_reverse_auction

class DesignReverseAuctionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignReverseAuctionResponse
        fields = ['responseID', 'auction', 'seller', 'price', 'created_at', 'status']
        extra_kwargs = {'responseID': {'read_only': True}, 'seller': {'read_only': True}, 'created_at': {'read_only': True}, 'status': {'read_only': True}}


class DesignReverseAuctionResponseCombinedSerializer(serializers.ModelSerializer):
    auction = serializers.SerializerMethodField()

    class Meta:
        model = DesignReverseAuctionResponse
        fields = ['responseID', 'auction', 'seller', 'price', 'created_at', 'status']

    def get_auction(self, obj):
        return {
            'requestID': obj.auction.requestID,
            'userID': obj.auction.userID.id,
            'description': obj.auction.description,
            'quantity': obj.auction.quantity,
            'material': obj.auction.material,
            'status': obj.auction.status,
            'accepted_response': obj.auction.accepted_response.responseID if obj.auction.accepted_response else None,
            'response_count': obj.auction.response_count,
            'design_images': [image.image_url for image in obj.auction.design_images.all()]
        }


class PrintReverseAuctionResponseCombinedSerializer(serializers.ModelSerializer):
    auction = serializers.SerializerMethodField()

    class Meta:
        model = PrintReverseAuctionResponse
        fields = ['responseID', 'auction', 'seller', 'price', 'created_at', 'status']

    def get_auction(self, obj):
        return {
            'requestID': obj.auction.requestID,
            'userID': obj.auction.userID.id,
            'description': obj.auction.description,
            'quantity': obj.auction.quantity,
            'material': obj.auction.material,
            'status': obj.auction.status,
            'accepted_response': obj.auction.accepted_response.responseID if obj.auction.accepted_response else None,
            'response_count': obj.auction.response_count,
            'stl_file_url': obj.auction.stl_file_url
        }