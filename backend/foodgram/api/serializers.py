from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import ValidationError
from recipes.models import Recipe, Ingredient, Tag, IngredientToRecipe
from users.models import Subscribe
from django.contrib.auth import get_user_model
import base64
import webcolors
from django.core.files.base import ContentFile
from django.db.models import F
from django.db import transaction

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
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


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientToRecipeWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(required=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количесто ингредиента не может быть меньше отрицательным'
            )
        return value


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для рецептов, используется для получения рецепта, списка
    рецептов, удаления
    Обрабатывает методы [POST], [GET], [DELETE].
    """

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'text', 'image', 'cooking_time', 'tags', 'ingredients', 'is_favorited', 'is_in_shopping_cart')

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

    # def validate(self, data):
    #     tags_ids = self.initial_data.get("tags")
    #     ingredients = self.initial_data.get("ingredients")

    #     if not tags_ids or not ingredients:
    #         raise ValidationError("Недостаточно данных.")

    #     tags = tags_exist_validator(tags_ids, Tag)
    #     ingredients = ingredients_validator(ingredients, Ingredient)

    #     data.update(
    #         {
    #             "tags": tags,
    #             "ingredients": ingredients,
    #             "author": self.context.get("request").user,
    #         }
    #     )
    #     return data




class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для создания рецепта.
    Обрабатывает метод [POST].
    """

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientToRecipeWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'text', 'image', 'cooking_time', 'tags', 'ingredients')

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент!'
            })
        ingredients_list = []
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredients_list:
                raise ValidationError({
                    'ingredients': 'Ингридиенты не должны повторяться!'
                })
            if int(item['amount']) <= 0:
                raise ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0!'
                })
            ingredients_list.append(ingredient)
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError({'tags': 'Нужно выбрать хотя бы один тег!'})
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError({'tags': 'Теги должны быть уникальными!'})
            tags_list.append(tag)
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
        self.create_ingredients_amounts(recipe=instance, ingredients=ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data