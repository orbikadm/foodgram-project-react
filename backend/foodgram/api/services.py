from recipes.models import IngredientAmount


def recipe_ingredients_set(recipe, ingredients):

    objs = []

    for ingredient, amount in ingredients.values():
        objs.append(
            IngredientAmount(
                recipe=recipe, ingredients=ingredient, amount=amount
            )
        )

    IngredientAmount.objects.bulk_create(objs)
