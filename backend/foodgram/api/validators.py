from django.shortcuts import get_object_or_404
from rest_framework.validators import ValidationError


def get_validate_ingredients(self, ingredients, model):
    if not ingredients:
        raise ValidationError({
            'ingredients': 'Нужен хотя бы один ингредиент'
        })
    ingredients_list = set()
    for item in ingredients:
        ingredient_in_db = model.objects.filter(id=item['id'])
        if not ingredient_in_db.exists():
            raise ValidationError({
                'ingredients': 'Такого ингредиента не сущестует'
            })
        ingredient = get_object_or_404(model, id=item['id'])
        if ingredient in ingredients_list:
            raise ValidationError({
                'ingredients': 'Ингредиенты не могут повторяться'
            })
        ingredients_list.add(ingredient)
    return ingredients


def get_validate_tags(self, tags):
    if not tags:
        raise ValidationError({'tags': 'Нужно выбрать хотя бы один тег'})
    tags_list = set()
    for tag in tags:
        if tag in tags_list:
            raise ValidationError({
                'tags': 'Теги должны быть уникальными'
            })
        tags_list.add(tag)
    return tags


def validate_tags_and_ingredients_exists(self, validated_data):
    if not validated_data.get('tags') or not validated_data.get('ingredients'):
        raise ValidationError(
            'Ингредиенты и теги обязательны!'
        )
