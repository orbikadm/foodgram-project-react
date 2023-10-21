from django.contrib import admin

from .models import Ingredient, Recipe, Tag, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email',)
    search_fields = ('email', 'username',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author',)
    list_filter = ('author', 'name', 'tags')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
