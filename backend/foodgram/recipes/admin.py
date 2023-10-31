from django.contrib import admin

from .models import Ingredient, Recipe, Tag, IngredientToRecipe, Favorite, Shopping_cart


class IngredientToRecipeAdmin(admin.TabularInline):
    model = IngredientToRecipe
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientToRecipeAdmin,)
    list_display = ('name', 'author', 'in_favorites')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '--не указано--'

    @admin.display(description='В избранном')
    def in_favorites(self, obj):
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'color', 'slug')
    # list_editable = ('name', 'color', 'slug')
    empty_value_display = '--не указано--'


@admin.register(IngredientToRecipe)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    # list_editable = ('recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    # list_editable = ('user', 'recipe')


@admin.register(Shopping_cart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    # list_editable = ('user', 'recipe')
