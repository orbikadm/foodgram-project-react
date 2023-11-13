from django.conf import settings
from django.db import transaction
from django.db.models import F
from rest_framework import serializers, status
from rest_framework.validators import ValidationError

from recipes.models import Ingredient, IngredientToRecipe, Recipe, Tag
from users.serializers import CustomUserReadSerializer
from .services import (Base64ImageField, BaseRecipeSerializer, Hex2NameColor,
                       get_validated_tags_and_ingredients_if_exists)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Вспомогательный сериалайзер для доступа к усеченному списку полей."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscribeSerializer(CustomUserReadSerializer):
    """
    Сериалайзер для подписок.
    Дополнительно проверяет повторные подписки и подписки на самого себя.
    """
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserReadSerializer.Meta):
        fields = CustomUserReadSerializer.Meta.fields + (
            'recipes_count', 'recipes'
        )
        read_only_fields = ('email', 'username')

    def validate(self, data):
        author = self.instance
        user = self.context['request'].user
        subscribe = author.owner.filter(user=user).exists()
        if subscribe:
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeShortSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientToRecipeWriteSerializer(serializers.Serializer):
    """Вспомогательный сериалайзер для записи количества ингредиентов."""

    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(
        required=True,
        min_value=settings.MIN_AMOUNT_INGR,
        max_value=settings.MAX_AMOUNT_INGR,
    )


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения тегов."""

    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')


class RecipeSerializer(BaseRecipeSerializer):
    """
    Сериалайзер для рецептов, используется для получения рецепта, списка
    рецептов, удаления рецепта.
    """

    author = CustomUserReadSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'text',
            'image', 'cooking_time', 'tags',
            'ingredients', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredienttorecipe__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class RecipeCreateSerializer(BaseRecipeSerializer):
    """Сериалайзер для создания и обновления рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientToRecipeWriteSerializer(many=True,)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=settings.MIN_COOCK_TIME, max_value=settings.MAX_COOCK_TIME
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients'
        )

    @transaction.atomic
    def create_ingredients_amounts(self, ingredients, recipe):
        IngredientToRecipe.objects.bulk_create([
            IngredientToRecipe(
                recipe=recipe,
                amount=ingredient.get('amount'),
                ingredient_id=ingredient.get('id')
            ) for ingredient in ingredients
        ])

    @transaction.atomic
    def create(self, validated_data):
        tags, ingredients = get_validated_tags_and_ingredients_if_exists(
            self, validated_data
        )
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(recipe=recipe, ingredients=ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags, ingredients = get_validated_tags_and_ingredients_if_exists(
            self, validated_data
        )
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients_amounts(
            recipe=instance, ingredients=ingredients
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data
