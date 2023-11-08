import base64
import datetime
import webcolors

from django.core.files.base import ContentFile
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import status
from rest_framework import serializers

from recipes.models import IngredientToRecipe, Ingredient
from .validators import validate_tags_and_ingredients_exists, get_validate_ingredients, get_validate_tags


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


class BaseRecipeSerializer(serializers.ModelSerializer):
    def validate_ingredients(self, value):
        return get_validate_ingredients(self, value, Ingredient)

    def validate_tags(self, value):
        return get_validate_tags(self, value)


def get_shopping_file(self, request):
    user = request.user

    ingredients = IngredientToRecipe.objects.filter(
        recipe__shopping_recipe__user=request.user
    ).values(
        'ingredient__name',
        'ingredient__measurement_unit'
    ).annotate(amount=Sum('amount'))

    today = datetime.datetime.today()
    shopping_list = (
        f'Список покупок для: {user.get_full_name()}\n\n'
        f'Дата: {today:%Y-%m-%d}\n\n'
    )
    shopping_list += '\n'.join([
        f'- {ingredient["ingredient__name"]} '
        f'({ingredient["ingredient__measurement_unit"]})'
        f' - {ingredient["amount"]}'
        for ingredient in ingredients
    ])
    shopping_list += f'\n\nFoodgram ({today:%Y})'
    filename = f'{user.username}_shopping_list.txt'
    response = HttpResponse(
        shopping_list,
        content_type='text/plain',
        status=status.HTTP_200_OK
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def method_switch(self, request, model, pk):
    if request.method == 'POST':
        return self.add_to(model, request.user, pk)
    else:
        return self.delete_from(model, request.user, pk)


def get_validated_tags_and_ingredients_if_exists(self, validated_data):
    validate_tags_and_ingredients_exists(self, validated_data)
    tags = validated_data.pop('tags')
    ingredients = validated_data.pop('ingredients')
    return tags, ingredients
