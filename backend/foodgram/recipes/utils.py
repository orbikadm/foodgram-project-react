from django.utils.crypto import get_random_string


def generate_code():
    return get_random_string(length=32)
