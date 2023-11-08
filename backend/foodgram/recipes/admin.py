from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientToRecipe, Recipe,
                     ShoppingCart, Tag)


class IngredientToRecipeAdmin(admin.TabularInline):
    model = IngredientToRecipe
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientToRecipeAdmin,)
    list_display = ('name', 'author', 'in_favorites')
    list_filter = ('author', 'name', 'tags')

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


@admin.register(IngredientToRecipe)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
