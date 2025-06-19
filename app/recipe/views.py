"""Views for the recipe API."""

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeImageSerializer,
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer,
    IngredientSerializer,
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                description="Comma-separated list of tag IDs to filter by",
            ),
            OpenApiParameter(
                "ingredients",
                OpenApiTypes.STR,
                description="Comma-separated list of ingredient IDs to filter by",  # noqa: E501
            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View set for the recipe APIs"""

    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of string to integers."""
        return [int(id) for id in qs.split(",")]

    def get_queryset(self):
        """Limit the queryset to the user's recipes."""
        tags = self.request.query_params.get("tags")
        ingredients = self.request.query_params.get("ingredients")
        queryset = self.queryset

        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)

        if ingredients:
            ing_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ing_ids)

        return (
            queryset.filter(user=self.request.user).order_by("-id").distinct()
        )

    def get_serializer_class(self):
        """Return the serializer class based on the request method."""
        if self.action == "list":
            return RecipeSerializer
        elif self.action == "upload_image":
            return RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe for the authenticated user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an to recipe."""
        recipe = self.get_object()
        serializer = RecipeImageSerializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseRecipeAttrViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Base view set for recipe attributes."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter the queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by("-name")


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags for the authenticated user."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients for the authenticated user."""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
