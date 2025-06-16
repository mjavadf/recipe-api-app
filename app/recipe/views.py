"""Views for the recipe API."""

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer,
    IngredientSerializer,
)


class RecipeViewSet(viewsets.ModelViewSet):
    """View set for the recipe APIs"""

    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Limit the queryset to the user's recipes."""
        return Recipe.objects.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        """Return the serializer class based on the request method."""
        if self.action == "list":
            return RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe for the authenticated user."""
        serializer.save(user=self.request.user)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Manage tags for the authenticated user."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Limit the queryset to the user's tags."""
        return self.queryset.filter(user=self.request.user).order_by("-name")


class IngredientViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Manage ingredients for the authenticated user."""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Limit the queryset to the user's ingredients."""
        return self.queryset.filter(user=self.request.user).order_by("-name")
