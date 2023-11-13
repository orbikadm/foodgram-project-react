from django.core.exceptions import ValidationError


FORBIDDEN_USERNAME = ('me', 'user', 'admin', 'moderator')


def username_validator(value):
    if value in FORBIDDEN_USERNAME:
        raise ValidationError('Недопустимое имя пользователя')
