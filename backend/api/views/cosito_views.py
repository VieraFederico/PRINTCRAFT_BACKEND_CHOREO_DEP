from .general_imports import *
from ..models import Product
import cohere

class CositoAI(APIView):
    permission_classes = [AllowAny]  # Allow any access to this view

    def post(self, request):
        try:
            user_input = request.data.get('input')

            # Step 1: Get all products from the database
            products = Product.objects.all()

            # Prepare a list to store responses
            product_scores = []

            # Initialize Cohere client
            co = cohere.Client(settings.COHERE_API_KEY)

            # Step 2: Iterate through each product and get Cohere's response
            for product in products:
                product_name = product.name  # Get product name
                product_description = product.description  # Get product description

                # Create the prompt using both name and description
                prompt = (f"Evaluate the product '{product_name}' with description: '{product_description}' "
                          f"against this user description: '{user_input}'. "
                          f"Respond with a score (1-10) indicating how well it matches.")

                response = co.generate(
                    model='command-xlarge-nightly',  # Cohere model to use
                    prompt=prompt,
                    max_tokens=10,
                    temperature=0.5,
                    stop_sequences=["\n"]
                )

                # Extract the score from Cohere's response
                score = float(response.generations[0].text.strip())
                product_scores.append((product_name, score))  # Store product name and score

            # Step 3: Find the product with the highest score
            best_product = max(product_scores, key=lambda x: x[1]) if product_scores else None

            if best_product:
                return Response({'response': best_product[0]}, status=status.HTTP_200_OK)  # Return the best product name
            else:
                return Response({'response': 'No matching products found.'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CositoAIID(APIView):
    permission_classes = [AllowAny]  # Allow any access to this view

    def post(self, request):
        try:
            user_input = request.data.get('input')

            # Step 1: Get all products from the database
            products = Product.objects.all()

            # Prepare a list to store responses
            product_scores = []

            # Initialize Cohere client
            co = cohere.Client(settings.COHERE_API_KEY)

            # Step 2: Iterate through each product and get Cohere's response
            for product in products:
                product_id = product.code  # Get product ID
                product_name = product.name  # Get product name
                product_description = product.description  # Get product description

                # Create the prompt using both name and description
                prompt = (f"Evaluate the product '{product_name}' with description: '{product_description}' "
                          f"against this user description: '{user_input}'. "
                          f"Respond with a score (1-10) indicating how well it matches.")

                response = co.generate(
                    model='command-xlarge-nightly',
                    prompt=prompt,
                    max_tokens=10,
                    temperature=0.5
                )

                # Extract the score from Cohere's response
                score = float(response.generations[0].text.strip())
                product_scores.append((product_id, score))  # Store product ID and score

            # Step 3: Find the product with the highest score
            best_product = max(product_scores, key=lambda x: x[1]) if product_scores else None

            if best_product:
                return Response({'response': best_product[0]},
                                status=status.HTTP_200_OK)  # Return the best product name
            else:
                return Response({'response': 'No matching products found.'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)