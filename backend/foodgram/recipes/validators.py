from django.core.exceptions import ValidationError

FORBIDDEN_USERNAME = ('me', 'user', 'admin', 'moderator')


def validation_username(value):
    if value in FORBIDDEN_USERNAME:
        raise ValidationError('Недопустимое имя пользователя')