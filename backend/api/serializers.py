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

class SellerSerializer(serializers.ModelSerializer):
    profile_picture_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Seller
        fields = ['userId', 'address', 'store_name', 'description', 'profile_picture', 'profile_picture_file'] # TODO agregar 'mp_mail'
        extra_kwargs = {'userId': {'read_only': True}, 'profile_picture':{'read_only': True}}  # El userId no se puede modificar

    def create(self, validated_data):

        profile_picture_file = validated_data.pop('profile_picture_file', None)
        user = self.context['request'].user

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
        return Seller.objects.create(userId=user, **validated_data)
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
        fields = ['requestID', 'userID', 'sellerID', 'stl_url', 'description', 'quantity', 'material', 'status', 'stl_file']
        extra_kwargs = {'requestID':{'read_only':True}, 'userID': {'read_only': True}, 'status': {'read_only': True}, 'stl_url': {'read_only': True}}

    def create(self, validated_data):
        stl_file = validated_data.pop('stl_file', None)
        user = self.context['request'].user

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
                stl_file_url = upload_file_to_supabase(stl_file_content, 'request-stl', f"{img_id}_stl")
                stl_file_url = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/request-stl/{stl_file_url}"
                # validated_data['stl_url'] = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/stl_files/{stl_file_url}"
            except Exception as e:
                raise serializers.ValidationError(f"Error al subir el archivo STL: {str(e)}")
        else:
            return serializers.ValidationError("No se ha proporcionado un archivo STL.")

        # validated_data['userID'] = user
        # return PrintRequest.objects.create(**validated_data)
        return PrintRequest.objects.create(userID=user, stl_url=stl_file_url, **validated_data)

## -------------------------------------------------------------------------------------  ##

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['product', 'image_url']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)  # Relación con las imágenes a través de la ForeignKey
    image_files = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)
    stl_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            'code', 'name', 'material', 'stock', 'description',
            'stl_file_url', 'seller', 'price', 'image_files', 'images', 'stl_file'
        ]
        extra_kwargs = {
            'code': {'read_only': True},  # Solo lectura
            'seller': {'read_only': True},  # Solo lectura
            'stl_file_url': {'read_only': True},  # Solo escritura
            # 'stl_file': {'write_only': True},  # Solo escritura
        }

    # TODO ARREGLAR PARA QUE SE PUEDA NO SUBIR UN ARCHIVO STL !!!
    def create(self, validated_data):
        product_name = validated_data['name']
        # Extraer archivos de imagen del campo de solo escritura
        image_files = validated_data.pop('image_files', [])
        stl_file = validated_data.pop('stl_file', None)


        # Asignar el vendedor desde el contexto del request
        seller = self.context['request'].user.seller

        # Leer el contenido del archivo STL antes de subirlo
        stl_file_content = stl_file.read()

        # Subir el archivo STL a Supabase y obtener la URL
        stl_file_url = upload_file_to_supabase(stl_file_content, '3d-archives', f"{product_name}_stl")

        stl_file_url = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/3d-archives/{stl_file_url}"

        # Crear el producto con los datos restantes
        product = Product.objects.create(seller=seller, stl_file_url=stl_file_url, **validated_data)


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

