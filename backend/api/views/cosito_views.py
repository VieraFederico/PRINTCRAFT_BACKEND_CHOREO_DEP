import cohere

from .general_imports import *

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import logging
from django.core.cache import cache
from sentence_transformers import SentenceTransformer

from api.models import Product, Category


class RecommendationEngine:

    def __init__(self, embedding_model='all-MiniLM-L6-v2'):

        self.model = SentenceTransformer(embedding_model)
        self.logger = logging.getLogger('recommendation_system')
        self.metrics = RecommendationMetrics()

    def get_cached_embedding(self, item, cache_key_prefix):
        try:
            print("ADENTRO")
            cache_key = f"{cache_key_prefix}_{item.code}"
            cached_embedding = cache.get(cache_key)
            print("SALIO")
            print("Item Embedding Key:", cache_key)
            print("Item Embedding:", cached_embedding)
            print("Item Embedding Type:", type(cached_embedding))

            if cached_embedding is None:
                embedding = np.array(self.model.encode([item.name])[0])
                cache.set(cache_key, embedding, timeout=86400)
            else:
                embedding = np.array(cached_embedding)

            return embedding

        except Exception as e:
            self.logger.error(f"Embedding error: {str(e)}")
            return None

    def calculate_semantic_similarity(self, query_embedding, item_embedding):
        return np.dot(query_embedding, item_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(item_embedding))

    def find_best_category(self, user_input):
        # Check categories exist
        categories = Category.objects.all()
        products = Product.objects.all()
        print(f"Total Categories: {categories.count()}")
        print(f"Total Product: {products.count()}")

        if not categories.exists():
            print("No categories in database!")
            return None

        user_embedding = self.model.encode([user_input])[0]

        category_similarities = []
        for category in categories:
            try:
                category_embedding = self.get_cached_embedding(category, 'category')
                similarity = self.calculate_semantic_similarity(user_embedding, category_embedding)
                category_similarities.append((category, similarity))
            except Exception as e:
                print(f"Error processing category {category.name}: {e}")

        if not category_similarities:
            print("No category similarities calculated!")
            return None

        return max(category_similarities, key=lambda x: x[1])[0]

    def recommend_products(self, user_input, confidence_threshold=0.2):
        try:

            selected_category = self.find_best_category(user_input)

            products = Product.objects.filter(categories=selected_category)
            user_embedding = self.model.encode([user_input])[0]

            product_scores = []
            for product in products:
                product_embedding = self.get_cached_embedding(product, 'product')
                print("ADENTRO")
                similarity = self.calculate_semantic_similarity(user_embedding, product_embedding)
                print("SALIO")
                product_scores.append((product.name, similarity))

            best_product = max(product_scores, key=lambda x: x[1]) if product_scores else None
            # Filter and rank recommendations
            confident_recommendations = [
                (product, similarity)

                for product, similarity in product_scores
                if similarity > confidence_threshold
            ]

            # Sort recommendations
            sorted_recommendations = sorted(
                confident_recommendations,
                key=lambda x: x[1],
                reverse=True
            )
       
            recommendation_result = {
                'top_recommendation': sorted_recommendations[0][0] if sorted_recommendations else None,
                'alternatives': [rec[0] for rec in sorted_recommendations[1:10]],
                'confidence_level': len(confident_recommendations) / len(product_scores) if product_scores else 0
            }
            self.metrics.update_metrics(recommendation_result['confidence_level'])

            return recommendation_result

        except Exception as e:
            self.logger.error(f"Recommendation error: {str(e)}")
            return None


class RecommendationMetrics:
    CONFIDENCE_THRESHOLD = 0.2

    def __init__(self):
        self.total_recommendations = 0
        self.successful_recommendations = 0
        self.average_confidence = 0

    def update_metrics(self, confidence_score):
        self.total_recommendations += 1
        self.successful_recommendations += 1 if confidence_score > self.CONFIDENCE_THRESHOLD else 0

        # Running average of confidence
        self.average_confidence = (self.average_confidence * (self.total_recommendations - 1) + confidence_score) / self.total_recommendations


class CositoAIView(APIView):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recommendation_engine = RecommendationEngine()

    def post(self, request):
        try:
            user_input = request.data.get('input')
            co = cohere.Client(settings.COHERE_API_KEY)

            if not user_input:
                return Response({'error': 'No input provided'},status=status.HTTP_400_BAD_REQUEST)

            recommendations = self.recommendation_engine.recommend_products(user_input)

            if recommendations:
                prompt = (
                    f"You are a product recommendation system. Your task is to identify the most relevant product from the following list: {recommendations}. "
                    f"The user has described what they are looking for as: '{user_input}'. "
                    f"Match the user's description to the listed products based solely on their name, description, or material. "
                    f"Do not recommend products, categories, or options that are not explicitly listed. "
                    f"If none of the products in the list match the user's description, respond with: 'No suitable match found.' "
                    f"Do not suggest searching for other categories or products outside this list. "
                    f"Respond in the same language as the user's input. "
                    f"Keep your response concise and factual."
                )

                cohere_response = co.generate(
                    model='command-xlarge-nightly',
                    prompt=prompt,
                    max_tokens=100,
                    temperature=0.5
                )

                generated_text = cohere_response.generations[0].text.strip()

                return Response(
                    {'recommendation': generated_text},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'message': 'No matching products found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            # Log unexpected errors
            logging.error(f"Recommendation system error: {str(e)}")
            return Response(
                {'error': 'Internal recommendation error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
"""
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
                        )

"""

"""
class CositoAIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            user_input = request.data.get('input')

            selected_category = self.get_best_category(user_input)

            products = Product.objects.filter(categories=selected_category)

            model = SentenceTransformer('all-MiniLM-L6-v2')
            user_embedding = model.encode([user_input])[0]

            product_embeddings = []

            for product in products:
                product_embedding = model.encode([product.name])[0]
                product_embeddings.append((product.name, product_embedding))

            user_embedding = np.array(user_embedding)

            product_scores = []

            for product_name, product_embedding in product_embeddings:
                similarity = np.dot(user_embedding, product_embedding) / (
                            np.linalg.norm(user_embedding) * np.linalg.norm(product_embedding))
                product_scores.append((product_name, similarity))

            best_product = max(product_scores, key=lambda x: x[1]) if product_scores else None

            if best_product:
                return Response({'response': best_product[0]}, status=status.HTTP_200_OK)
            else:
                return Response({'response': 'No matching products found.'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_best_category(self, user_input):
        model = SentenceTransformer('all-MiniLM-L6-v2')

        user_embedding = model.encode([user_input])[0]

        categories = Category.objects.all()
        category_embeddings = []

        for category in categories:
            category_embedding = model.encode([category.name])[0]
            category_embeddings.append((category, np.array(category_embedding)))

        max_similarity = -1
        best_category = None

        for category, category_embedding in category_embeddings:
            similarity = np.dot(user_embedding, category_embedding) / (
                        np.linalg.norm(user_embedding) * np.linalg.norm(category_embedding))
            if similarity > max_similarity:
                max_similarity = similarity
                best_category = category

        return best_category
"""
