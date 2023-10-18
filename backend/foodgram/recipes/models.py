from django.db import models
# from django.contrib.auth.models import AbstractUser

# TODO
# class User(AbstractUser):
#     following = models.ManyToManyField('self', verbose_name='Подписки', related_name='followers')
#     favorite = models.ForeignKey('Recipe', on_delete=models.SET_NULL, verbose_name='Избранное')
#     def is_subscribed(self): # 
        


class Ingredient(models.Model):
    name = models.CharField('Название ингредиента', max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

    def __str__(self):
        return self.name[:50]


class Recipe(models.Model):
    name = models.CharField('Название', max_length=200)
    text = models.TextField('Описание')
    image = models.ImageField('Картинка', upload_to='images/recipes')
    cooking_time = models.PositiveSmallIntegerField('Время приготовления')
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Теги',
        blank=True,
        null=True,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиенты',
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name[:50]


class Tag(models.Model):
    name = models.CharField('Название', max_length=200, blank=True)
    color = models.CharField('Цвет', max_length=7, default=None)

    def __str__(self):
        return self.name[:50]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
