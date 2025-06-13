"""Tests for the user API."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    """Create a user."""
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = {
            "email": "test@example.com",
            "password": "test1234",
            "name": "Test name",
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.json())

    def test_user_with_email_exists_error(self):
        """Test creating a user with an existing email fails."""
        payload = {
            "email": "test@example.com",
            "password": "test1234",
            "name": "Test name",
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """
        Test creating a user with a password less
        than 5 characters fails.
        """
        payload = {
            "email": "test@example.com",
            "password": "pw",
            "name": "Test name",
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = (
            get_user_model().objects.filter(email=payload["email"]).exists()
        )
        self.assertFalse(user_exist)

    def test_create_token_success(self):
        """Test generates for valid credentials."""
        user_details = {
            "email": "test@example.com",
            "password": "test1234",
            "name": "Test name",
        }
        create_user(**user_details)

        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.json())
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_failure(self):
        """Test returns error for invalid credentials."""
        create_user(
            email="test@example.com",
            password="test1234",
        )

        payload = {
            "email": "test@example.com",
            "password": "wrongpassword",
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.json())
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test returns error for blank password."""
        payload = {
            "email": "test@example.com",
            "password": "",
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.json())
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required to retrieve user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    """Test the API reqests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="test1234",
            name="Test name",
        )

        self.client = APIClient()

        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for authenticated user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.json(),
            {
                "email": self.user.email,
                "name": self.user.name,  # type: ignore
            },
        )

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for me endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating user profile for authenticated user."""
        payload = {"name": "New name", "password": "newpass1234"}
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload["name"])  # type: ignore
        self.assertTrue(self.user.check_password(payload["password"]))
