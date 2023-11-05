import base64
import webcolors

from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.files.base import ContentFile
from django.db.models import F
from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import status, serializers
from rest_framework.validators import ValidationError

from recipes.models import Recipe, Ingredient, Tag, IngredientToRecipe
from users.models import Subscribe
from .validators import tags_exist_validator, ingredients_validator


User = get_user_model()


class CustomUserSerializer(UserSerializer):
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


class RecipeForSubscribeSerializer(serializers.ModelSerializer):
    """Сериалайзер рецептов для использования в сериализаторе подписок."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscribeSerializer(CustomUserSerializer):
    """
    Сериалайзер для подписок.
    Дополнительно проверяет повторные подписки и подписки на самого себя.
    """
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
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
        serializer = RecipeForSubscribeSerializer(
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
    """Вспомогательный сериалайзер для получения количества ингредиентов."""

    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(required=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количесто ингредиента не может быть меньше отрицательным'
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

    author = CustomUserSerializer(read_only=True)
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
        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент.'
            })
        ingredients_list = []
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredients_list:
                raise ValidationError({
                    'ingredients': 'Ингридиенты не могут повторяться.'
                })
            if int(item['amount']) <= 0:
                raise ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0.'
                })
            ingredients_list.append(ingredient)
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError({'tags': 'Нужно выбрать хотя бы один тег.'})
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError({'tags': 'Теги должны быть уникальными.'})
            tags_list.append(tag)
        return value



class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер для создания рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientToRecipeWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients'
        )

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент.'
            })
        ingredients_list = []
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredients_list:
                raise ValidationError({
                    'ingredients': 'Ингридиенты не могут повторяться.'
                })
            if int(item['amount']) <= 0:
                raise ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0.'
                })
            ingredients_list.append(ingredient)
        return value

    # def validate_ingredients(self, value):
    #     ingredients = value
    #     if not ingredients:
    #         raise ValidationError({
    #             'ingredients': 'Нужен хотя бы один ингредиент.'
    #         })
    #     ingredients_list = []
    #     for item in ingredients:
    #         # ingredient = Ingredient.objects.filter(id=item.get('id')).exists()
    #         # if ingredient is False:
    #         #     return ValidationError({'errors': 'Несуществующий ингридиент.'})
    #         ingredient = Ingredient.objects.get(id=item.get('id'))
    #         if ingredient in ingredients_list:
    #             raise ValidationError({
    #                 'ingredients': 'Ингридиенты не должны повторяться.'
    #             })
    #         if int(item['amount']) <= 0:
    #             raise ValidationError({
    #                 'amount': 'Количество ингредиентов должно быть больше 0.'
    #             })
    #         ingredients_list.append(ingredient)
    #     # db_ings = Ingredient.objects.filter(pk__in=ingredients_list.keys())
    #     # if not db_ings:
    #     #     raise ValidationError({
    #     #             'ingredients': 'Несуществующий ингридиент.'
    #     #         })
    #     return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError({'tags': 'Нужно выбрать хотя бы один тег!'})
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError({
                    'tags': 'Теги должны быть уникальными!'
                })
            tags_list.append(tag)
        return value
    
    def validate_cooking_time(self, value):
        if value <= 0:
            raise ValidationError({
                'cooking_time': 'Время приготовления не может быть отрицательным'
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
