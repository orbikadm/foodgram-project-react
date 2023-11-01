import csv

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic

from recipes.models import Ingredient


class Command(BaseCommand):
    @atomic
    def handle(self, **options):
        try:
            with open(
                f'{settings.BASE_DIR}/data/ingredients.csv',
                encoding='utf-8'
            ) as csv_file:
                reader = csv.reader(csv_file, delimiter=",")
                Ingredient.objects.bulk_create([
                    Ingredient(
                        id=num,
                        name=line[0],
                        measurement_unit=line[1]
                    ) for num, line in enumerate(reader)
                ])
            self.stdout.write(self.style.SUCCESS(
                'Загрузка данных в БД прошла успешно'
            ))

        except Exception as error:
            raise CommandError(f'Во время загрузки произошла ошибка {error}')
