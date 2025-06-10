"""
Tests fort Django admin modifications
"""

from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):
    """Tests for the admin site."""

    def setUp(self):
        """Create user and client."""
        self.client = Client()

        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="admin",
        )  # type: ignore
        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="user",
            name="Test User",
        )  # type: ignore

    def test_users_list(self):
        """Test that users are listed in the admin site."""
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_edit_suer_page(self):
        """Test that the edit user page is accessible."""
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """Test that the create user page is accessible."""
        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page_success(self):
        """Test that the create user page is can be
        used to create a new user."""
        url = reverse("admin:core_user_add")
        res = self.client.post(
            url,
            {
                "email": "newuser@example.com",
                "password1": "newuser",
                "password2": "newuser",
                "name": "New User",
                "is_active": True,
            },
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 2)
