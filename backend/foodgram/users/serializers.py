from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from .models import Subscribe


User = get_user_model()


class CustomUserReadSerializer(UserSerializer):
    """Кастомный сериалайзер для пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        read_only_fields = ('is_subscribed',)
        write_only_fields = ('password',)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Кастомный сериалайзер для создания пользователя."""

    username = serializers.RegexField(r'^[\w.@+-]+\Z')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'username': {'required': True},
        }

    def validate_username(self, username):
        if len(username) < 1 or len(username) > 150:
            raise serializers.ValidationError('Длина username должна быть от 0 до 150')
        return username
