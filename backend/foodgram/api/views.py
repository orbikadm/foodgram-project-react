from recipes.models import Ingredient, Recipe, Tag, RecipeIngredient, RecipeTag
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import SearchFilter
from .serializers import RecipeSerializer, IngredientSerializer, TagSerializer, UsersSerializer
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly
)



User = get_user_model()


class UsersViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    # permission_classes = (AdminOnly,)
    http_method_names = ['get', 'post']
    lookup_field = 'username'
    filter_backends = (SearchFilter,)
    search_fields = ('username',)

    @action(
        methods=['get', 'post'],
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated,)
    )
    def get_account_details(self, request):
        serializer = UsersSerializer(request.user)
        if request.method == 'POST':
            if request.user.is_admin:
                serializer = UsersSerializer(
                    request.user,
                    data=request.data,
                    partial=True
                )
            else:
                serializer = MeSerializer(
                    request.user,
                    data=request.data,
                    partial=True
                )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination


class IngredientViewSet(ModelViewSet):
    allowed_methods = ('GET',)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = LimitOffsetPagination
    search_fields = ('^name',)


class TagViewSet(ModelViewSet):
    allowed_methods = ('GET',)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = LimitOffsetPagination
