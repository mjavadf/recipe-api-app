"""Tests for models."""

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from unittest.mock import patch

from core import models


def create_user(email="test@example.com", password="test1234"):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test Models."""

    def test_create_user_with_email_successful(self):
        """Test create user with email successful."""
        email = "test@example.com"
        password = "test1234"
        user = get_user_model().objects.create_user(
            email=email, password=password
        )  # type: ignore

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email is normalized for new users."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email, password="test1234"
            )  # type: ignore
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_fails(self):
        """Test that creating a new user without
        an email raises an ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", password="test1234")

    def test_create_superuser_successful(self):
        """Test create superuser."""
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            password="test1234",
        )  # type: ignore

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe is successful."""
        user = get_user_model().objects.create_user(
            email="test@example.com", password="test1234"
        )  # type: ignore
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample Recipe name",
            time_minutes=10,
            price=Decimal("10.00"),
            description="Sample Recipe description",
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a tag is successful."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test creating an ingredient is successful."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name="Ingredient1",
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "test.jpg")

        self.assertEqual(file_path, f"uploads/recipe/{uuid}.jpg")
