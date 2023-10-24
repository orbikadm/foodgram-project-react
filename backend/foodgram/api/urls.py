from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, TagViewSet, IngredientViewSet, UsersViewSet

api_router = DefaultRouter()
api_router.register('tags', TagViewSet)
api_router.register('recipes', RecipeViewSet)
api_router.register('ingredients', IngredientViewSet)
# api_router.register('')
api_router.register(
    'users',
    UsersViewSet,
    basename='users'
)

# TODO Добавить урл users/{id}  и  урл users/set_password/ (Разобраться почему не работает)

urlpatterns = [
    # path('', include('djoser.urls.jwt')),
    path('', include(api_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]
