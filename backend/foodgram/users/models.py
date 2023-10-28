from django.db import models
from django.contrib.auth.models import AbstractUser

from .validators import username_validator


class User(AbstractUser):
    username = models.CharField(
        'Логин',
        max_length=150,
        unique=True,
        help_text='Обязательное, не более 150 символов. Только буквы, цифры и символы @/./+/-/_',
        validators=[username_validator],
    )
    password = models.CharField('Пароль', max_length=128)
    email = models.EmailField('Адрес электронной почты', unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [username, password, first_name, last_name]

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owner',
        verbose_name='Автор рецепта',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='subscribe_unique'),
        )
        verbose_name = 'Подписка на автора'
        verbose_name_plural = 'Подписки на авторов'

    def __str__(self) -> str:
        return f'{self.user.username} подписан на {self.author.username}'
