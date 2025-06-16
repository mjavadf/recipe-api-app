"""Tests for the ingredient API"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def create_user(email="user@example.com", password="testpassword1234"):
    """Create and return a user"""
    return get_user_model().objects.create_user(email=email, password=password)  # type: ignore # noqa: E501


class PublicIngredientAPITestCase(TestCase):
    """Test unauthenticated access to the ingredient API."""
    def setUp(self):
        self.client = APIClient()
        
    def test_auth_required(self):
        """Test auth is required to access the API."""
        res = self.client.get(INGREDIENTS_URL)
        
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        
        
class PrivateIngredientAPITestCase(TestCase):
    """Test authenticated API requests."""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        
    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(name="Egg", user=self.user)
        Ingredient.objects.create(name="Cheese", user=self.user)
        
        res = self.client.get(INGREDIENTS_URL)
        
        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), serializer.data)
        
    def test_ingredient_list_limited_to_user(self):
        """Test list of ingredients is limited to the user's ingredients."""
        other_user = create_user(
            email="other_user@example.com",
            password="testpassword1234",
        )
        Ingredient.objects.create(name="Salt", user=other_user)
        ingredient = Ingredient.objects.create(name="Pepper", user=self.user)
        
        
        res = self.client.get(INGREDIENTS_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["name"], ingredient.name)
        self.assertEqual(res.json()[0]["id"], ingredient.id)