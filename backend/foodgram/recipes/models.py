from django.db import models
# from django.contrib.auth.models import AbstractUser


# class User(AbstractUser):
#     following = ...

#     def is_subscribed(self):
#         pass


class Ingredient(models.Model):
    name = models.CharField('Название ингредиента', max_length=200)
    measurement_unt = models.CharField('Единица ищмерения', max_length=200)

    def __str__(self):
        return self.name[:50]


class Recipes(models.Model):
    name = ...
    text = ...
    image = ...
    cooking_time = ...
    image = ...
    tags = ...
    ingredients = ...


class Tag(models.Model):
    pass


class Favorite(models.Model):
    pass
