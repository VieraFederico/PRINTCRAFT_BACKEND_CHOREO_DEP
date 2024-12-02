import numpy as np
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

from ..models import Category, Product
from ..views.cosito_views import RecommendationEngine, RecommendationMetrics


class RecommendationEngineTestCase(TestCase):
    def setUp(self):
        """
        Prepare test data for recommendation engine
        """
        # Create test categories
        self.category_electronics = Category.objects.create(name="Electronics")
        self.category_clothing = Category.objects.create(name="Clothing")
        
        # Create test products
        self.product_laptop = Product.objects.create(
            name="High-Performance Laptop", 
            categories=self.category_electronics
        )
        self.product_smartphone = Product.objects.create(
            name="Smart Smartphone", 
            categories=self.category_electronics
        )
        self.product_tshirt = Product.objects.create(
            name="Comfortable T-Shirt", 
            categories=self.category_clothing
        )
        
        # Initialize recommendation engine
        self.engine = RecommendationEngine()

    def test_find_best_category(self):
        """
        Test category matching based on semantic similarity
        """
        # Test electronics-related input
        input_electronics = "I need a powerful computer for work"
        best_category = self.engine.find_best_category(input_electronics)
        self.assertEqual(best_category, self.category_electronics)
        
        # Test clothing-related input
        input_clothing = "Looking for a comfortable shirt"
        best_category = self.engine.find_best_category(input_clothing)
        self.assertEqual(best_category, self.category_clothing)

    def test_recommend_products(self):
        """
        Test product recommendation logic
        """
        # Test electronics recommendation
        electronics_input = "I need a fast laptop for programming"
        recommendations = self.engine.recommend_products(electronics_input)
        
        self.assertIsNotNone(recommendations)
        self.assertGreater(recommendations['confidence_level'], 0)
        self.assertIn(recommendations['top_recommendation'], 
                      ["High-Performance Laptop", "Smart Smartphone"])

    @patch('sentence_transformers.SentenceTransformer')
    def test_embedding_generation(self, mock_transformer):
        """
        Test embedding generation and caching
        """
        # Mock embedding generation
        mock_embedding = MagicMock(return_value=np.array([0.1, 0.2, 0.3]))
        mock_transformer.encode.return_value = mock_embedding
        
        # Test embedding caching
        category_embedding1 = self.engine.get_cached_embedding(
            self.category_electronics, 
            'category'
        )
        category_embedding2 = self.engine.get_cached_embedding(
            self.category_electronics, 
            'category'
        )
        
        # Verify caching works
        self.assertTrue(np.array_equal(category_embedding1, category_embedding2))

class CositoAIIntegrationTestCase(TestCase):
    def setUp(self):
        """
        Prepare test client and data for API testing
        """
        self.client = APIClient()
        
        # Create test categories and products
        electronics = Category.objects.create(name="Electronics")
        Product.objects.create(
            name="Powerful Laptop", 
            categories=electronics
        )
        Product.objects.create(
            name="Gaming Smartphone", 
            categories=electronics
        )

    def test_recommendation_api_endpoint(self):
        """
        Test the recommendation API endpoint
        """
        # Prepare test input
        test_input = {
            'input': 'I need a fast computer for work'
        }
        
        # Make API request
        response = self.client.post('/api/recommend/', test_input)
        
        # Assert successful response
        self.assertEqual(response.status_code, 200)
        self.assertIn('top_recommendation', response.data)
        self.assertIn('alternatives', response.data)
        self.assertIn('confidence', response.data)

    def test_invalid_input_handling(self):
        """
        Test handling of invalid or empty input
        """
        # Test empty input
        response = self.client.post('/api/recommend/', {})
        self.assertEqual(response.status_code, 400)
        
        # Test input with no matching products
        response = self.client.post('/api/recommend/', {
            'input': 'Completely unrelated random text'
        })
        self.assertEqual(response.status_code, 404)

class RecommendationMetricsTestCase(TestCase):
    def setUp(self):
        """
        Prepare metrics tracking instance
        """
        self.metrics = RecommendationMetrics()

    def test_metrics_tracking(self):
        """
        Verify recommendation metrics are tracked correctly
        """
        # Simulate multiple recommendations
        test_confidence_scores = [0.6, 0.4, 0.7, 0.3]
        
        for score in test_confidence_scores:
            self.metrics.update_metrics(score)
        
        # Verify metrics
        self.assertEqual(self.metrics.total_recommendations, 4)
        self.assertEqual(self.metrics.successful_recommendations, 3)
        self.assertGreater(self.metrics.average_confidence, 0)
