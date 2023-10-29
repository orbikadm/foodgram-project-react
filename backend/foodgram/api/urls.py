from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, TagViewSet, IngredientViewSet, UsersViewSet

api_router = DefaultRouter()
api_router.register(r'tags', TagViewSet)
api_router.register(r'recipes', RecipeViewSet)
api_router.register(r'ingredients', IngredientViewSet)
api_router.register(
    'users',
    UsersViewSet,
    basename='users'
)

urlpatterns = [
    path('', include(api_router.urls)),
    path(r'auth/', include('djoser.urls.authtoken'))
]
