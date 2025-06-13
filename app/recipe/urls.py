from django.urls import path, include
from rest_framework.routers import DefaultRouter
from recipe import views

router = DefaultRouter()
# TODO: Change recipe to recipes
router.register("recipe", views.RecipeViewSet)
router.register("tags", views.TagViewSet)

app_name = "recipe"

urlpatterns = [
    path("", include(router.urls)),
]
