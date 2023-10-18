from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, TagViewSet, IngredientViewSet

api_router = DefaultRouter()
api_router.register('tags', TagViewSet)
api_router.register('recipes', RecipeViewSet)
api_router.register('ingredients', IngredientViewSet)
# api_router.register('')

urlpatterns = [
    path('', include(api_router.urls)),
]
