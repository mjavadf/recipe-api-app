"""Tests for the recipe API."""

import tempfile
import os

from PIL import Image
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def image_upload_url(recipe_id):
    """Create and return an image upload URL for a recipe."""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


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

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            "title": "New Recipe Title",
            "time_minutes": 10,
            "price": Decimal("10.99"),
            "tags": [
                {"name": "Thai"},
                {"name": "Dinner"},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

        def test_create_recipe_with_existing_tags(self):
            """Test creating a recipe with existing tags"""
            tag_italian = Tag.objects.create(name="Italian", user=self.user)
            payload = {
                "title": "Pizza Margherita",
                "time_minutes": 20,
                "price": Decimal("5.99"),
                "tags": [
                    {"name": "Italian"},
                    {"name": "Pizza"},
                ],
            }
            res = self.client.post(RECIPES_URL, payload, format="json")

            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            recipes = Recipe.objects.filter(user=self.user)
            self.assertEqual(recipes.count(), 1)
            recipe = recipes[0]
            self.assertEqual(recipe.tags.count(), 2)
            self.assertIn(tag_italian, recipe.tags.all())
            for tag in payload["tags"]:
                exists = recipe.tags.filter(
                    name=tag["name"], user=self.user
                ).exists()
                self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test crerating a tag on recipe update."""
        recipe = create_recipe(user=self.user)

        payload = {
            "tags": [
                {"name": "Mediterranean"},
            ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name="Mediterranean", user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tags(self):
        """Test assigning an existing when updating a recipe"""
        tag_breakfast = Tag.objects.create(name="Breakfast", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_launch = Tag.objects.create(name="Launch", user=self.user)
        # Try to change "Breakfast" to "Launch"
        payload = {"tags": [{"name": "Launch"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_launch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing all tags on a recipe"""
        tag = Tag.objects.create(name="Dessert", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients"""
        payload = {
            "title": "New Recipe Title",
            "time_minutes": 10,
            "price": Decimal("10.99"),
            "ingredients": [
                {"name": "Egg"},
                {"name": "Cheese"},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a recipe with existing ingredients"""
        ingredient_egg = Ingredient.objects.create(name="Egg", user=self.user)
        payload = {
            "title": "New Recipe Title",
            "time_minutes": 10,
            "price": Decimal("10.99"),
            "ingredients": [
                {"name": "Egg"},
                {"name": "Cheese"},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient_egg, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient on recipe update"""
        recipe = create_recipe(user=self.user)

        payload = {"ingredients": [{"name": "Lettuce"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(name="Lettuce", user=self.user)
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredients(self):
        """Test assigning an existing when updating a recipe"""
        ingredient1 = Ingredient.objects.create(name="Pepper", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(name="Onion", user=self.user)
        payload = {"ingredients": [{"name": "Onion"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing all ingredients on a recipe"""
        ingredient = Ingredient.objects.create(name="Egg", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class ImageUploadTests(TestCase):
    """Tests for image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="user@example.com",
            password="testpassword1234",
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, "JPEG")
            image_file.seek(0)  # set file pointer back to start of file
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.recipe.id)
        payload = {"image": "invalid-image.jpg"}
        res = self.client.post(url, payload, format="multipart")
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        