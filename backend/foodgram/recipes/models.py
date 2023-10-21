from collections.abc import Iterable
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
# from slugify import slugify


class User(AbstractUser):

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        'Логин',
        max_length=150,
        unique=True,
        help_text='Обязательное, не более 150 символов. Только буквы, цифры и символы @/./+/-/_',
        validators=[username_validator],
        error_messages={
            'unique': "Пользователь с таким именем или e-mail уже существует",
        },
    )
    password = models.CharField('Пароль', max_length=128)
    email = models.EmailField('email-адрес', unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    following = models.ManyToManyField('self', verbose_name='Подписки', related_name='followers', blank=True)
    favorite = models.ForeignKey('Recipe', on_delete=models.CASCADE, verbose_name='Избранное', blank=True, null=True)


class Ingredient(models.Model):
    name = models.CharField('Название ингредиента', max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

    def __str__(self):
        return self.name[:50]


class Recipe(models.Model):
    author = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='Автор')
    name = models.CharField('Название', max_length=200)
    text = models.TextField('Описание')
    image = models.ImageField('Картинка', upload_to='images/recipes')
    cooking_time = models.PositiveSmallIntegerField('Время приготовления')
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиенты',
    )

    def __str__(self):
        return self.name[:50]


class Tag(models.Model):
    name = models.CharField('Название', max_length=200, unique=True)
    color = models.CharField('Цвет', max_length=7, default=None, unique=True)
    slug = models.SlugField('Slug', max_length=200, unique=True)

    def __str__(self):
        return self.name[:50]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
