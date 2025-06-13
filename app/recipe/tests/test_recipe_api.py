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


def create_user(**params):
    """Create and return a user."""
    return get_user_model().objects.create_user(**params)


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
        self.user = create_user(
            email="user@example.com",
            password="testpassword1234",
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
        other_user = create_user(
            email="other_user@example.com",
            password="testpassword1234",
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

    def test_create_recipe(self):
        """Test creating a new recipe."""
        payload = {
            "title": "New Recipe Title",
            "time_minutes": 10,
            "price": Decimal("10.99"),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.json()["id"])

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test partially updating a recipe."""
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user, title="Sample Recipe Title", link=original_link
        )

        payload = {
            "title": "New Recipe Title",
        }

        url = detail_url(recipe.id)  # type: ignore

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test fully updating a recipe."""
        recipe = create_recipe(
            user=self.user,
            title="Sample Recipe Title",
            link="https://example.com/recipe.pdf",
            description="Sample Recipe Description",
        )

        payload = {
            "title": "New Recipe Title",
            "description": "New Recipe Description",
            "link": "https://example.com/new-recipe.pdf",
            "time_minutes": 20,
            "price": Decimal("20.99"),
        }

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_error(self):
        """Test changing the user results in and error."""
        new_user = create_user(
            email="new_user@example.com",
            password="testpassword1234",
        )
        recipe = create_recipe(user=self.user)
        payload = {
            "user": new_user.id,  # type: ignore
        }
        url = detail_url(recipe.id)  # type: ignore
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())  # noqa: E501 type: ignore

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete a recipe owned by another user."""
        new_user = create_user(
            email="new_user@example.com",
            password="testpassword1234",
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)  # type: ignore

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())  # noqa: E501 type: ignore
