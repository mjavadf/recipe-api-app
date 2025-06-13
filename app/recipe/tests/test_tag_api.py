"""Test for the tags api."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id) -> str:
    """Create and return a detail URL for a tag"""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="testpassword1234"):
    """Create and return a user"""
    return get_user_model().objects.create_user(email=email, password=password)  # type: ignore # noqa: E501


class PublicTagAPITestCase(TestCase):
    """Test unauthenticated access to the tag API."""

    def setUp(self):
        self.client = APIClient()

    def auth_required(self):
        """Test auth is required to access the API"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagAPITestCase(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags"""
        Tag.objects.create(name="Dessert", user=self.user)
        Tag.objects.create(name="Vegan", user=self.user)

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), serializer.data)

    def test_tag_list_limited_to_user(self):
        """Test list of tags is limited to the user's tags."""
        other_user = create_user(
            email="other_user@example.com",
            password="testpassword1234",
        )
        Tag.objects.create(name="Fruitty", user=other_user)
        tag = Tag.objects.create(name="Vegan", user=self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["name"], tag.name)
        self.assertEqual(res.json()[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating a tag."""
        tag = Tag.objects.create(name="Seafood", user=self.user)

        payload = {"name": "Insalata"}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(name="Seafood", user=self.user)
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
