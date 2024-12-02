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
            cache_key = f"{cache_key_prefix}_{item.code}"
            cached_embedding = cache.get(cache_key)

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
