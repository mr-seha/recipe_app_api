import time

from django.core.management.base import BaseCommand
from django.db import OperationalError
from psycopg2 import OperationalError as Psycopg2Operror


class Command(BaseCommand):
    help = 'Wait until the database is available'

    def handle(self, *args, **options):
        self.stdout.write('Wait for database...')

        db_up = False

        while not db_up:
            try:
                self.check(databases=['default'])
                db_up = True

            except (Psycopg2Operror, OperationalError):
                self.stdout.write('Database is unavailable, waiting 1 seconds...')
                time.sleep(1)

        self.stdout.write('Database is available!')
