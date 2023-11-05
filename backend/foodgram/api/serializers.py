import base64
import webcolors

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import F
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import status, serializers
from rest_framework.validators import ValidationError

from recipes.models import Recipe, Ingredient, Tag, IngredientToRecipe
from users.models import Subscribe
from .validators import get_validate_ingredients, get_validate_tags

User = get_user_model()


class CustomUserReadSerializer(UserSerializer):
    """Кастомный сериалайзер для пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        read_only_fields = ('is_subscribed',)
        write_only_fields = ('password',)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Кастомный сериалайзер для создания пользователя."""

    username = serializers.RegexField(r'^[\w.@+-]+\Z')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'username': {'required': True},
        }

    def validate_username(self, username):
        if len(username) < 1 or len(username) > 150:
            raise ValidationError('Длина username должна быть от 0 до 150')
        return username


class Base64ImageField(serializers.ImageField):
    """
    Сериалайзер для сохранения изображений на сервер.
    Декодирует получаемую в формате base64 картинку для сохранения её на
    сервере в файл.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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
        user = self.context.get('request').user
        subscribe = Subscribe.objects.filter(author=author, user=user).exists()
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


class Hex2NameColor(serializers.Field):
    """Вспомогательный сериалайзер преобразует HEX-код цвета в его название."""

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientToRecipeWriteSerializer(serializers.Serializer):
    """Вспомогательный сериалайзер для записи количества ингредиентов."""

    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(required=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количесто ингредиента не может быть меньше 0'
            )
        return value


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения тегов."""

    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')


class RecipeSerializer(serializers.ModelSerializer):
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
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()

    def validate_ingredients(self, value):
        return get_validate_ingredients(self, value, Ingredient)

    def validate_tags(self, value):
        return get_validate_tags(self, value)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер для создания рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientToRecipeWriteSerializer(many=True,)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients'
        )

    def validate_ingredients(self, value):
        return get_validate_ingredients(self, value, Ingredient)

    def validate_tags(self, value):
        return get_validate_tags(self, value)

    def validate_cooking_time(self, value):
        if value <= 0:
            raise ValidationError({
                'cooking_time': 'Время приготовления не может быть меньше 0'
            })
        return value

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
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(recipe=recipe, ingredients=ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
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
