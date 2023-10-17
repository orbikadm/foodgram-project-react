from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    following = ...

    def is_subscribed(self):
        pass


class Ingredient(models.Model):
    pass


class Recipes(models.Model):
    pass


class Tag(models.Model):
    pass


class Favorite(models.Model):
    pass
