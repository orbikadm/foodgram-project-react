from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUsersViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet)


api_router = DefaultRouter()
api_router.register(r'tags', TagViewSet)
api_router.register(r'recipes', RecipeViewSet)
api_router.register(r'ingredients', IngredientViewSet)
api_router.register(
    'users',
    CustomUsersViewSet,
    basename='users'
)

urlpatterns = [
    path('', include(api_router.urls)),
    path('', include('djoser.urls')),
    path(r'auth/', include('djoser.urls.authtoken'))
]