"""
if stl_file:
    stl_file_content = stl_file.read()
    product_name = validated_data['name']
    # Subir el archivo STL a Supabase y obtener la URL
    stl_file_url = upload_file_to_supabase(stl_file_content, '3d-archives', f"{product_name}_stl")
    stl_file_url = f"https://vvvlpyyvmavjdmfrkqvw.supabase.co/storage/v1/object/public/3d-archives/{stl_file_url}"
    validated_data['stl_file_url'] = stl_file_url
"""
"""

        if stl_file:
            try:
                # Leer el contenido del archivo STL antes de subirlo
                stl_file_content = stl_file.read()

                # Subir el archivo STL a Supabase y obtener la URL
                stl_file_url = upload_file_to_supabase(stl_file_content, 'stl_files', f"{product.name}_stl")
                
                # Guardar la URL en el modelo Product
                product.stl_file_url = stl_file_url
                product.save()
            except Exception as e:
                raise serializers.ValidationError(f"Error al subir el archivo STL: {str(e)}")

        for index, image_file in enumerate(image_files, start=1):
            file_name = f"{product.name}_{index}"
            bucket_name = 'images'

            try:
                # Leer el contenido del archivo antes de subirlo
                file_content = image_file.read()

                # Subir el archivo a Supabase y obtener la URL
                image_url = upload_file_to_supabase(file_content, bucket_name, file_name)

                # Guardar la URL en el modelo ProductImage asociado al producto
                ProductImage.objects.create(product=product, image_url=image_url)
            except Exception as e:
                raise serializers.ValidationError(f"Error al subir la imagen: {str(e)}")

        return product
"""


"""
for index, image_file in enumerate(image_files, start=1):
    file_name = f"{product.name}_{index}"
    bucket_name = 'images'

    try:
        # Subir el archivo a Supabase y obtener la URL
        image_url = upload_file_to_supabase(image_file, bucket_name, file_name)

        # Guardar la URL en el modelo ProductImage asociado al producto
        ProductImage.objects.create(product=product, image_url=image_url)
    except Exception as e:
        # Manejar cualquier error durante la subida
        raise serializers.ValidationError(f"Error al subir la imagen: {str(e)}")
"""
"""
index = 0
for image_file in image_files:
    index += 1
    file_name = f"{product.name}_{index}"
    bucket_name = 'images'

    try:
        # Subir el archivo a Supabase y obtener la URL
        image_url = upload_file_to_supabase(image_file, bucket_name, file_name)

        # Guardar la URL en el modelo ProductImage asociado al producto
        ProductImage.objects.create(product=product, image_url=image_url)
    except Exception as e:
        # Manejar cualquier error durante la subida
        raise serializers.ValidationError(f"Error al subir la imagen: {str(e)}")
"""
# Example Payload:
# {
#     "name": "Product Name",
#     "material": "Material",
#     "stock": 10,
#     "description": "Product Description",
#     "stl_file_url": "http://example.com/file.stl",
#     "price": "19.99",
#     "image_files": [file1, file2]  # List of image files
# }

"""
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['code', 'name', 'material', 'stock', 'description', 'stl_file_url', 'seller', 'price', 'images']
        extra_kwargs = {'code': {'read_only': True}, 'seller': {'read_only': True}} # TODO chequear
        # read_only_fields = ['code', 'seller']  # Hacemos el código y el vendedor de solo lectura

    def create(self, validated_data):
        images_data = validated_data.pop('images', []) # todo -> check
        seller = self.context['request'].user.seller
        product = Product.objects.create(seller=seller, **validated_data)

        for image_data in images_data:
            # subir imagen al bucket
            # guardar URL
            # crear la instancia en la tabla con la URL obtenida
            ProductImage.objects.create(product=product, **image_data)

        return product

# Example:
# {
#     "name": "Product Name",
#     "material": "Material",
#     "stock": 10,
#     "description": "Product Description",
#     "stl_file_url": "http://example.com/file.stl",
#     "price": "19.99",
#     "images": [
#         {"image_url": "http://example.com/image1.jpg"},
#         {"image_url": "http://example.com/image2.jpg"}
#     ]
# }
"""

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['orderID', 'userID', 'orderDate', 'quantity', 'productCode', 'status']
        extra_kwargs = {'orderID': {'read_only': True}, 'orderDate': {'read_only': True}, 'status': {'read_only': True}}
        #read_only_fields = ['order_id', 'order_date', 'status']  # El ID, la fecha y el estado no se pueden modificar

    def create(self, validated_data):
        # Al crear una orden, el estado siempre será "pendiente"
        return Order.objects.create(**validated_data)



