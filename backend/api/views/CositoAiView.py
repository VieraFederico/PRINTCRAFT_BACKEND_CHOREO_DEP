from rest_framework.permissions import AllowAny
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
        cache_key = f"{cache_key_prefix}_{item.id}"
        cached_embedding = cache.get(cache_key)

        if cached_embedding is None:
            embedding = self.model.encode([item.name])[0]
            cache.set(cache_key, embedding, timeout=86400)  # Cache for 24 hours
        else:
            embedding = cached_embedding

        return embedding

    def calculate_semantic_similarity(self, query_embedding, item_embedding):
        return np.dot(query_embedding, item_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(item_embedding)
        )

    def find_best_category(self, user_input):
        user_embedding = self.model.encode([user_input])[0]

        categories = Category.objects.all()

        category_similarities = []
        for category in categories:
            category_embedding = self.get_cached_embedding(category, 'category')
            similarity = self.calculate_semantic_similarity(user_embedding, category_embedding)
            category_similarities.append((category, similarity))

        return max(category_similarities, key=lambda x: x[1])[0]

    def recommend_products(self, user_input, confidence_threshold=0.5):
        try:
            selected_category = self.find_best_category(user_input)

            products = Product.objects.filter(categories=selected_category)

            user_embedding = self.model.encode([user_input])[0]

            product_scores = []
            for product in products:
                product_embedding = self.get_cached_embedding(product, 'product')
                similarity = self.calculate_semantic_similarity(user_embedding, product_embedding)
                product_scores.append((product.name, similarity))

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

            # Prepare recommendation response
            recommendation_result = {
                'top_recommendation': sorted_recommendations[0][0] if sorted_recommendations else None,
                'alternatives': [rec[0] for rec in sorted_recommendations[1:3]],
                'confidence_level': len(confident_recommendations) / len(product_scores) if product_scores else 0
            }

            # Log recommendation event
            self.metrics.update_metrics(recommendation_result['confidence_level'])

            return recommendation_result

        except Exception as e:
            self.logger.error(f"Recommendation error: {str(e)}")
            return None


class RecommendationMetrics:

    CONFIDENCE_THRESHOLD = 0.5

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

            if not user_input:
                return Response(
                    {'error': 'No input provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            recommendations = self.recommendation_engine.recommend_products(user_input)

            if recommendations and recommendations['top_recommendation']:
                return Response({
                    'top_recommendation': recommendations['top_recommendation'],
                    'alternatives': recommendations['alternatives'],
                    'confidence': recommendations['confidence_level']
                }, status=status.HTTP_200_OK)
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
