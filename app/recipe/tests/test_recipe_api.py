"""Tests for the recipe API."""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a detail URL for a recipe."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **kwargs):
    """Create and return a sample recipe."""
    defaults = {
        "title": "Sample Recipe Title",
        "time_minutes": 10,
        "price": Decimal("10.99"),
        "description": "Sample Recipe Description",
        "link": "https://example.com/recipe.pdf",
    }

    defaults.update(kwargs)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


class PublicRecipeAPITestCase(TestCase):
    """Test unauthenticated access to the recipe API."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to access the API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITestCase(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "testpassword1234",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to the user's recipes."""
        other_user = get_user_model().objects.create_user(
            "other_user@example.com",
            "testpassword1234",
        )

        # Other user's recipes
        create_recipe(user=other_user)

        # Current user's recipes
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), serializer.data)

    def test_get_recipe_detail(self):
        """Test retrieving a recipe's details."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)  # type: ignore
        res = self.client.get(url)
        serialzier = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), serialzier.data)
