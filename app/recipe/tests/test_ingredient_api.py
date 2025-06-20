"""Tests for the ingredient API"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Create and return a detail URL for an Ingredient"""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


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

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(name="Cucumber", user=self.user)

        payload = {"name": "Tomato"}
        url = detail_url(ingredient.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test deleting an Ingredient"""
        ingredient = Ingredient.objects.create(name="Onion", user=self.user)
        url = detail_url(ingredient.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredients_assigned_to_recipe(self):
        """Test ingredients are filtered by recipe"""
        in1 = Ingredient.objects.create(name="Onion", user=self.user)
        in2 = Ingredient.objects.create(name="Tomato", user=self.user)
        recipe = Recipe.objects.create(
            title="Spaghetti",
            time_minutes=5,
            price=Decimal("10"),
            user=self.user,
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)

        self.assertIn(s1.data, res.json())
        self.assertNotIn(s2.data, res.json())

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients return a unique list."""
        ing = Ingredient.objects.create(name="Onion", user=self.user)
        Ingredient.objects.create(name="Tomato", user=self.user)
        recipe1 = Recipe.objects.create(
            title="Test Recipe",
            time_minutes=5,
            price=Decimal("10"),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title="Test Recipe 2",
            time_minutes=5,
            price=Decimal("12"),
            user=self.user,
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.json()), 1)
